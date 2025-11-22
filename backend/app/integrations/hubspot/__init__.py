"""
HubSpot CRM Integration

This module provides a comprehensive integration with HubSpot CRM API
for managing contacts, deals, notes, tasks, and other CRM operations.
"""

from .client import HubSpotClient, RateLimiter
from .exceptions import (
    HubSpotAuthenticationError,
    HubSpotAuthorizationError,
    HubSpotConfigurationError,
    HubSpotConflictError,
    HubSpotConnectionError,
    HubSpotException,
    HubSpotNotFoundError,
    HubSpotRateLimitError,
    HubSpotServerError,
    HubSpotTokenExpiredError,
    HubSpotValidationError,
)

__all__ = [
    # Client
    "HubSpotClient",
    "RateLimiter",
    # Exceptions
    "HubSpotException",
    "HubSpotAuthenticationError",
    "HubSpotAuthorizationError",
    "HubSpotConfigurationError",
    "HubSpotConflictError",
    "HubSpotConnectionError",
    "HubSpotNotFoundError",
    "HubSpotRateLimitError",
    "HubSpotServerError",
    "HubSpotTokenExpiredError",
    "HubSpotValidationError",
]
