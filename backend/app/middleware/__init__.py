"""Middleware components for the Sales OS backend."""

from .rate_limit import RateLimitMiddleware, rate_limiter
from .error_handler import error_handler, EnrichmentError, ValidationError, ProviderError

# Try to import ActivityLoggerMiddleware if it exists
try:
    from app.middleware.activity_logger import ActivityLoggerMiddleware
except ImportError:
    ActivityLoggerMiddleware = None

__all__ = [
    "RateLimitMiddleware",
    "rate_limiter",
    "error_handler",
    "EnrichmentError",
    "ValidationError",
    "ProviderError",
]

if ActivityLoggerMiddleware:
    __all__.append("ActivityLoggerMiddleware")
