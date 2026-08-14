"""
Webhook: Twilio POSTs here with the transcribed text of what the customer
said, after the <Gather> in the greeting (or retry) response.
 
Classifies the speech, updates the DB via the matching call_flows/*
handler, and returns the TwiML that ends (or continues) the call.
"""
from uuid import UUID
 
from fastapi import APIRouter, Depends, Form, Query, Response
from sqlalchemy.orm import Session
 
from app.core.constants import FollowupResult
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.unknown_flow import handle_unknown
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.stt.arabic_classifier import classify_response
from app.telephony.twilio.response import build_escalate_response
 
router = APIRouter(prefix="/telephony")
 
 
@router.post("/speech")
def handle_speech(
    followup_id: UUID = Query(...),
    call_id: UUID = Query(...),
    attempt: int = Query(1, description="Which gather attempt this is, for the unknown/retry flow"),
    SpeechResult: str = Form(None, description="Twilio's transcribed speech text"),
    db: Session = Depends(get_db),
):
    speech_text = SpeechResult or ""
    logger.info("Speech webhook: followup=%s call=%s attempt=%s text=%r",
                followup_id, call_id, attempt, speech_text)
 
    result = classify_response(speech_text)
 
    if result == FollowupResult.YES:
        twiml = handle_yes(db, followup_id, call_id)
    elif result == FollowupResult.NO:
        twiml = handle_no(db, followup_id, call_id)
    else:
        next_attempt = attempt + 1
        retry_speech_url = (
            f"{settings.PUBLIC_BASE_URL}/api/v1/telephony/speech"
            f"?followup_id={followup_id}&call_id={call_id}&attempt={next_attempt}"
        )
        twiml = handle_unknown(db, followup_id, call_id, retry_speech_url, attempt=attempt)
 
    return Response(content=twiml, media_type="application/xml")
 