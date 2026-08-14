"""
Places the outbound AI follow-up call via Twilio.
 
Creates the Call row FIRST (before dialing), so both the answer webhook
(incoming.py) and the status webhook (status.py) have a call_id to work
with from the very start of the call's life — including the no-answer
case, where incoming.py never fires at all.
"""
from datetime import datetime, timezone
from uuid import UUID
 
from sqlalchemy.orm import Session
 
from app.core.config import settings
from app.core.constants import CallOutcome, CallType, FollowupStatus
from app.core.logging import logger
from app.models.call import Call
from app.repositories.call_repository import CallRepository
from app.repositories.followup_repository import FollowupRepository
from app.telephony.twilio.client import get_from_number, get_twilio_client
 
 
def place_followup_call(db: Session, followup_id: UUID) -> Call:
    """
    Dials the customer for the given AIFollowup. Returns the created Call
    row. Raises if the follow-up doesn't exist or the customer has no
    usable phone number — callers should catch and mark the follow-up
    FAILED if this raises.
    """
    followup_repo = FollowupRepository(db)
    followup = followup_repo.get_by_id(followup_id)
    if not followup:
        raise ValueError(f"AIFollowup {followup_id} not found")
 
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
 
    incoming_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/telephony/incoming"
        f"?followup_id={followup_id}&call_id={created_call.id}"
    )
    status_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/telephony/status"
        f"?followup_id={followup_id}&call_id={created_call.id}"
    )
 
    customer_phone = followup.customer.phone  # assumes relationship is loaded
 
    client = get_twilio_client()
    twilio_call = client.calls.create(
        to=customer_phone,
        from_=get_from_number(),
        url=incoming_url,
        status_callback=status_url,
        status_callback_event=["completed", "no-answer", "busy", "failed", "canceled"],
        status_callback_method="POST",
    )
 
    logger.info("Placed outbound AI call: followup=%s call=%s twilio_sid=%s",
                followup_id, created_call.id, twilio_call.sid)
 
    return created_call
 