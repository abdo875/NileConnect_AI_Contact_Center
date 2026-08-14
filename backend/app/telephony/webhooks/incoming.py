from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import CallOutcome, CallType, FollowupStatus
from app.core.database import get_db
from app.core.logging import logger
from app.models.call import Call
from app.repositories.call_repository import CallRepository
from app.repositories.followup_repository import FollowupRepository
from app.telephony.twilio.response import build_escalate_response, build_greeting_response

router = APIRouter(prefix="/telephony")


@router.post("/incoming")
def handle_incoming_call(
    followup_id: UUID = Query(..., description="AIFollowup this call belongs to"),
    CallSid: str = Form(None),
    db: Session = Depends(get_db),
):
    followup_repo = FollowupRepository(db)
    followup = followup_repo.get_by_id(followup_id)

    if not followup:
        # Follow-up vanished between scheduling and the call connecting.
        # We must still return valid TwiML or the live call errors out.
        logger.error("Incoming call webhook: follow-up %s not found", followup_id)
        return Response(content=build_escalate_response(), media_type="application/xml")

    # TODO: Call model has no twilio_call_sid column yet — needed so the
    # status webhook (call completed/failed/no-answer) can look up this
    # exact Call row later. Raise with Abdelrahman: add a nullable
    # `twilio_call_sid` (String, indexed) column + migration on Call.
    # Once added, set it here: call.twilio_call_sid = CallSid
    if not CallSid:
        logger.warning("Incoming call webhook received with no CallSid (manual test?)")

    call = Call(
        customer_id=followup.customer_id,
        case_id=followup.case_id,
        call_type=CallType.OUTBOUND_AI,
        started_at=datetime.now(timezone.utc),
        outcome=CallOutcome.PENDING,
    )
    call_repo = CallRepository(db)
    created_call = call_repo.create(call)

    followup.call_id = created_call.id
    followup.status = FollowupStatus.IN_PROGRESS
    followup_repo.update(followup)

    speech_webhook_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/telephony/speech"
        f"?followup_id={followup_id}&call_id={created_call.id}"
    )
    twiml = build_greeting_response(speech_webhook_url)
    return Response(content=twiml, media_type="application/xml")