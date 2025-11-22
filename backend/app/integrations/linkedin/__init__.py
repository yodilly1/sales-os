"""
LinkedIn Integration Module

This module provides LinkedIn integration for Sales OS including:
- Profile data enrichment
- Company page data extraction
- Connection status tracking
- Activity monitoring (posts, engagement)
- Outreach tracking (InMail, connection requests)
- Sales Navigator integration support
"""

from .client import LinkedInClient
from .service import LinkedInService
from .rate_limiter import LinkedInRateLimiter
from .parser import LinkedInURLParser
from .exceptions import (
    LinkedInError,
    LinkedInAuthError,
    LinkedInRateLimitError,
    LinkedInNotFoundError,
    LinkedInAPIError,
)

__all__ = [
    "LinkedInClient",
    "LinkedInService",
    "LinkedInRateLimiter",
    "LinkedInURLParser",
    "LinkedInError",
    "LinkedInAuthError",
    "LinkedInRateLimitError",
    "LinkedInNotFoundError",
    "LinkedInAPIError",
]
