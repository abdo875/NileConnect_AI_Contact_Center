from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.constants import CaseStatus, CasePriority, CaseCategory
from app.schemas.customer import CustomerResponse
from app.schemas.user import UserResponse


class CaseCreate(BaseModel):
    customer_id: UUID
    assigned_agent_id: Optional[UUID] = None
    issue: str
    category: CaseCategory = CaseCategory.OTHER
    description: Optional[str] = None
    priority: CasePriority = CasePriority.MEDIUM


class CaseUpdate(BaseModel):
    assigned_agent_id: Optional[UUID] = None
    issue: Optional[str] = None
    category: Optional[CaseCategory] = None
    description: Optional[str] = None
    priority: Optional[CasePriority] = None
    status: Optional[CaseStatus] = None


class CaseResponse(BaseModel):
    id: UUID
    customer_id: UUID
    assigned_agent_id: Optional[UUID] = None
    issue: str
    category: CaseCategory
    description: Optional[str] = None
    priority: CasePriority
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    customer: Optional[CustomerResponse] = None
    assigned_agent: Optional[UserResponse] = None

    model_config = {"from_attributes": True}
