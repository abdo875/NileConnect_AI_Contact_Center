from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.constants import FollowupStatus, FollowupResult


class FollowupCreate(BaseModel):
    case_id: UUID
    customer_id: UUID
    scheduled_at: datetime
    notes: Optional[str] = None


class FollowupUpdate(BaseModel):
    status: Optional[FollowupStatus] = None
    result: Optional[FollowupResult] = None
    call_id: Optional[UUID] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class FollowupResponse(BaseModel):
    id: UUID
    case_id: UUID
    customer_id: UUID
    scheduled_at: datetime
    status: FollowupStatus
    attempt_number: int
    result: Optional[FollowupResult] = None
    call_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
