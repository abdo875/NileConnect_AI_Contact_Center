from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.call import Call


class CallRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, call_id: UUID) -> Optional[Call]:
        return self.db.query(Call).filter(Call.id == call_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
    ) -> List[Call]:
        query = self.db.query(Call)
        if customer_id:
            query = query.filter(Call.customer_id == customer_id)
        if case_id:
            query = query.filter(Call.case_id == case_id)
        if agent_id:
            query = query.filter(Call.agent_id == agent_id)
        return query.order_by(Call.started_at.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        customer_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
    ) -> int:
        query = self.db.query(Call)
        if customer_id:
            query = query.filter(Call.customer_id == customer_id)
        if case_id:
            query = query.filter(Call.case_id == case_id)
        if agent_id:
            query = query.filter(Call.agent_id == agent_id)
        return query.count()

    def create(self, call: Call) -> Call:
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call

    def update(self, call: Call) -> Call:
        self.db.commit()
        self.db.refresh(call)
        return call
