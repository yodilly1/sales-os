"""
Notification models for Sales OS.

This module defines the database models and Pydantic schemas for the notification system,
including notification storage, preferences, and event types.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


# =============================================================================
# Enums
# =============================================================================


class NotificationType(str, Enum):
    """Types of notifications that can be sent."""

    TRANSCRIPT_PROCESSED = "transcript_processed"
    CONTENT_GENERATED = "content_generated"
    ENRICHMENT_COMPLETE = "enrichment_complete"
    COACHING_FEEDBACK_READY = "coaching_feedback_ready"
    INTEGRATION_SYNC_STATUS = "integration_sync_status"
    SYSTEM_ALERT = "system_alert"
    TEAM_UPDATE = "team_update"


class NotificationChannel(str, Enum):
    """Channels through which notifications can be delivered."""

    IN_APP = "in_app"
    EMAIL_INSTANT = "email_instant"
    EMAIL_DIGEST = "email_digest"
    WEBSOCKET = "websocket"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Status of a notification."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ARCHIVED = "archived"
    FAILED = "failed"


# =============================================================================
# SQLAlchemy Database Models
# =============================================================================


class Notification(Base):
    """
    Database model for storing notifications.

    Represents a single notification sent to a user, including its content,
    delivery status, and read state.
    """

    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Notification content
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(
        SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL
    )

    # Related entity (for deep linking)
    entity_type = Column(String(50), nullable=True)  # e.g., "transcript", "content", "prospect"
    entity_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Additional metadata
    metadata = Column(JSON, nullable=True, default=dict)

    # Delivery tracking
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    channel = Column(SQLEnum(NotificationChannel), nullable=False, default=NotificationChannel.IN_APP)

    # Read tracking
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Deduplication
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_type_status", "type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"


class NotificationPreference(Base):
    """
    Database model for user notification preferences.

    Stores user preferences for each notification type and channel combination,
    allowing fine-grained control over how users receive notifications.
    """

    __tablename__ = "notification_preferences"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Preference settings
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)

    # Email digest settings (only applicable for EMAIL_DIGEST channel)
    digest_frequency = Column(String(20), nullable=True)  # "daily", "weekly", "monthly"
    digest_time = Column(String(5), nullable=True)  # HH:MM format, e.g., "09:00"
    digest_timezone = Column(String(50), nullable=True)  # e.g., "America/New_York"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    # Unique constraint for user + type + channel combination
    __table_args__ = (
        Index(
            "ix_notification_preferences_unique",
            "user_id",
            "notification_type",
            "channel",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationPreference(user_id={self.user_id}, "
            f"type={self.notification_type}, channel={self.channel}, enabled={self.enabled})>"
        )


class NotificationDigestQueue(Base):
    """
    Queue for email digest notifications.

    Stores notifications that should be included in the next digest email
    for a user, grouped by digest frequency.
    """

    __tablename__ = "notification_digest_queue"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    notification_id = Column(
        PGUUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False, index=True
    )
    digest_frequency = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    sent = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User")
    notification = relationship("Notification")

    __table_args__ = (Index("ix_digest_queue_pending", "scheduled_for", "sent"),)


# =============================================================================
# Pydantic Schemas for API
# =============================================================================


class NotificationBase(BaseModel):
    """Base schema for notification data."""

    type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.NORMAL
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""

    user_id: UUID
    organization_id: UUID
    channel: NotificationChannel = NotificationChannel.IN_APP
    idempotency_key: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Schema for notification API responses."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    status: NotificationStatus
    channel: NotificationChannel
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list response."""

    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preference data."""

    notification_type: NotificationType
    channel: NotificationChannel
    enabled: bool = True
    digest_frequency: Optional[str] = None
    digest_time: Optional[str] = None
    digest_timezone: Optional[str] = None


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating a notification preference."""

    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating a notification preference."""

    enabled: Optional[bool] = None
    digest_frequency: Optional[str] = None
    digest_time: Optional[str] = None
    digest_timezone: Optional[str] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference API responses."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceBulkUpdate(BaseModel):
    """Schema for bulk updating notification preferences."""

    preferences: List[NotificationPreferenceCreate]


class UnreadCountResponse(BaseModel):
    """Schema for unread notification count response."""

    count: int
    by_type: Dict[str, int]


class MarkReadRequest(BaseModel):
    """Schema for marking notifications as read."""

    notification_ids: List[UUID]


class MarkAllReadRequest(BaseModel):
    """Schema for marking all notifications as read."""

    before_date: Optional[datetime] = None
    notification_type: Optional[NotificationType] = None


# =============================================================================
# WebSocket Event Schemas
# =============================================================================


class WebSocketNotificationEvent(BaseModel):
    """Schema for WebSocket notification events."""

    event_type: str = "notification"
    notification: NotificationResponse


class WebSocketConnectionEvent(BaseModel):
    """Schema for WebSocket connection events."""

    event_type: str = "connection"
    status: str  # "connected", "disconnected"
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketHeartbeat(BaseModel):
    """Schema for WebSocket heartbeat messages."""

    event_type: str = "heartbeat"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Email Notification Schemas
# =============================================================================


class EmailNotificationRequest(BaseModel):
    """Schema for email notification request."""

    recipient_email: str
    recipient_name: str
    subject: str
    notification: NotificationResponse
    template_name: str = "notification"


class EmailDigestRequest(BaseModel):
    """Schema for email digest request."""

    recipient_email: str
    recipient_name: str
    notifications: List[NotificationResponse]
    digest_period: str  # "daily", "weekly", "monthly"
    period_start: datetime
    period_end: datetime
