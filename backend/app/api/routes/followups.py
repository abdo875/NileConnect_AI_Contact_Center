from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.followup import FollowupCreate, FollowupUpdate, FollowupResponse
from app.services.followup_service import FollowupService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.constants import FollowupStatus

router = APIRouter(prefix="/followups")


@router.get("", response_model=List[FollowupResponse])
def list_followups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    case_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    status: Optional[FollowupStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FollowupService(db).get_all(skip=skip, limit=limit, case_id=case_id, customer_id=customer_id, status=status)


@router.post("", response_model=FollowupResponse, status_code=201)
def create_followup(
    data: FollowupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FollowupService(db).create(data)


@router.get("/{followup_id}", response_model=FollowupResponse)
def get_followup(
    followup_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FollowupService(db).get_by_id(followup_id)


@router.patch("/{followup_id}", response_model=FollowupResponse)
def update_followup(
    followup_id: UUID,
    data: FollowupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FollowupService(db).update(followup_id, data)
