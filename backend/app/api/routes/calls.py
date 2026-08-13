from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.call import CallCreate, CallResponse
from app.services.call_service import CallService
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/calls")


@router.get("", response_model=List[CallResponse])
def list_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    customer_id: Optional[UUID] = None,
    case_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CallService(db).get_all(skip=skip, limit=limit, customer_id=customer_id, case_id=case_id)


@router.post("", response_model=CallResponse, status_code=201)
def create_call(
    data: CallCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CallService(db).create(data, agent_id=current_user.id)


@router.get("/{call_id}", response_model=CallResponse)
def get_call(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CallService(db).get_by_id(call_id)
