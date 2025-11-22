"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import export, import_api

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Sales OS - AI-powered sales enablement platform",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://sales-os.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# API routes
app.include_router(
    export.router,
    prefix=f"/api/{settings.api_version}/export",
    tags=["export"],
)

app.include_router(
    import_api.router,
    prefix=f"/api/{settings.api_version}/import",
    tags=["import"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs" if settings.debug else None,
    }
