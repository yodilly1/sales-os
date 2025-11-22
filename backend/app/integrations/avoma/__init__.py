<<<<<<< HEAD
"""Avoma integration (to be implemented by AGENT-009)."""
=======
"""
Avoma integration for automatic transcript ingestion.

This module provides:
- AvomaClient: API client for interacting with Avoma
- AvomaAuthManager: Token refresh and authentication handling
- Webhook handlers for new recording notifications
"""

from .client import AvomaClient
from .auth import AvomaAuthManager
from .webhooks import AvomaWebhookHandler

__all__ = ["AvomaClient", "AvomaAuthManager", "AvomaWebhookHandler"]
>>>>>>> origin/claude/avoma-integration-012eUdYgqKTMNxw384aFQkWN
