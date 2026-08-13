import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.core.constants import FollowupStatus, FollowupResult
from datetime import datetime, timezone


class AIFollowup(Base):
    __tablename__ = "ai_followups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SAEnum(FollowupStatus, name="followup_status"), nullable=False, default=FollowupStatus.SCHEDULED, index=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    result = Column(SAEnum(FollowupResult, name="followup_result"), nullable=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    case = relationship("Case", back_populates="followups")
    customer = relationship("Customer", back_populates="followups")

    def __repr__(self) -> str:
        return f"<AIFollowup id={self.id} status={self.status} scheduled_at={self.scheduled_at}>"
