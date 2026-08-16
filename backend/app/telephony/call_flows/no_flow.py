"""
Call flow branch: customer said the problem is NOT resolved.
 
Escalates: Case moves to NEEDS_HUMAN so it surfaces on the human agent's
dashboard. The AI does not attempt any troubleshooting itself.
"""
from datetime import datetime, timezone
 
from sqlalchemy.orm import Session
 
from app.core.constants import CallOutcome, CaseStatus, FollowupResult, FollowupStatus
from app.repositories.call_repository import CallRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.followup_repository import FollowupRepository
from app.telephony.twilio.response import build_escalate_response
 
 
def handle_no(db: Session, followup_id, call_id) -> str:
    followup_repo = FollowupRepository(db)
    call_repo = CallRepository(db)
    case_repo = CaseRepository(db)
 
    followup = followup_repo.get_by_id(followup_id)
    call = call_repo.get_by_id(call_id)
 
    now = datetime.now(timezone.utc)
 
    if call:
        call.outcome = CallOutcome.ESCALATED
        call.ended_at = now
        call_repo.update(call)
 
    if followup:
        followup.status = FollowupStatus.COMPLETED
        followup.result = FollowupResult.NO
        followup.completed_at = now
        followup_repo.update(followup)
 
        case = case_repo.get_by_id(followup.case_id)
        if case:
            case.status = CaseStatus.NEEDS_HUMAN
            case_repo.update(case)
 
    return build_escalate_response()
 