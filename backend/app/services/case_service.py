from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.case_repository import CaseRepository
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.core.exceptions import NotFoundError
from app.core.constants import CaseStatus


class CaseService:
    def __init__(self, db: Session):
        self.repo = CaseRepository(db)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[CaseStatus] = None,
    ) -> List[CaseResponse]:
        cases = self.repo.get_all(skip=skip, limit=limit, customer_id=customer_id, agent_id=agent_id, status=status)
        return [CaseResponse.model_validate(c) for c in cases]

    def count(
        self,
        customer_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[CaseStatus] = None,
    ) -> int:
        return self.repo.count(customer_id=customer_id, agent_id=agent_id, status=status)

    def get_by_id(self, case_id: UUID) -> CaseResponse:
        case = self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        return CaseResponse.model_validate(case)

    def create(self, data: CaseCreate, agent_id: Optional[UUID] = None) -> CaseResponse:
        case_data = data.model_dump()
        # Auto-assign the creating agent if not explicitly assigned
        if not case_data.get("assigned_agent_id") and agent_id:
            case_data["assigned_agent_id"] = agent_id
        case = Case(**case_data)
        created = self.repo.create(case)
        return CaseResponse.model_validate(created)

    def update(self, case_id: UUID, data: CaseUpdate) -> CaseResponse:
        case = self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(case, key, value)
        # Set resolved_at when status becomes RESOLVED
        if data.status == CaseStatus.RESOLVED and not case.resolved_at:
            case.resolved_at = datetime.now(timezone.utc)
        updated = self.repo.update(case)
        return CaseResponse.model_validate(updated)

    def delete(self, case_id: UUID) -> None:
        case = self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        self.repo.delete(case)
