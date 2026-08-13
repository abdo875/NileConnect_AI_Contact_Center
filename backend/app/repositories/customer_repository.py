from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.phone == phone).first()

    def get_all(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Customer]:
        query = self.db.query(Customer)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Customer.name.ilike(like), Customer.phone.ilike(like), Customer.email.ilike(like))
            )
        return query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, search: Optional[str] = None) -> int:
        query = self.db.query(Customer)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Customer.name.ilike(like), Customer.phone.ilike(like), Customer.email.ilike(like))
            )
        return query.count()

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete(self, customer: Customer) -> None:
        self.db.delete(customer)
        self.db.commit()
