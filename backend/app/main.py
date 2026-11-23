import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import update
from sqlalchemy.exc import OperationalError

from app.api.auth import router as auth_router
from app.api.collections import router as collections_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.papers import router as papers_router
from app.core.config import settings
from app.database.session import SessionLocal
from app.models import ResearchPaper

logger = logging.getLogger(__name__)


def recover_interrupted_jobs():
    db = SessionLocal()
    try:
        db.execute(
            update(ResearchPaper)
            .where(ResearchPaper.processing_status.in_(["pending", "running"]))
            .values(
                processing_status="failed",
                processing_step="interrupted",
                processing_error="Processing did not finish before the server restarted. Retry from the paper page.",
            )
        )
        db.execute(
            update(ResearchPaper)
            .where(ResearchPaper.summary_status.in_(["pending", "running"]))
            .values(
                summary_status="failed",
                summary_error="Summary generation did not finish before the server restarted. Request it again.",
            )
        )
        db.commit()
    except OperationalError:
        db.rollback()
        logger.warning("Could not recover interrupted paper jobs because the database is unavailable.")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app):
    recover_interrupted_jobs()
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(papers_router, prefix=settings.api_v1_prefix)
app.include_router(collections_router, prefix=settings.api_v1_prefix)


@app.exception_handler(OperationalError)
async def database_unavailable_handler(_request, _exc: OperationalError):
    logger.exception("Database operation failed")
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is unavailable. Start PostgreSQL and apply migrations."},
    )

