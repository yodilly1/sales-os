"""Rate limiting middleware."""

from typing import Callable, Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.constants import DEFAULT_RATE_LIMIT, AUTH_RATE_LIMIT


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses user ID if authenticated, otherwise IP address.
    """
    # Check for authenticated user (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.user_id}"

    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use first 12 chars of API key as identifier
        return f"apikey:{api_key[:12]}"

    # Fallback to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}seconds"],
)


def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Custom rate limiting middleware with JSON error responses."""

    def __init__(
        self,
        app,
        limiter: Limiter,
        default_limit: str = DEFAULT_RATE_LIMIT,
    ):
        super().__init__(app)
        self.limiter = limiter
        self.default_limit = default_limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": e.retry_after if hasattr(e, "retry_after") else 60,
                },
                headers={
                    "Retry-After": str(e.retry_after if hasattr(e, "retry_after") else 60),
                    "X-RateLimit-Limit": self.default_limit,
                },
            )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded exceptions."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": 60,
        },
        headers={"Retry-After": "60"},
    )


# Decorator shortcuts for common limits
def limit_auth(func: Callable) -> Callable:
    """Apply auth-specific rate limit (stricter)."""
    return limiter.limit(AUTH_RATE_LIMIT)(func)


def limit_default(func: Callable) -> Callable:
    """Apply default rate limit."""
    return limiter.limit(DEFAULT_RATE_LIMIT)(func)


def limit_custom(limit_string: str) -> Callable:
    """Apply custom rate limit."""
    return limiter.limit(limit_string)
