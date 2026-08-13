import os
import uuid
import shutil
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.repositories.document_repository import DocumentRepository
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.core.config import settings
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.constants import DocumentStatus

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


class DocumentService:
    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[DocumentStatus] = None) -> List[DocumentResponse]:
        docs = self.repo.get_all(skip=skip, limit=limit, status=status)
        return [DocumentResponse.model_validate(d) for d in docs]

    def count(self, status: Optional[DocumentStatus] = None) -> int:
        return self.repo.count(status=status)

    def get_by_id(self, document_id: UUID) -> DocumentResponse:
        doc = self.repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(f"Document {document_id} not found")
        return DocumentResponse.model_validate(doc)

    async def upload(self, file: UploadFile, uploader_id: UUID) -> DocumentResponse:
        if file.content_type not in ALLOWED_TYPES:
            raise BadRequestError(f"File type '{file.content_type}' is not supported. Use PDF, DOCX, or TXT.")

        ext = ALLOWED_TYPES[file.content_type]
        safe_filename = f"{uuid.uuid4()}.{ext}"
        storage_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(storage_path, "wb") as dest:
            shutil.copyfileobj(file.file, dest)

        file_size = os.path.getsize(storage_path)

        doc = Document(
            filename=safe_filename,
            original_name=file.filename,
            file_type=ext,
            storage_path=storage_path,
            file_size=file_size,
            uploaded_by=uploader_id,
            status=DocumentStatus.READY,  # Phase 1: mark ready immediately (no processing pipeline)
        )
        created = self.repo.create(doc)
        return DocumentResponse.model_validate(created)

    def delete(self, document_id: UUID) -> None:
        doc = self.repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(f"Document {document_id} not found")
        # Remove physical file
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
        self.repo.delete(doc)
