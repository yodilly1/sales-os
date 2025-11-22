"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, zoom, webhooks

app = FastAPI(
    title=settings.app_name,
    description="VP-of-Sales Operating System - AI-powered sales automation",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(zoom.router, prefix="/api/zoom", tags=["zoom"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass
