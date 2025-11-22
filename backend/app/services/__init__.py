"""
Business logic services for Sales OS.

This package contains all service classes that implement the core
business logic of the application.
"""

from .notifications import (
    NotificationService,
    EmailNotificationService,
    EmailConfig,
    DigestScheduler,
)

__all__ = [
    # Notification services
    "NotificationService",
    "EmailNotificationService",
    "EmailConfig",
    "DigestScheduler",
]
