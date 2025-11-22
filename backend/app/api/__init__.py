"""
API routes for Sales OS.

This module exports all API routers.
"""

from .search import router as search_router

__all__ = ["search_router"]
