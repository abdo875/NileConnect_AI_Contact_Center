from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.models.case import Case
from app.core.constants import CaseStatus


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, case_id: UUID) -> Optional[Case]:
        return (
            self.db.query(Case)
            .options(joinedload(Case.customer), joinedload(Case.assigned_agent))
            .filter(Case.id == case_id)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[CaseStatus] = None,
    ) -> List[Case]:
        query = self.db.query(Case).options(
            joinedload(Case.customer), joinedload(Case.assigned_agent)
        )
        if customer_id:
            query = query.filter(Case.customer_id == customer_id)
        if agent_id:
            query = query.filter(Case.assigned_agent_id == agent_id)
        if status:
            query = query.filter(Case.status == status)
        return query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        customer_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[CaseStatus] = None,
    ) -> int:
        query = self.db.query(Case)
        if customer_id:
            query = query.filter(Case.customer_id == customer_id)
        if agent_id:
            query = query.filter(Case.assigned_agent_id == agent_id)
        if status:
            query = query.filter(Case.status == status)
        return query.count()

    def create(self, case: Case) -> Case:
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return self.get_by_id(case.id)  # reload with relationships

    def update(self, case: Case) -> Case:
        self.db.commit()
        self.db.refresh(case)
        return case

    def delete(self, case: Case) -> None:
        self.db.delete(case)
        self.db.commit()
