"""
Sales OS API Endpoints

FastAPI routers for all Sales OS functionality.
"""

from .coaching import router as coaching_router

__all__ = [
    "coaching_router",
]
