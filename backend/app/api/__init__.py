"""
Sales OS API Routes

This module contains all FastAPI route handlers.
"""

from .linkedin import router as linkedin_router

__all__ = [
    "linkedin_router",
]
