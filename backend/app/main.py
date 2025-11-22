"""Sales OS Backend API - Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.content import router as content_router
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting Sales OS API...")
    settings = get_settings()
    logger.info(f"Running in {'debug' if settings.debug else 'production'} mode")

    yield

    # Shutdown
    logger.info("Shutting down Sales OS API...")


# Create FastAPI application
app = FastAPI(
    title="Sales OS API",
    description="""
    VP-of-Sales Operating System API

    This API powers the Sales OS platform, providing:
    - **Content Generation**: AI-powered sales content creation
    - **Transcript Analysis**: SPICED methodology extraction
    - **Prospect Enrichment**: Contact and company intelligence
    - **Sales Coaching**: Performance analytics and recommendations

    All content follows the Winning by Design (WbD) SPICED methodology.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(content_router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Sales OS API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sales-os-api",
    }


@app.get("/api", tags=["api"])
async def api_info():
    """API information endpoint."""
    return {
        "version": "0.1.0",
        "endpoints": {
            "content": "/api/content",
            "transcript": "/api/transcript (coming soon)",
            "enrichment": "/api/enrichment (coming soon)",
            "coaching": "/api/coaching (coming soon)",
        },
        "documentation": "/docs",
    }
