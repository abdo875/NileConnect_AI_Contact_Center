from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.document import Document
from app.core.constants import DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: UUID) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None,
    ) -> List[Document]:
        query = self.db.query(Document)
        if status:
            query = query.filter(Document.status == status)
        return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, status: Optional[DocumentStatus] = None) -> int:
        query = self.db.query(Document)
        if status:
            query = query.filter(Document.status == status)
        return query.count()

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: Document) -> Document:
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
