from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.followup_repository import FollowupRepository
from app.repositories.case_repository import CaseRepository
from app.models.ai_followup import AIFollowup
from app.schemas.followup import FollowupCreate, FollowupUpdate, FollowupResponse
from app.core.exceptions import NotFoundError
from app.core.constants import CaseStatus, FollowupStatus


class FollowupService:
    def __init__(self, db: Session):
        self.repo = FollowupRepository(db)
        self.case_repo = CaseRepository(db)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        case_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        status: Optional[FollowupStatus] = None,
    ) -> List[FollowupResponse]:
        followups = self.repo.get_all(skip=skip, limit=limit, case_id=case_id, customer_id=customer_id, status=status)
        return [FollowupResponse.model_validate(f) for f in followups]

    def count(self, case_id=None, customer_id=None, status=None) -> int:
        return self.repo.count(case_id=case_id, customer_id=customer_id, status=status)

    def get_by_id(self, followup_id: UUID) -> FollowupResponse:
        followup = self.repo.get_by_id(followup_id)
        if not followup:
            raise NotFoundError(f"Follow-up {followup_id} not found")
        return FollowupResponse.model_validate(followup)

    def create(self, data: FollowupCreate) -> FollowupResponse:
        # Verify case exists
        case = self.case_repo.get_by_id(data.case_id)
        if not case:
            raise NotFoundError(f"Case {data.case_id} not found")

        followup = AIFollowup(**data.model_dump())
        created = self.repo.create(followup)

        # Update case status to AI_FOLLOW_UP_SCHEDULED
        case.status = CaseStatus.AI_FOLLOW_UP_SCHEDULED
        self.case_repo.update(case)

        return FollowupResponse.model_validate(created)

    def update(self, followup_id: UUID, data: FollowupUpdate) -> FollowupResponse:
        followup = self.repo.get_by_id(followup_id)
        if not followup:
            raise NotFoundError(f"Follow-up {followup_id} not found")
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(followup, key, value)
        updated = self.repo.update(followup)
        return FollowupResponse.model_validate(updated)
