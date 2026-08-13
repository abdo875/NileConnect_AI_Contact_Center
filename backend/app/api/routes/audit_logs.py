from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.audit_log_service import AuditLogService
from app.api.dependencies import require_admin
from app.models.user import User

router = APIRouter(prefix="/audit-logs")


@router.get("")
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve audit log entries (admin only)."""
    return AuditLogService(db).get_all(skip=skip, limit=limit, entity_type=entity_type)
