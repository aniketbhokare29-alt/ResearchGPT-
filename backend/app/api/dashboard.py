from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models import GeneratedReport, ResearchCollection, ResearchPaper
from app.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return counts scoped to the authenticated user's workspace."""
    return {
        "papers": db.scalar(
            select(func.count()).select_from(ResearchPaper).where(ResearchPaper.owner_id == user.id)
        ) or 0,
        "analyzed_papers": db.scalar(
            select(func.count()).select_from(ResearchPaper).where(
                ResearchPaper.owner_id == user.id,
                ResearchPaper.processing_status == "completed",
            )
        ) or 0,
        "collections": db.scalar(
            select(func.count()).select_from(ResearchCollection).where(ResearchCollection.owner_id == user.id)
        ) or 0,
        "reports": db.scalar(
            select(func.count()).select_from(GeneratedReport).where(GeneratedReport.owner_id == user.id)
        ) or 0,
    }
