<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""External service integrations."""
=======
"""
External service integrations for Sales OS.
"""

from .avoma import AvomaClient, AvomaAuthManager

__all__ = ["AvomaClient", "AvomaAuthManager"]
>>>>>>> origin/claude/avoma-integration-012eUdYgqKTMNxw384aFQkWN
=======
"""External service integrations for Sales OS."""
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
=======
"""
External Service Integrations for Sales OS

Provides connectors for:
- Email (SendGrid, SES)
- HubSpot CRM
- Avoma
"""

from . import email

__all__ = ["email"]
>>>>>>> origin/claude/email-integration-017ZiRSG6H1WHpye9kKe1ehW
=======
"""
Sales OS Integrations

This module contains integrations with external services.
"""

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

__all__ = [
    # LinkedIn Integration
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
>>>>>>> origin/claude/linkedin-integration-01VmE4MUdZtsYVbAeCay7X3m
=======
"""Sales OS integrations with external services."""
>>>>>>> origin/claude/slack-integration-01FAipAuMUsRJRL7psy92hdb
=======
"""
External service integrations for Sales OS.
"""
>>>>>>> origin/claude/salesforce-integration-01Jk6WSRuSJXErwMJ2igKMJQ
=======
"""External service integrations."""

from app.integrations.zoom import ZoomClient

__all__ = ["ZoomClient"]
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP
=======
"""
Sales OS Integrations Package

This package contains integrations with external services
for conversation intelligence and CRM data.
"""
>>>>>>> origin/claude/gong-integration-01Mysb6zKfXmpQEHrWqe4iA8
