import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)


@app.exception_handler(OperationalError)
async def database_unavailable_handler(_request, _exc: OperationalError):
    logger.exception("Database operation failed")
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is unavailable. Start PostgreSQL and apply migrations."},
    )

