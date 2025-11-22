"""Sales OS Backend Application - FastAPI entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.db.session import init_db
from app.middleware.activity_logger import ActivityLoggerMiddleware, RequestContextMiddleware
from app.models.activity import ActivityCategory, ActivitySeverity
from app.services.activity import ActivityService
from app.db.session import async_session_maker

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Sales OS Backend...")
    logger.info("Environment: %s", settings.FASTAPI_ENV)
    logger.info("Debug mode: %s", settings.DEBUG)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Log system startup event
    if settings.ACTIVITY_LOG_ENABLED:
        try:
            async with async_session_maker() as session:
                activity_service = ActivityService(session)
                await activity_service.log_activity(
                    category=ActivityCategory.SYSTEM_STARTUP,
                    action="Sales OS Backend started",
                    severity=ActivitySeverity.INFO,
                    details={
                        "environment": settings.FASTAPI_ENV,
                        "debug": settings.DEBUG,
                    },
                )
                await session.commit()
        except Exception as e:
            logger.warning("Failed to log startup event: %s", e)

    logger.info("Sales OS Backend started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Sales OS Backend...")

    # Log system shutdown event
    if settings.ACTIVITY_LOG_ENABLED:
        try:
            async with async_session_maker() as session:
                activity_service = ActivityService(session)
                await activity_service.log_activity(
                    category=ActivityCategory.SYSTEM_SHUTDOWN,
                    action="Sales OS Backend shutting down",
                    severity=ActivitySeverity.INFO,
                )
                await session.commit()
        except Exception as e:
            logger.warning("Failed to log shutdown event: %s", e)

    logger.info("Sales OS Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Sales OS - AI-powered sales enablement platform",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request context middleware (must be added before activity logger)
app.add_middleware(RequestContextMiddleware)

# Add activity logging middleware
app.add_middleware(
    ActivityLoggerMiddleware,
    excluded_paths=[
        "/health",
        "/healthz",
        "/ready",
        "/readyz",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "sales-os-backend"}


@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for load balancers."""
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level="debug" if settings.DEBUG else "info",
    )
