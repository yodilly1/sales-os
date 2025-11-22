<<<<<<< HEAD
<<<<<<< HEAD
"""Entry point for running the application."""
import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
=======
"""
Sales OS Backend Application Entry Point.

This module creates and configures the FastAPI application instance
with all routes, middleware, and startup/shutdown handlers.
"""
=======
"""Sales OS Backend Application - FastAPI entry point."""
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
<<<<<<< HEAD
from app.core.config import settings
from app.websockets import websocket_manager
from app.websockets.handlers import router as websocket_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
=======
from app.core.config import get_settings
from app.db.session import init_db
from app.middleware.activity_logger import ActivityLoggerMiddleware, RequestContextMiddleware
from app.models.activity import ActivityCategory, ActivitySeverity
from app.services.activity import ActivityService
from app.db.session import async_session_maker

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().DEBUG else logging.INFO,
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

<<<<<<< HEAD

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.

    Handles:
    - WebSocket manager initialization
    - Database connection pool setup
    - Background task initialization
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Start WebSocket manager
    await websocket_manager.start()
    logger.info("WebSocket manager started")

    # TODO: Initialize database connection pool
    # TODO: Start background tasks (e.g., digest scheduler)
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

    yield

    # Shutdown
<<<<<<< HEAD
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Stop WebSocket manager
    await websocket_manager.stop()
    logger.info("WebSocket manager stopped")

    # TODO: Close database connections
    # TODO: Cancel background tasks
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
<<<<<<< HEAD
    version=settings.APP_VERSION,
    description="Sales OS - AI-powered sales operations platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include WebSocket routes
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint returning application info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK


@app.get("/health")
async def health_check():
<<<<<<< HEAD
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
<<<<<<< HEAD
        reload=settings.DEBUG,
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
        reload=settings.is_development,
        log_level="debug" if settings.DEBUG else "info",
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    )
