"""API routes for Sales OS."""

from fastapi import APIRouter

from app.api import activity

api_router = APIRouter()

# Include activity routes
api_router.include_router(
    activity.router,
    prefix="/activities",
    tags=["activities"],
)

__all__ = [
    "api_router",
]
