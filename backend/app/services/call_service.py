from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.call_repository import CallRepository
from app.models.call import Call
from app.schemas.call import CallCreate, CallResponse
from app.core.exceptions import NotFoundError


class CallService:
    def __init__(self, db: Session):
        self.repo = CallRepository(db)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
    ) -> List[CallResponse]:
        calls = self.repo.get_all(skip=skip, limit=limit, customer_id=customer_id, case_id=case_id, agent_id=agent_id)
        return [CallResponse.model_validate(c) for c in calls]

    def count(
        self,
        customer_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
    ) -> int:
        return self.repo.count(customer_id=customer_id, case_id=case_id, agent_id=agent_id)

    def get_by_id(self, call_id: UUID) -> CallResponse:
        call = self.repo.get_by_id(call_id)
        if not call:
            raise NotFoundError(f"Call {call_id} not found")
        return CallResponse.model_validate(call)

    def create(self, data: CallCreate, agent_id: Optional[UUID] = None) -> CallResponse:
        call_data = data.model_dump()
        if not call_data.get("started_at"):
            call_data["started_at"] = datetime.now(timezone.utc)
        call = Call(**call_data, agent_id=agent_id)
        created = self.repo.create(call)
        return CallResponse.model_validate(created)
