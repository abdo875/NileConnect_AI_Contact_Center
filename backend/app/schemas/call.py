from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.constants import CallType, CallOutcome


class CallCreate(BaseModel):
    customer_id: UUID
    case_id: Optional[UUID] = None
    call_type: CallType
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    summary: Optional[str] = None
    outcome: CallOutcome = CallOutcome.PENDING
    transcript: Optional[str] = None


class CallResponse(BaseModel):
    id: UUID
    customer_id: UUID
    case_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    call_type: CallType
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    summary: Optional[str] = None
    outcome: CallOutcome
    transcript: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
