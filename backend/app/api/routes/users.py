from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.api.dependencies import require_admin
from app.models.user import User
from app.core.constants import UserRole

router = APIRouter(prefix="/users")


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: Optional[UserRole] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).get_all(skip=skip, limit=limit, role=role)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).create(data)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).update(user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    UserService(db).delete(user_id)
