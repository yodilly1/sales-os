<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""API route handlers."""
=======
"""
Sales OS API Endpoints

FastAPI routers for all Sales OS functionality.
"""

from .coaching import router as coaching_router

__all__ = [
    "coaching_router",
]
>>>>>>> origin/claude/spiced-coaching-module-01AiTWp9Wpsm2vQQXbEqCfvu
=======
"""Sales OS API Routes."""
>>>>>>> origin/claude/pdf-deck-renderer-01QnNpwQFSMU7WYfb9J8gfKi
=======
"""
API routes for Sales OS backend.
"""

from .avoma import router as avoma_router
from .webhooks import router as webhooks_router

__all__ = ["avoma_router", "webhooks_router"]
>>>>>>> origin/claude/avoma-integration-012eUdYgqKTMNxw384aFQkWN
=======
"""API routes."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
=======
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
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
"""API routes for Sales OS."""

from fastapi import APIRouter

from .files import router as files_router

api_router = APIRouter()
api_router.include_router(files_router, prefix="/files", tags=["files"])

__all__ = ["api_router"]
>>>>>>> origin/claude/file-upload-service-01Fp4Hpux99bpp7yFrPVgU3s
