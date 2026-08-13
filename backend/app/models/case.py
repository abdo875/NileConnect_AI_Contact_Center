import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import CaseStatus, CasePriority, CaseCategory


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    issue = Column(String(500), nullable=False)
    category = Column(SAEnum(CaseCategory, name="case_category"), nullable=False, default=CaseCategory.OTHER)
    description = Column(Text, nullable=True)
    priority = Column(SAEnum(CasePriority, name="case_priority"), nullable=False, default=CasePriority.MEDIUM)
    status = Column(SAEnum(CaseStatus, name="case_status"), nullable=False, default=CaseStatus.OPEN, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="cases")
    assigned_agent = relationship("User", back_populates="assigned_cases", foreign_keys=[assigned_agent_id])
    calls = relationship("Call", back_populates="case")
    followups = relationship("AIFollowup", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Case id={self.id} status={self.status} priority={self.priority}>"
