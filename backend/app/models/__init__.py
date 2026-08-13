# Import all models here so SQLAlchemy can discover them
from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.case import Case  # noqa: F401
from app.models.call import Call  # noqa: F401
from app.models.ai_followup import AIFollowup  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

__all__ = ["Base", "User", "Customer", "Case", "Call", "AIFollowup", "Document", "AuditLog"]
