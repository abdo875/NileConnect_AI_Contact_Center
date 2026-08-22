"""
Vonage voice webhooks + Call-Now trigger.

Vonage calls webhook URLs during an outbound call:

  GET  /api/v1/vonage/answer
       Vonage fetches this when the callee picks up.
       Returns the NCCO (Arabic greeting + record action).

  POST /api/v1/vonage/recording
       Vonage POSTs the recording metadata here after the customer speaks.
       Downloads the customer's audio, transcribes with Whisper STT, saves
       the transcript to Call.transcript, classifies the Arabic response,
       updates the DB, and returns the next NCCO.

  POST /api/v1/vonage/input
       Backward-compatible endpoint for speech input.

  POST /api/v1/vonage/call-now/{followup_id}
       Internal endpoint — called by the frontend "Call Now" button.
       Immediately places a Vonage call for the given follow-up.

All timestamps are in Egypt time (UTC+3 / EET).
Webhook endpoints receive followup_id and call_id as query parameters —
embedded in the URLs when placing the call so we can always look up the right
DB records without relying on Vonage's own call UUID.
"""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import FollowupResult
from app.core.database import get_db
from app.core.logging import logger
from app.repositories.call_repository import CallRepository
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.stt.arabic_classifier import classify_response
from app.telephony.stt.whisper_service import get_whisper_service
from app.telephony.vonage.client import get_vonage_client
from app.telephony.vonage.outbound_call import place_vonage_followup_call
from app.telephony.vonage.response import (
    build_escalate_ncco,
    build_greeting_ncco,
    build_no_input_ncco,
    build_resolved_ncco,
    build_retry_ncco,
)

router = APIRouter(prefix="/vonage", tags=["Vonage Telephony"])

# Egypt Standard Time = UTC+3
EGYPT_TZ = timezone(timedelta(hours=3))


def _egypt_now() -> datetime:
    """Returns current datetime in Egypt timezone (UTC+3)."""
    return datetime.now(EGYPT_TZ)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ANSWER WEBHOOK — Vonage fetches this when the callee picks up
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/answer")
def vonage_answer(
    followup_id: UUID = Query(..., description="AIFollowup this call belongs to"),
    call_id: UUID = Query(..., description="Call DB row ID"),
    db: Session = Depends(get_db),
):
    """
    Called by Vonage (GET) when the destination number answers the call.
    Returns the NCCO that plays the Arabic greeting and records the customer's reply.
    """
    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Vonage answer webhook [%s]: followup=%s call=%s",
        egypt_time, followup_id, call_id,
    )

    # The recording webhook URL — Vonage will POST the recording result here
    recording_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/recording"
        f"?followup_id={followup_id}&call_id={call_id}&attempt=1"
    )

    ncco = build_greeting_ncco(recording_url)
    return JSONResponse(content=ncco)


# ─────────────────────────────────────────────────────────────────────────────
# 2. RECORDING WEBHOOK — Vonage POSTs recording metadata here (Whisper STT)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/recording")
async def vonage_recording(
    request: Request,
    followup_id: UUID = Query(...),
    call_id: UUID = Query(...),
    attempt: int = Query(1, description="Which listen attempt this is (for retry logic)"),
    db: Session = Depends(get_db),
):
    """
    Called by Vonage (POST) with the recording metadata after <record>.

    Vonage sends a JSON body with shape:
      {
        "recording_url": "https://api-us-3.vonage.com/v1/files/...",
        "recording_uuid": "...",
        "size": 12345,
        "timestamp": "..."
      }

    Workflow:
      1. Download audio file using authenticated Vonage client.
      2. Transcribe audio with Whisper STT to Arabic text.
      3. Save transcript to Call.transcript in the database.
      4. Classify Arabic transcript (YES / NO / UNKNOWN).
      5. Execute existing call flow handler (handle_yes / handle_no / retry).
      6. Return closing or retry NCCO.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Vonage recording webhook [%s]: followup=%s call=%s attempt=%s",
        egypt_time, followup_id, call_id, attempt,
    )

    # ── 1. Extract recording URL and transcribe with Whisper ───────────────
    recording_url = body.get("recording_url", "")
    speech_text = ""

    if recording_url:
        temp_file_path = None
        try:
            client = get_vonage_client()
            whisper_service = get_whisper_service()

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_file_path = tmp.name

            logger.info("Downloading Vonage recording from: %s", recording_url)
            client.voice.download_recording(recording_url, temp_file_path)

            speech_text = whisper_service.transcribe(temp_file_path)
            logger.info("Whisper transcribed speech: %r", speech_text)
        except Exception as exc:
            logger.exception("Error processing Vonage recording with Whisper: %s", exc)
            speech_text = ""
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
    else:
        logger.warning("No recording_url found in Vonage recording webhook payload.")

    # ── 2. Save transcript to Call.transcript ──────────────────────────────
    if speech_text:
        try:
            call_repo = CallRepository(db)
            call = call_repo.get_by_id(call_id)
            if call:
                call.transcript = speech_text
                call_repo.update(call)
                logger.info("Saved Whisper transcript to Call %s", call_id)
        except Exception as exc:
            logger.exception("Failed to update Call.transcript for call=%s: %s", call_id, exc)

    # ── 3. Classify Arabic response ─────────────────────────────────────────
    result = classify_response(speech_text)
    logger.info("Classification result: %s", result.value)

    # ── 4. Route to existing call flow ──────────────────────────────────────
    if result == FollowupResult.YES:
        # Customer confirmed issue is resolved → Case RESOLVED
        handle_yes(db, followup_id, call_id)
        ncco = build_resolved_ncco()

    elif result == FollowupResult.NO:
        # Customer said issue is NOT resolved → Case NEEDS_HUMAN
        handle_no(db, followup_id, call_id)
        ncco = build_escalate_ncco()

    else:
        # UNKNOWN or empty audio → Retry or escalate
        if attempt < 2:
            next_recording_url = (
                f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/recording"
                f"?followup_id={followup_id}&call_id={call_id}&attempt={attempt + 1}"
            )
            ncco = build_retry_ncco(next_recording_url)
        else:
            # Second attempt also unclear → escalate (fail safe)
            handle_no(db, followup_id, call_id)
            ncco = build_no_input_ncco()

    return JSONResponse(content=ncco)


# ─────────────────────────────────────────────────────────────────────────────
# 3. INPUT WEBHOOK — Backward-compatible endpoint for speech input
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/input")
async def vonage_input(
    request: Request,
    followup_id: UUID = Query(...),
    call_id: UUID = Query(...),
    attempt: int = Query(1, description="Which listen attempt this is (for retry logic)"),
    db: Session = Depends(get_db),
):
    """
    Backward-compatible input webhook handler.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Vonage input webhook [%s]: followup=%s call=%s attempt=%s",
        egypt_time, followup_id, call_id, attempt,
    )

    # ── If recording_url is present, delegate to Whisper flow ──────────────
    if "recording_url" in body:
        return await vonage_recording(
            request=request,
            followup_id=followup_id,
            call_id=call_id,
            attempt=attempt,
            db=db,
        )

    # ── Fallback extract text if provided directly ──────────────────────────
    speech_text = ""
    speech_section = body.get("speech", {})
    results = speech_section.get("results", [])
    if results:
        speech_text = results[0].get("text", "")

    logger.info("Speech text received: %r", speech_text)

    # ── Save transcript to Call.transcript ──────────────────────────────────
    if speech_text:
        try:
            call_repo = CallRepository(db)
            call = call_repo.get_by_id(call_id)
            if call:
                call.transcript = speech_text
                call_repo.update(call)
        except Exception as exc:
            logger.exception("Failed to update Call.transcript: %s", exc)

    # ── Classify Arabic response ────────────────────────────────────────────
    result = classify_response(speech_text)

    # ── Route to the right call flow ────────────────────────────────────────
    if result == FollowupResult.YES:
        handle_yes(db, followup_id, call_id)
        ncco = build_resolved_ncco()

    elif result == FollowupResult.NO:
        handle_no(db, followup_id, call_id)
        ncco = build_escalate_ncco()

    else:
        if attempt < 2:
            next_url = (
                f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/input"
                f"?followup_id={followup_id}&call_id={call_id}&attempt={attempt + 1}"
            )
            ncco = build_retry_ncco(next_url)
        else:
            handle_no(db, followup_id, call_id)
            ncco = build_no_input_ncco()

    return JSONResponse(content=ncco)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CALL NOW — Immediately places a Vonage call for a follow-up
#    Called by the frontend "📞 Call Now" button
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/call-now/{followup_id}")
def call_now(
    followup_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Immediately places a Vonage outbound call for the given follow-up.
    Does NOT wait for the scheduler — fires the call right now.

    Returns the created Call row ID on success.
    Egypt time is logged for traceability.
    """
    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Call-Now triggered [%s]: followup=%s", egypt_time, followup_id
    )

    try:
        created_call = place_vonage_followup_call(db, followup_id)
        logger.info(
            "Call-Now placed successfully [%s]: call_id=%s",
            egypt_time, created_call.id,
        )
        return {
            "success": True,
            "call_id": str(created_call.id),
            "followup_id": str(followup_id),
            "triggered_at_egypt": egypt_time,
            "message": "Call placed successfully. The phone will ring shortly.",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Call-Now failed for followup=%s: %s", followup_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to place call: {e}")
