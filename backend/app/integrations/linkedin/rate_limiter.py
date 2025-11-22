"""
LinkedIn Rate Limiter

Implements rate limiting for LinkedIn API calls to avoid getting blocked.
Uses a sliding window algorithm with configurable limits per endpoint.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Awaitable, Any
from functools import wraps
import logging

from .exceptions import LinkedInRateLimitError

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 20
    requests_per_hour: int = 100
    requests_per_day: int = 500
    burst_limit: int = 5  # Max requests in quick succession
    burst_window_seconds: int = 10
    cooldown_seconds: int = 60  # Wait time after hitting limit


@dataclass
class RequestWindow:
    """Track requests within a time window"""
    timestamps: list = field(default_factory=list)

    def add_request(self):
        """Record a new request"""
        self.timestamps.append(time.time())

    def count_in_window(self, window_seconds: int) -> int:
        """Count requests in the last N seconds"""
        cutoff = time.time() - window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        return len(self.timestamps)


class LinkedInRateLimiter:
    """
    Rate limiter for LinkedIn API calls.

    Implements multiple rate limit tiers:
    - Per-minute limits
    - Per-hour limits
    - Per-day limits
    - Burst protection

    Also supports:
    - Endpoint-specific limits
    - User-specific tracking
    - Graceful backoff
    """

    # Default limits based on LinkedIn's typical restrictions
    DEFAULT_CONFIG = RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=100,
        requests_per_day=500,
        burst_limit=5,
        burst_window_seconds=10,
        cooldown_seconds=60,
    )

    # Stricter limits for Sales Navigator
    SALES_NAV_CONFIG = RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=200,
        requests_per_day=1000,
        burst_limit=10,
        burst_window_seconds=10,
        cooldown_seconds=30,
    )

    # Stricter limits for profile enrichment
    ENRICHMENT_CONFIG = RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=50,
        requests_per_day=250,
        burst_limit=3,
        burst_window_seconds=10,
        cooldown_seconds=120,
    )

    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        endpoint_configs: Optional[Dict[str, RateLimitConfig]] = None,
    ):
        self.default_config = config or self.DEFAULT_CONFIG
        self.endpoint_configs = endpoint_configs or {}

        # Track requests per endpoint
        self._endpoint_windows: Dict[str, RequestWindow] = defaultdict(RequestWindow)

        # Track requests per user per endpoint
        self._user_windows: Dict[str, Dict[str, RequestWindow]] = defaultdict(
            lambda: defaultdict(RequestWindow)
        )

        # Track cooldowns
        self._cooldowns: Dict[str, float] = {}

        # Global lock for thread safety
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = {
            "total_requests": 0,
            "rate_limited": 0,
            "cooldown_triggered": 0,
        }

    def get_config(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit config for an endpoint"""
        return self.endpoint_configs.get(endpoint, self.default_config)

    async def acquire(
        self,
        endpoint: str = "default",
        user_id: Optional[str] = None,
        wait: bool = True,
    ) -> bool:
        """
        Acquire permission to make a request.

        Args:
            endpoint: API endpoint being called
            user_id: Optional user ID for per-user limiting
            wait: If True, wait until allowed; if False, raise immediately

        Returns:
            True if request is allowed

        Raises:
            LinkedInRateLimitError if rate limited and wait=False
        """
        async with self._lock:
            config = self.get_config(endpoint)
            window = self._endpoint_windows[endpoint]

            # Check if in cooldown
            cooldown_key = f"{endpoint}:{user_id or 'global'}"
            if cooldown_key in self._cooldowns:
                remaining = self._cooldowns[cooldown_key] - time.time()
                if remaining > 0:
                    if wait:
                        logger.warning(
                            f"Rate limit cooldown for {endpoint}, waiting {remaining:.1f}s"
                        )
                        await asyncio.sleep(remaining)
                        del self._cooldowns[cooldown_key]
                    else:
                        raise LinkedInRateLimitError(
                            f"Rate limit cooldown active for {endpoint}",
                            retry_after=int(remaining),
                        )

            # Check burst limit
            burst_count = window.count_in_window(config.burst_window_seconds)
            if burst_count >= config.burst_limit:
                wait_time = config.burst_window_seconds - (
                    time.time() - min(window.timestamps[-config.burst_limit:])
                )
                if wait:
                    logger.debug(f"Burst limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise LinkedInRateLimitError(
                        "Burst limit exceeded",
                        retry_after=int(wait_time),
                    )

            # Check per-minute limit
            minute_count = window.count_in_window(60)
            if minute_count >= config.requests_per_minute:
                self._stats["rate_limited"] += 1
                wait_time = 60 - (time.time() - window.timestamps[-config.requests_per_minute])
                if wait:
                    logger.info(f"Per-minute limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise LinkedInRateLimitError(
                        "Per-minute rate limit exceeded",
                        retry_after=int(wait_time),
                    )

            # Check per-hour limit
            hour_count = window.count_in_window(3600)
            if hour_count >= config.requests_per_hour:
                self._stats["rate_limited"] += 1
                self._trigger_cooldown(cooldown_key, config.cooldown_seconds * 2)
                if wait:
                    logger.warning(
                        f"Per-hour limit reached, cooldown {config.cooldown_seconds * 2}s"
                    )
                    await asyncio.sleep(config.cooldown_seconds * 2)
                else:
                    raise LinkedInRateLimitError(
                        "Per-hour rate limit exceeded",
                        retry_after=config.cooldown_seconds * 2,
                    )

            # Check per-day limit
            day_count = window.count_in_window(86400)
            if day_count >= config.requests_per_day:
                self._stats["rate_limited"] += 1
                # Calculate time until midnight (or 24 hours from first request)
                cooldown = min(config.cooldown_seconds * 10, 3600)  # Max 1 hour cooldown
                self._trigger_cooldown(cooldown_key, cooldown)
                if wait:
                    logger.warning(f"Per-day limit reached, cooldown {cooldown}s")
                    await asyncio.sleep(cooldown)
                else:
                    raise LinkedInRateLimitError(
                        "Per-day rate limit exceeded",
                        retry_after=cooldown,
                    )

            # All checks passed, record the request
            window.add_request()
            self._stats["total_requests"] += 1

            # Also track per-user if provided
            if user_id:
                self._user_windows[user_id][endpoint].add_request()

            return True

    def _trigger_cooldown(self, key: str, duration: float):
        """Trigger a cooldown period"""
        self._cooldowns[key] = time.time() + duration
        self._stats["cooldown_triggered"] += 1

    async def wait_if_needed(
        self,
        endpoint: str = "default",
        user_id: Optional[str] = None,
    ):
        """Wait if rate limited, otherwise return immediately"""
        await self.acquire(endpoint, user_id, wait=True)

    def check(
        self,
        endpoint: str = "default",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check current rate limit status without making a request.

        Returns dict with:
            - allowed: bool
            - remaining_minute: int
            - remaining_hour: int
            - remaining_day: int
            - retry_after: Optional[int]
        """
        config = self.get_config(endpoint)
        window = self._endpoint_windows[endpoint]

        minute_count = window.count_in_window(60)
        hour_count = window.count_in_window(3600)
        day_count = window.count_in_window(86400)

        # Check cooldown
        cooldown_key = f"{endpoint}:{user_id or 'global'}"
        in_cooldown = cooldown_key in self._cooldowns and self._cooldowns[cooldown_key] > time.time()
        retry_after = None
        if in_cooldown:
            retry_after = int(self._cooldowns[cooldown_key] - time.time())

        allowed = (
            minute_count < config.requests_per_minute
            and hour_count < config.requests_per_hour
            and day_count < config.requests_per_day
            and not in_cooldown
        )

        return {
            "allowed": allowed,
            "remaining_minute": max(0, config.requests_per_minute - minute_count),
            "remaining_hour": max(0, config.requests_per_hour - hour_count),
            "remaining_day": max(0, config.requests_per_day - day_count),
            "retry_after": retry_after,
            "in_cooldown": in_cooldown,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            **self._stats,
            "active_cooldowns": len([
                k for k, v in self._cooldowns.items() if v > time.time()
            ]),
        }

    def reset(self, endpoint: Optional[str] = None):
        """Reset rate limit tracking"""
        if endpoint:
            self._endpoint_windows[endpoint] = RequestWindow()
            keys_to_remove = [k for k in self._cooldowns if k.startswith(endpoint)]
            for key in keys_to_remove:
                del self._cooldowns[key]
        else:
            self._endpoint_windows.clear()
            self._user_windows.clear()
            self._cooldowns.clear()


def rate_limited(
    endpoint: str = "default",
    limiter: Optional[LinkedInRateLimiter] = None,
):
    """
    Decorator to apply rate limiting to async functions.

    Usage:
        @rate_limited("profile_enrichment")
        async def enrich_profile(url: str):
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _limiter = limiter or LinkedInRateLimiter()
            await _limiter.acquire(endpoint, wait=True)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Create global rate limiter instance
_global_limiter: Optional[LinkedInRateLimiter] = None


def get_rate_limiter() -> LinkedInRateLimiter:
    """Get or create global rate limiter instance"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = LinkedInRateLimiter(
            endpoint_configs={
                "profile_enrichment": LinkedInRateLimiter.ENRICHMENT_CONFIG,
                "company_enrichment": LinkedInRateLimiter.ENRICHMENT_CONFIG,
                "sales_navigator": LinkedInRateLimiter.SALES_NAV_CONFIG,
            }
        )
    return _global_limiter
