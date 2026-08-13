from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.report_service import ReportService
from app.api.dependencies import require_admin
from app.models.user import User

router = APIRouter(prefix="/reports")


@router.get("/summary")
def get_summary(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Overall platform statistics (admin only)."""
    return ReportService(db).get_summary()


@router.get("/cases-by-status")
def cases_by_status(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReportService(db).get_cases_by_status()


@router.get("/cases-by-category")
def cases_by_category(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReportService(db).get_cases_by_category()
