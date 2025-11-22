"""
API Routes for Sales OS

FastAPI router definitions for all API endpoints.
"""

from fastapi import APIRouter

from .email import router as email_router


# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(email_router)


__all__ = ["api_router", "email_router"]
