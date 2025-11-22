"""Sales OS Backend Application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import render
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: ensure required directories exist
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    (settings.output_dir / "decks").mkdir(parents=True, exist_ok=True)
    settings.templates_dir.mkdir(parents=True, exist_ok=True)
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    (settings.assets_dir / "logos").mkdir(parents=True, exist_ok=True)
    (settings.assets_dir / "fonts").mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Sales OS - VP-of-Sales Operating System

    A comprehensive platform for sales teams featuring:
    - SPICED methodology transcript analysis
    - Content generation (proposals, decks)
    - Prospect enrichment
    - CRM integration
    - Professional PDF and deck rendering
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for downloads
if settings.output_dir.exists():
    app.mount(
        "/downloads",
        StaticFiles(directory=str(settings.output_dir)),
        name="downloads",
    )

# Include API routers
app.include_router(render.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Global health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }
