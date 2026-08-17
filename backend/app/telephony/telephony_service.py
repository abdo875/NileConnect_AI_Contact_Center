"""
Single entry point for triggering an AI follow-up call via Vonage.

This is what the scheduler (backend/app/scheduler/) calls when a
follow-up's scheduled_at time arrives. Kept separate from outbound_call.py
so retry/failure bookkeeping lives in one obvious place rather than
scattered across whoever calls trigger_followup_call.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import FollowupStatus
from app.core.logging import logger
from app.repositories.followup_repository import FollowupRepository
from app.telephony.vonage.outbound_call import place_vonage_followup_call


def trigger_followup_call(db: Session, followup_id: UUID) -> None:
    """
    Attempts to place the outbound Vonage call for a scheduled follow-up.

    On failure (bad credentials, Vonage API error, etc.), marks the
    follow-up FAILED rather than leaving it stuck SCHEDULED forever.
    """
    try:
        place_vonage_followup_call(db, followup_id)
    except Exception:
        logger.exception("Failed to place Vonage follow-up call for %s", followup_id)
        followup_repo = FollowupRepository(db)
        followup = followup_repo.get_by_id(followup_id)
        if followup:
            followup.status = FollowupStatus.FAILED
            followup_repo.update(followup)