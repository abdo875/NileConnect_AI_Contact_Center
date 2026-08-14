"""
Webhook: Twilio POSTs call status changes here (queued, ringing, answered,
completed, busy, failed, no-answer), via the statusCallback URL we set
when placing the outbound call.
 
We identify the call via our own `call_id` query param (passed in the
statusCallback URL we control) rather than Twilio's CallSid, sidestepping
the fact that the Call model doesn't yet store twilio_call_sid.
 
This mainly matters for the case where the customer never answers at all —
`incoming.py` (and therefore the whole rest of the flow) never fires, so
this is the only place a no-answer/failed attempt gets recorded.
"""
from datetime import datetime, timezone
from uuid import UUID
 
from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.orm import Session
 
from app.core.constants import CallOutcome, FollowupResult, FollowupStatus
from app.core.database import get_db
from app.core.logging import logger
from app.repositories.call_repository import CallRepository
from app.repositories.followup_repository import FollowupRepository
 
router = APIRouter(prefix="/telephony")
 
# Twilio statuses that mean the call never actually connected to the customer.
NO_CONNECT_STATUSES = {"no-answer", "busy", "failed", "canceled"}
 
 
@router.post("/status")
def handle_call_status(
    followup_id: UUID = Query(...),
    call_id: UUID = Query(...),
    CallStatus: str = Form(None),
    db: Session = Depends(get_db),
):
    logger.info("Status webhook: followup=%s call=%s status=%s", followup_id, call_id, CallStatus)
 
    if CallStatus not in NO_CONNECT_STATUSES:
        # "completed" is already handled by yes_flow/no_flow when the
        # customer actually answered and spoke. Nothing more to do here.
        return {"ok": True}
 
    call_repo = CallRepository(db)
    followup_repo = FollowupRepository(db)
 
    call = call_repo.get_by_id(call_id)
    followup = followup_repo.get_by_id(followup_id)
 
    now = datetime.now(timezone.utc)
 
    if call:
        call.outcome = CallOutcome.NO_ANSWER
        call.ended_at = now
        call_repo.update(call)
 
    if followup:
        followup.status = FollowupStatus.FAILED
        followup.result = FollowupResult.NO_ANSWER
        followup.completed_at = now
        followup_repo.update(followup)
        # Note: does NOT change Case.status. A no-answer isn't a decision
        # about the case, just a failed contact attempt — leave the case
        # as-is so a human can decide whether to retry or escalate.
 
    return {"ok": True}
 