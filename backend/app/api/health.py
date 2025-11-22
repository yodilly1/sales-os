<<<<<<< HEAD
"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
=======
"""Health check endpoint."""

from fastapi import APIRouter
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP

router = APIRouter()


<<<<<<< HEAD
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str
    environment: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response."""

    database: str
    services: dict


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
) -> DetailedHealthResponse:
    """Detailed health check with service status."""
    # Check database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return DetailedHealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
        services={
            "auth": "healthy",
            "rate_limiter": "healthy",
        },
    )
=======
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP
