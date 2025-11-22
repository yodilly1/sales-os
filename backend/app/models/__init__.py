"""
Database models for Sales OS.

This package contains all SQLAlchemy ORM models and Pydantic schemas
for the application's data layer.
"""

from .base import Base
from .notification import (
    # Enums
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    # Database Models
    Notification,
    NotificationPreference,
    NotificationDigestQueue,
    # Pydantic Schemas
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceBase,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationPreferenceBulkUpdate,
    UnreadCountResponse,
    MarkReadRequest,
    MarkAllReadRequest,
    WebSocketNotificationEvent,
    WebSocketConnectionEvent,
    WebSocketHeartbeat,
    EmailNotificationRequest,
    EmailDigestRequest,
)

__all__ = [
    # Base
    "Base",
    # Enums
    "NotificationType",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationStatus",
    # Database Models
    "Notification",
    "NotificationPreference",
    "NotificationDigestQueue",
    # Pydantic Schemas
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationPreferenceBase",
    "NotificationPreferenceCreate",
    "NotificationPreferenceUpdate",
    "NotificationPreferenceResponse",
    "NotificationPreferenceBulkUpdate",
    "UnreadCountResponse",
    "MarkReadRequest",
    "MarkAllReadRequest",
    "WebSocketNotificationEvent",
    "WebSocketConnectionEvent",
    "WebSocketHeartbeat",
    "EmailNotificationRequest",
    "EmailDigestRequest",
]
