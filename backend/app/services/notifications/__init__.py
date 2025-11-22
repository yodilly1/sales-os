"""
Notification services for Sales OS.

This package provides notification management, delivery, and
scheduling functionality for the application.
"""

from .notification_service import NotificationService
from .email_service import EmailNotificationService, EmailConfig, DigestScheduler

__all__ = [
    "NotificationService",
    "EmailNotificationService",
    "EmailConfig",
    "DigestScheduler",
]
