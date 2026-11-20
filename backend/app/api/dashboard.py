from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import GeneratedReport, ResearchCollection, ResearchPaper

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Return aggregate workspace counts for the dashboard.

    Authentication and per-user scoping will be added in the accounts phase.
    Until then, this endpoint deliberately returns aggregate counts only.
    """
    return {
        "papers": db.scalar(select(func.count()).select_from(ResearchPaper)) or 0,
        "analyzed_papers": db.scalar(
            select(func.count()).select_from(ResearchPaper).where(ResearchPaper.processing_status == "completed")
        ) or 0,
        "collections": db.scalar(select(func.count()).select_from(ResearchCollection)) or 0,
        "reports": db.scalar(select(func.count()).select_from(GeneratedReport)) or 0,
    }
