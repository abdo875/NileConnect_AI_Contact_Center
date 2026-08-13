import uuid
from sqlalchemy import Column, String, BigInteger, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import DocumentStatus


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(SAEnum(DocumentStatus, name="document_status"), nullable=False, default=DocumentStatus.UPLOADING, index=True)

    # Relationships
    uploader = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status}>"
