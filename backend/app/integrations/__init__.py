"""External service integrations."""

# Import integrations if they exist, otherwise ignore
try:
    from . import email
except ImportError:
    email = None

try:
    from .linkedin import (
        LinkedInClient,
        LinkedInService,
        LinkedInRateLimiter,
        LinkedInURLParser,
        LinkedInError,
        LinkedInAuthError,
        LinkedInRateLimitError,
        LinkedInNotFoundError,
        LinkedInAPIError,
    )
except ImportError:
    LinkedInClient = None

try:
    from app.integrations.zoom import ZoomClient
except ImportError:
    ZoomClient = None

__all__ = []

if email:
    __all__.append("email")

if LinkedInClient:
    __all__.extend([
        "LinkedInClient",
        "LinkedInService",
        "LinkedInRateLimiter",
        "LinkedInURLParser",
        "LinkedInError",
        "LinkedInAuthError",
        "LinkedInRateLimitError",
        "LinkedInNotFoundError",
        "LinkedInAPIError",
    ])

if ZoomClient:
    __all__.append("ZoomClient")
