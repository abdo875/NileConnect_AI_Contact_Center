import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.core.constants import CallType, CallOutcome
from datetime import datetime, timezone


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    call_type = Column(SAEnum(CallType, name="call_type"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    summary = Column(Text, nullable=True)
    outcome = Column(SAEnum(CallOutcome, name="call_outcome"), nullable=False, default=CallOutcome.PENDING)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="calls")
    case = relationship("Case", back_populates="calls")
    agent = relationship("User", back_populates="calls", foreign_keys=[agent_id])

    def __repr__(self) -> str:
        return f"<Call id={self.id} type={self.call_type} outcome={self.outcome}>"
