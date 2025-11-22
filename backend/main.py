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

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.websockets import websocket_manager
from app.websockets.handlers import router as websocket_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Stop WebSocket manager
    await websocket_manager.stop()
    logger.info("WebSocket manager stopped")

    # TODO: Close database connections
    # TODO: Cancel background tasks


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
    )
