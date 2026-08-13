from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.constants import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    original_name: str
    file_type: str
    file_size: Optional[int] = None
    uploaded_by: Optional[UUID] = None
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
