from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService
from app.api.dependencies import get_current_user, require_admin
from app.models.user import User
from app.core.constants import DocumentStatus

router = APIRouter(prefix="/documents")


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[DocumentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_all(skip=skip, limit=limit, status=status)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Upload a PDF, DOCX, or TXT document to the knowledge base (admin only)."""
    service = DocumentService(db)
    return await service.upload(file, uploader_id=current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_by_id(document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    DocumentService(db).delete(document_id)
