<<<<<<< HEAD
"""HubSpot CRM integration module.

This module provides integration with HubSpot CRM for managing contacts,
companies, deals, and notes.

Note: This is a stub implementation. The full HubSpot integration will be
implemented by AGENT-004.
"""

from .client import HubSpotClient

__all__ = ["HubSpotClient"]
=======
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
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
