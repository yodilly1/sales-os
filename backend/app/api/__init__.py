"""API routes for Sales OS."""

from fastapi import APIRouter

from .files import router as files_router

api_router = APIRouter()
api_router.include_router(files_router, prefix="/files", tags=["files"])

__all__ = ["api_router"]
