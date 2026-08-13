from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.case import Case
from app.models.customer import Customer
from app.models.call import Call
from app.models.ai_followup import AIFollowup
from app.models.user import User
from app.core.constants import CaseStatus, UserRole, FollowupStatus


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> dict:
        total_customers = self.db.query(func.count(Customer.id)).scalar()
        total_cases = self.db.query(func.count(Case.id)).scalar()
        open_cases = self.db.query(func.count(Case.id)).filter(Case.status == CaseStatus.OPEN).scalar()
        in_progress_cases = self.db.query(func.count(Case.id)).filter(Case.status == CaseStatus.IN_PROGRESS).scalar()
        resolved_cases = self.db.query(func.count(Case.id)).filter(Case.status == CaseStatus.RESOLVED).scalar()
        needs_human = self.db.query(func.count(Case.id)).filter(Case.status == CaseStatus.NEEDS_HUMAN).scalar()
        pending_followups = self.db.query(func.count(AIFollowup.id)).filter(
            AIFollowup.status == FollowupStatus.SCHEDULED
        ).scalar()
        total_calls = self.db.query(func.count(Call.id)).scalar()
        total_agents = self.db.query(func.count(User.id)).filter(User.role == UserRole.CALL_CENTER, User.is_active == True).scalar()

        return {
            "total_customers": total_customers,
            "total_cases": total_cases,
            "open_cases": open_cases,
            "in_progress_cases": in_progress_cases,
            "resolved_cases": resolved_cases,
            "needs_human": needs_human,
            "pending_followups": pending_followups,
            "total_calls": total_calls,
            "total_agents": total_agents,
        }

    def get_cases_by_status(self) -> dict:
        rows = (
            self.db.query(Case.status, func.count(Case.id))
            .group_by(Case.status)
            .all()
        )
        return {row[0].value: row[1] for row in rows}

    def get_cases_by_category(self) -> dict:
        rows = (
            self.db.query(Case.category, func.count(Case.id))
            .group_by(Case.category)
            .all()
        )
        return {row[0].value: row[1] for row in rows}
