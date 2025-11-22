<<<<<<< HEAD
"""Rate limiting middleware for API endpoints."""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per client
            requests_per_hour: Max requests per hour per client
            burst_limit: Max requests in quick succession
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit

        # Store request timestamps per client
        self._minute_requests: dict[str, list[float]] = defaultdict(list)
        self._hour_requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, client_id: str, now: float) -> None:
        """Remove expired request timestamps."""
        # Clean minute window
        minute_ago = now - 60
        self._minute_requests[client_id] = [
            ts for ts in self._minute_requests[client_id] if ts > minute_ago
        ]

        # Clean hour window
        hour_ago = now - 3600
        self._hour_requests[client_id] = [
            ts for ts in self._hour_requests[client_id] if ts > hour_ago
        ]

    def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique client identifier (IP, API key, etc.)

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()
        self._clean_old_requests(client_id, now)

        minute_count = len(self._minute_requests[client_id])
        hour_count = len(self._hour_requests[client_id])

        info = {
            "limit_minute": self.requests_per_minute,
            "remaining_minute": max(0, self.requests_per_minute - minute_count),
            "limit_hour": self.requests_per_hour,
            "remaining_hour": max(0, self.requests_per_hour - hour_count),
            "reset_minute": int(60 - (now % 60)),
            "reset_hour": int(3600 - (now % 3600)),
        }

        # Check limits
        if minute_count >= self.requests_per_minute:
            info["retry_after"] = info["reset_minute"]
            return False, info

        if hour_count >= self.requests_per_hour:
            info["retry_after"] = info["reset_hour"]
            return False, info

        # Record request
        self._minute_requests[client_id].append(now)
        self._hour_requests[client_id].append(now)

        return True, info

    def get_client_stats(self, client_id: str) -> dict:
        """Get rate limit statistics for a client."""
        now = time.time()
        self._clean_old_requests(client_id, now)

        return {
            "minute_requests": len(self._minute_requests[client_id]),
            "hour_requests": len(self._hour_requests[client_id]),
            "limit_minute": self.requests_per_minute,
            "limit_hour": self.requests_per_hour,
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_minute * 20,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints."""
=======
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
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef

    def __init__(
        self,
        app,
<<<<<<< HEAD
        limiter: Optional[RateLimiter] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            limiter: Rate limiter instance
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = limiter or rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        allowed, info = self.limiter.is_allowed(client_id)

        if not allowed:
            logger.warning(f"Rate limit exceeded for client {client_id}")
=======
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
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
<<<<<<< HEAD
                    "retry_after": info.get("retry_after", 60),
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info["limit_minute"]),
                    "X-RateLimit-Remaining": str(info["remaining_minute"]),
                    "X-RateLimit-Reset": str(info["reset_minute"]),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit_minute"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining_minute"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_minute"])

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"


def rate_limit_dependency(
    requests_per_minute: int = 60,
) -> Callable:
    """
    Create a rate limit dependency for specific endpoints.

    Usage:
        @router.get("/expensive", dependencies=[Depends(rate_limit_dependency(10))])
        async def expensive_endpoint():
            pass
    """
    limiter = RateLimiter(requests_per_minute=requests_per_minute)

    async def check_rate_limit(request: Request):
        client_id = request.headers.get("X-API-Key") or request.client.host
        allowed, info = limiter.is_allowed(client_id)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(info.get("retry_after", 60))},
            )

    return check_rate_limit
=======
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
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
