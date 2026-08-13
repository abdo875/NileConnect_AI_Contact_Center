import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    cases = relationship("Case", back_populates="customer", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="customer")
    followups = relationship("AIFollowup", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.name} phone={self.phone}>"
