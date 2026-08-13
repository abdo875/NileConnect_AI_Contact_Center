from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog
from app.schemas.common import PaginatedResponse
import math


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: Optional[UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()

    def get_all(self, skip: int = 0, limit: int = 100, entity_type: Optional[str] = None) -> dict:
        query = self.db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        return {
            "items": logs,
            "total": total,
            "page": skip // limit + 1 if limit else 1,
            "page_size": limit,
            "pages": math.ceil(total / limit) if limit else 1,
        }
