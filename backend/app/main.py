"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.api import enrichment
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import error_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Sales Operating System - AI-powered sales enablement platform",
    version="0.1.0",
    debug=settings.debug,
)

# Error handling middleware (must be added first to catch all errors)
app.middleware("http")(error_handler)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    exclude_paths=["/health", "/docs", "/openapi.json", "/"],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(enrichment.router, prefix="/api/enrichment", tags=["enrichment"])

logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }
