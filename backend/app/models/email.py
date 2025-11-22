"""
Email Models for Sales OS

This module defines Pydantic models and SQLAlchemy entities for email
functionality including messages, templates, tracking events, and unsubscribes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr


# Enums
class EmailStatus(str, Enum):
    """Status of an email message."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"


class EmailProvider(str, Enum):
    """Supported email service providers."""
    SENDGRID = "sendgrid"
    SES = "ses"


class EmailEventType(str, Enum):
    """Types of email tracking events."""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    DROPPED = "dropped"
    SPAM_REPORT = "spam_report"
    UNSUBSCRIBED = "unsubscribed"
    DEFERRED = "deferred"


class BounceType(str, Enum):
    """Types of email bounces."""
    HARD = "hard"  # Permanent failure (invalid address)
    SOFT = "soft"  # Temporary failure (mailbox full, etc.)
    BLOCK = "block"  # Blocked by recipient server


class EmailTemplateType(str, Enum):
    """Types of email templates."""
    FOLLOW_UP = "follow_up"
    PROPOSAL = "proposal"
    INTRO = "intro"
    CONTENT_DELIVERY = "content_delivery"
    OUTREACH = "outreach"
    MEETING_RECAP = "meeting_recap"
    CUSTOM = "custom"


# Base Models
class EmailRecipient(BaseModel):
    """Email recipient details."""
    email: EmailStr
    name: Optional[str] = None
    recipient_type: str = "to"  # to, cc, bcc


class EmailAttachment(BaseModel):
    """Email attachment details."""
    filename: str
    content_type: str
    content_base64: Optional[str] = None
    file_path: Optional[str] = None
    size_bytes: Optional[int] = None


class TrackingPixel(BaseModel):
    """Tracking pixel configuration."""
    enabled: bool = True
    pixel_id: str = Field(default_factory=lambda: str(uuid4()))


class LinkTracking(BaseModel):
    """Link tracking configuration."""
    enabled: bool = True
    original_url: str
    tracked_url: str
    link_id: str = Field(default_factory=lambda: str(uuid4()))


# Email Message Models
class EmailMessageBase(BaseModel):
    """Base email message model."""
    subject: str = Field(..., min_length=1, max_length=998)
    from_email: EmailStr
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None

    # Content
    html_content: Optional[str] = None
    text_content: Optional[str] = None

    # Recipients
    to_recipients: List[EmailRecipient]
    cc_recipients: Optional[List[EmailRecipient]] = None
    bcc_recipients: Optional[List[EmailRecipient]] = None

    # Attachments
    attachments: Optional[List[EmailAttachment]] = None

    # Template
    template_id: Optional[UUID] = None
    template_variables: Optional[Dict[str, Any]] = None

    # Tracking
    track_opens: bool = True
    track_clicks: bool = True

    # Metadata
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EmailMessageCreate(EmailMessageBase):
    """Model for creating a new email message."""
    send_at: Optional[datetime] = None  # For scheduled sending
    campaign_id: Optional[UUID] = None
    sequence_id: Optional[UUID] = None
    sequence_step: Optional[int] = None


class EmailMessage(EmailMessageBase):
    """Complete email message model with tracking."""
    id: UUID = Field(default_factory=uuid4)
    status: EmailStatus = EmailStatus.PENDING

    # Provider info
    provider: Optional[EmailProvider] = None
    provider_message_id: Optional[str] = None

    # Tracking
    tracking_id: str = Field(default_factory=lambda: str(uuid4()))
    open_count: int = 0
    click_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None

    # Related IDs
    campaign_id: Optional[UUID] = None
    sequence_id: Optional[UUID] = None
    sequence_step: Optional[int] = None
    prospect_id: Optional[UUID] = None
    contact_id: Optional[str] = None  # HubSpot contact ID

    class Config:
        from_attributes = True


# Email Template Models
class TemplateVariable(BaseModel):
    """Template variable definition."""
    name: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False


class EmailTemplateBase(BaseModel):
    """Base email template model."""
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=998)
    template_type: EmailTemplateType

    # Content
    html_content: str
    text_content: Optional[str] = None

    # Variables
    variables: Optional[List[TemplateVariable]] = None

    # Metadata
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """Model for creating a new email template."""
    pass


class EmailTemplate(EmailTemplateBase):
    """Complete email template model."""
    id: UUID = Field(default_factory=uuid4)
    version: int = 1

    # Statistics
    send_count: int = 0
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


# Email Event Models (for tracking)
class EmailEventBase(BaseModel):
    """Base email event model."""
    event_type: EmailEventType
    email_id: UUID

    # Event details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Click-specific
    url: Optional[str] = None
    link_id: Optional[str] = None

    # Bounce-specific
    bounce_type: Optional[BounceType] = None
    bounce_reason: Optional[str] = None

    # Provider data
    provider: Optional[EmailProvider] = None
    raw_event: Optional[Dict[str, Any]] = None


class EmailEvent(EmailEventBase):
    """Complete email event model."""
    id: UUID = Field(default_factory=uuid4)
    tracking_id: Optional[str] = None
    recipient_email: Optional[EmailStr] = None

    class Config:
        from_attributes = True


# Unsubscribe Models
class UnsubscribeReason(str, Enum):
    """Reasons for unsubscription."""
    USER_REQUEST = "user_request"
    SPAM_COMPLAINT = "spam_complaint"
    BOUNCE = "bounce"
    ADMIN = "admin"
    COMPLIANCE = "compliance"


class UnsubscribeBase(BaseModel):
    """Base unsubscribe model."""
    email: EmailStr
    reason: UnsubscribeReason = UnsubscribeReason.USER_REQUEST

    # Scope
    global_unsubscribe: bool = False  # Unsubscribe from all emails
    list_ids: Optional[List[str]] = None  # Specific lists to unsubscribe from
    campaign_id: Optional[UUID] = None  # Specific campaign

    # Source
    source_email_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UnsubscribeCreate(UnsubscribeBase):
    """Model for creating an unsubscribe record."""
    pass


class Unsubscribe(UnsubscribeBase):
    """Complete unsubscribe model."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Resubscribe tracking
    resubscribed: bool = False
    resubscribed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Bounce Models
class BounceRecord(BaseModel):
    """Record of a bounced email."""
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    bounce_type: BounceType
    bounce_reason: Optional[str] = None

    # Source
    email_id: UUID
    provider: EmailProvider

    # Timestamps
    bounced_at: datetime = Field(default_factory=datetime.utcnow)

    # Retry tracking
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Campaign/Sequence Models (for workflow integration)
class EmailCampaignBase(BaseModel):
    """Base email campaign model."""
    name: str
    description: Optional[str] = None
    template_id: Optional[UUID] = None

    # Settings
    from_email: EmailStr
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None

    # Tracking
    track_opens: bool = True
    track_clicks: bool = True

    # Status
    is_active: bool = True


class EmailCampaign(EmailCampaignBase):
    """Complete email campaign model."""
    id: UUID = Field(default_factory=uuid4)

    # Statistics
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OutreachSequenceStep(BaseModel):
    """A step in an outreach sequence."""
    step_number: int
    template_id: UUID
    delay_days: int = 0  # Days to wait after previous step
    delay_hours: int = 0

    # Conditions
    skip_if_replied: bool = True
    skip_if_opened: bool = False
    skip_if_clicked: bool = False


class OutreachSequenceBase(BaseModel):
    """Base outreach sequence model."""
    name: str
    description: Optional[str] = None

    # Steps
    steps: List[OutreachSequenceStep]

    # Settings
    from_email: EmailStr
    from_name: Optional[str] = None

    # Status
    is_active: bool = True


class OutreachSequence(OutreachSequenceBase):
    """Complete outreach sequence model."""
    id: UUID = Field(default_factory=uuid4)

    # Statistics
    total_prospects: int = 0
    total_completed: int = 0
    total_replied: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# API Response Models
class SendEmailResponse(BaseModel):
    """Response after sending an email."""
    success: bool
    message_id: UUID
    provider_message_id: Optional[str] = None
    status: EmailStatus
    error: Optional[str] = None


class EmailStatsResponse(BaseModel):
    """Email statistics response."""
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_unsubscribed: int

    delivery_rate: Optional[float] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    bounce_rate: Optional[float] = None


class WebhookPayload(BaseModel):
    """Incoming webhook payload from email provider."""
    provider: EmailProvider
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None  # For webhook verification
