"""
Vonage voice webhooks + Call-Now trigger.

Vonage calls two URLs during an outbound call:

  GET  /api/v1/vonage/answer
       Vonage fetches this when the callee picks up.
       Returns the NCCO (Arabic greeting + speech input action).

  POST /api/v1/vonage/input
       Vonage POSTs the speech recognition result here after the customer speaks.
       Classifies the Arabic response, updates the DB, returns a closing NCCO.

  POST /api/v1/vonage/call-now/{followup_id}
       Internal endpoint — called by the frontend "Call Now" button.
       Immediately places a Vonage call for the given follow-up.

All timestamps are in Egypt time (UTC+3 / EET).
Both webhook endpoints receive followup_id and call_id as query parameters —
embedded in the URLs when placing the call so we can always look up the right
DB records without relying on Vonage's own call UUID.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.constants import FollowupResult
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.stt.arabic_classifier import classify_response
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
    Returns the NCCO that plays the Arabic greeting and starts listening.
    """
    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Vonage answer webhook [%s]: followup=%s call=%s",
        egypt_time, followup_id, call_id,
    )

    # The input webhook URL — Vonage will POST the speech result here
    input_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/input"
        f"?followup_id={followup_id}&call_id={call_id}&attempt=1"
    )

    ncco = build_greeting_ncco(input_url)
    return JSONResponse(content=ncco)


# ─────────────────────────────────────────────────────────────────────────────
# 2. INPUT WEBHOOK — Vonage POSTs speech recognition result here
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
    Called by Vonage (POST) with the transcribed Arabic speech after <input>.

    Vonage sends a JSON body with shape:
      {
        "speech": {
          "results": [{"text": "أيوه اتحلت", "confidence": 0.95}, ...],
          "timeout_reason": "end_on_silence" | "max_duration" | null
        },
        ...
      }

    We extract the top result text, classify it, update the DB, and return
    the appropriate closing NCCO.
    """
    body = await request.json()
    egypt_time = _egypt_now().strftime("%Y-%m-%d %H:%M:%S EET")
    logger.info(
        "Vonage input webhook [%s]: followup=%s call=%s attempt=%s",
        egypt_time, followup_id, call_id, attempt,
    )

    # ── Extract speech text ────────────────────────────────────────────────
    speech_text = ""
    speech_section = body.get("speech", {})
    results = speech_section.get("results", [])
    if results:
        # Vonage returns results sorted by confidence (highest first)
        speech_text = results[0].get("text", "")

    logger.info("Speech recognised: %r", speech_text)

    # ── Classify Arabic response ────────────────────────────────────────────
    result = classify_response(speech_text)

    # ── Route to the right call flow ────────────────────────────────────────
    if result == FollowupResult.YES:
        # Customer said the issue IS resolved → mark case RESOLVED in DB
        handle_yes(db, followup_id, call_id)
        ncco = build_resolved_ncco()

    elif result == FollowupResult.NO:
        # Customer said the issue is NOT resolved → escalate to human
        handle_no(db, followup_id, call_id)
        ncco = build_escalate_ncco()

    else:
        # Could not understand — give one retry, then fail safe
        if attempt < 2:
            next_input_url = (
                f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/input"
                f"?followup_id={followup_id}&call_id={call_id}&attempt={attempt + 1}"
            )
            ncco = build_retry_ncco(next_input_url)
        else:
            # Second attempt also unclear → escalate (fail safe)
            handle_no(db, followup_id, call_id)
            ncco = build_no_input_ncco()

    return JSONResponse(content=ncco)


# ─────────────────────────────────────────────────────────────────────────────
# 3. CALL NOW — Immediately places a Vonage call for a follow-up
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
