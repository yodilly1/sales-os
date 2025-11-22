"""
API routes for Sales OS.

This package contains all REST API route definitions organized
by domain area.
"""

from fastapi import APIRouter

from .notifications import router as notifications_router

# Create main API router
api_router = APIRouter()

# Include domain routers
api_router.include_router(notifications_router)

__all__ = [
    "api_router",
    "notifications_router",
]
