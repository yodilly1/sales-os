<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""Middleware components for the Sales OS backend."""

from .rate_limit import RateLimitMiddleware, rate_limiter
from .error_handler import error_handler, EnrichmentError, ValidationError, ProviderError

__all__ = [
    "RateLimitMiddleware",
    "rate_limiter",
    "error_handler",
    "EnrichmentError",
    "ValidationError",
    "ProviderError",
=======
"""Middleware modules."""

from app.middleware.auth import (
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_permissions,
    require_roles,
)
from app.middleware.rate_limit import RateLimitMiddleware, get_rate_limiter
from app.middleware.audit import AuditMiddleware

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_permissions",
    "require_roles",
    "RateLimitMiddleware",
    "get_rate_limiter",
    "AuditMiddleware",
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
=======
"""Middleware components for Sales OS."""

from app.middleware.activity_logger import ActivityLoggerMiddleware

__all__ = [
    "ActivityLoggerMiddleware",
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
]
=======
# Middleware module
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
=======
"""Custom middleware for the application."""
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP
