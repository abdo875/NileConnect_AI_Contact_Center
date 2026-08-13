from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.services.case_service import CaseService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.constants import CaseStatus

router = APIRouter(prefix="/cases")


@router.get("", response_model=List[CaseResponse])
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    customer_id: Optional[UUID] = None,
    status: Optional[CaseStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Agents see only their own cases; admins see all
    from app.core.constants import UserRole
    agent_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return CaseService(db).get_all(skip=skip, limit=limit, customer_id=customer_id, agent_id=agent_id, status=status)


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(
    data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CaseService(db).create(data, agent_id=current_user.id)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CaseService(db).get_by_id(case_id)


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: UUID,
    data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CaseService(db).update(case_id, data)


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.core.constants import UserRole
    from app.core.exceptions import ForbiddenError
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Only admins can delete cases")
    CaseService(db).delete(case_id)
