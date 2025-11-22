<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
"""
API Routes for Sales OS

FastAPI router definitions for all API endpoints.
>>>>>>> origin/claude/email-integration-017ZiRSG6H1WHpye9kKe1ehW
"""

from fastapi import APIRouter

<<<<<<< HEAD
from .notifications import router as notifications_router
=======
from .email import router as email_router

>>>>>>> origin/claude/email-integration-017ZiRSG6H1WHpye9kKe1ehW

# Create main API router
api_router = APIRouter()

<<<<<<< HEAD
# Include domain routers
api_router.include_router(notifications_router)

__all__ = [
    "api_router",
    "notifications_router",
]
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
=======
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
"""API routes for Sales OS."""

from fastapi import APIRouter

<<<<<<< HEAD
from .files import router as files_router

api_router = APIRouter()
api_router.include_router(files_router, prefix="/files", tags=["files"])

__all__ = ["api_router"]
>>>>>>> origin/claude/file-upload-service-01Fp4Hpux99bpp7yFrPVgU3s
=======
"""
API routes for Sales OS.

This module exports all API routers.
"""

from .search import router as search_router

__all__ = ["search_router"]
>>>>>>> origin/claude/search-filtering-service-013Ca1SFsW8utCJ4NV94ST1R
=======
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
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
=======
# API routes
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
=======
"""API route handlers."""

from . import export, import_api

__all__ = ["export", "import_api"]
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3
=======
# Include sub-routers
api_router.include_router(email_router)


__all__ = ["api_router", "email_router"]
>>>>>>> origin/claude/email-integration-017ZiRSG6H1WHpye9kKe1ehW
