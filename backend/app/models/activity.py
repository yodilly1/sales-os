"""Activity logging models and schemas for audit trail and activity tracking."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ActivityCategory(str, Enum):
    """Categories of activities that can be logged."""

    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_SETTINGS_CHANGE = "user.settings_change"
    USER_PASSWORD_CHANGE = "user.password_change"
    USER_PROFILE_UPDATE = "user.profile_update"

    # Transcript processing
    TRANSCRIPT_UPLOAD = "transcript.upload"
    TRANSCRIPT_PROCESS = "transcript.process"
    TRANSCRIPT_SPICED_ANALYSIS = "transcript.spiced_analysis"
    TRANSCRIPT_DELETE = "transcript.delete"

    # Content generation
    CONTENT_GENERATE = "content.generate"
    CONTENT_DECK_CREATE = "content.deck_create"
    CONTENT_PROPOSAL_CREATE = "content.proposal_create"
    CONTENT_ONEPAGER_CREATE = "content.onepager_create"
    CONTENT_BATTLECARD_CREATE = "content.battlecard_create"
    CONTENT_EXPORT = "content.export"
    CONTENT_DELETE = "content.delete"

    # CRM sync operations
    CRM_SYNC_START = "crm.sync_start"
    CRM_SYNC_COMPLETE = "crm.sync_complete"
    CRM_SYNC_FAILED = "crm.sync_failed"
    CRM_CONTACT_CREATE = "crm.contact_create"
    CRM_CONTACT_UPDATE = "crm.contact_update"
    CRM_DEAL_CREATE = "crm.deal_create"
    CRM_DEAL_UPDATE = "crm.deal_update"

    # Integration events
    INTEGRATION_CONNECT = "integration.connect"
    INTEGRATION_DISCONNECT = "integration.disconnect"
    INTEGRATION_WEBHOOK_RECEIVED = "integration.webhook_received"
    INTEGRATION_AVOMA_SYNC = "integration.avoma_sync"
    INTEGRATION_HUBSPOT_SYNC = "integration.hubspot_sync"

    # Coaching events
    COACHING_REPORT_GENERATE = "coaching.report_generate"
    COACHING_SCORE_UPDATE = "coaching.score_update"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_MAINTENANCE = "system.maintenance"

    # API events
    API_REQUEST = "api.request"
    API_ERROR = "api.error"
    API_RATE_LIMITED = "api.rate_limited"


class ActivitySeverity(str, Enum):
    """Severity levels for activity logs."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActivityLog(Base, TimestampMixin):
    """SQLAlchemy model for activity logs."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Actor information
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Action information
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ActivitySeverity.INFO.value
    )

    # Resource information
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Response information
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional details
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp for the actual event (may differ from created_at)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_activity_logs_user_category", "user_id", "category"),
        Index("ix_activity_logs_org_category", "organization_id", "category"),
        Index("ix_activity_logs_occurred_at_category", "occurred_at", "category"),
        Index("ix_activity_logs_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, category={self.category}, action={self.action})>"


# Pydantic Schemas


class ActivityLogBase(BaseModel):
    """Base schema for activity logs."""

    category: ActivityCategory
    action: str
    severity: ActivitySeverity = ActivitySeverity.INFO
    resource_type: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    error_message: str | None = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for creating activity logs."""

    user_id: int | None = None
    user_email: str | None = None
    organization_id: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    status_code: int | None = None
    response_time_ms: int | None = None
    occurred_at: datetime | None = None


class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_email: str | None
    organization_id: int | None
    ip_address: str | None
    request_id: str | None
    request_method: str | None
    request_path: str | None
    status_code: int | None
    response_time_ms: int | None
    occurred_at: datetime
    created_at: datetime


class ActivityLogQuery(BaseModel):
    """Schema for querying activity logs."""

    user_id: int | None = None
    organization_id: int | None = None
    category: ActivityCategory | None = None
    categories: list[ActivityCategory] | None = None
    severity: ActivitySeverity | None = None
    severities: list[ActivitySeverity] | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    request_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    search: str | None = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ActivityFeedResponse(PaginatedResponse):
    """Paginated activity feed response."""

    items: list[ActivityLogResponse]


class AuditTrailEntry(BaseModel):
    """Schema for audit trail entries (compliance-focused view)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    user_id: int | None
    user_email: str | None
    category: str
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    status_code: int | None
    details: dict[str, Any] | None


class AuditTrailResponse(PaginatedResponse):
    """Paginated audit trail response."""

    items: list[AuditTrailEntry]


class ActivityStats(BaseModel):
    """Activity statistics summary."""

    total_activities: int
    activities_by_category: dict[str, int]
    activities_by_severity: dict[str, int]
    activities_by_day: dict[str, int]
    top_users: list[dict[str, Any]]
    error_rate: float
