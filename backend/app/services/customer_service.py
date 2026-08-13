from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.customer_repository import CustomerRepository
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.exceptions import NotFoundError, ConflictError


class CustomerService:
    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[CustomerResponse]:
        customers = self.repo.get_all(skip=skip, limit=limit, search=search)
        return [CustomerResponse.model_validate(c) for c in customers]

    def count(self, search: Optional[str] = None) -> int:
        return self.repo.count(search=search)

    def get_by_id(self, customer_id: UUID) -> CustomerResponse:
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        return CustomerResponse.model_validate(customer)

    def create(self, data: CustomerCreate) -> CustomerResponse:
        if self.repo.get_by_phone(data.phone):
            raise ConflictError(f"A customer with phone '{data.phone}' already exists")
        customer = Customer(**data.model_dump())
        created = self.repo.create(customer)
        return CustomerResponse.model_validate(created)

    def update(self, customer_id: UUID, data: CustomerUpdate) -> CustomerResponse:
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        updates = data.model_dump(exclude_unset=True)
        if "phone" in updates:
            existing = self.repo.get_by_phone(updates["phone"])
            if existing and existing.id != customer_id:
                raise ConflictError(f"Phone '{updates['phone']}' is already in use")
        for key, value in updates.items():
            setattr(customer, key, value)
        updated = self.repo.update(customer)
        return CustomerResponse.model_validate(updated)

    def delete(self, customer_id: UUID) -> None:
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        self.repo.delete(customer)
