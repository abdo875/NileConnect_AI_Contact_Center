from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError
from app.core.constants import UserRole


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None) -> List[UserResponse]:
        users = self.repo.get_all(skip=skip, limit=limit, role=role)
        return [UserResponse.model_validate(u) for u in users]

    def get_by_id(self, user_id: UUID) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return UserResponse.model_validate(user)

    def create(self, data: UserCreate) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise ConflictError(f"A user with email '{data.email}' already exists")
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
        )
        created = self.repo.create(user)
        return UserResponse.model_validate(created)

    def update(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        if data.name is not None:
            user.name = data.name
        if data.email is not None:
            existing = self.repo.get_by_email(data.email)
            if existing and existing.id != user_id:
                raise ConflictError(f"Email '{data.email}' is already in use")
            user.email = data.email
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        updated = self.repo.update(user)
        return UserResponse.model_validate(updated)

    def delete(self, user_id: UUID) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        self.repo.delete(user)

    def count(self, role: Optional[UserRole] = None) -> int:
        return self.repo.count(role=role)
