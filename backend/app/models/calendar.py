"""
Calendar Models for Sales OS

Defines data models for calendar integrations, events, and transcript linking.
Supports Google Calendar and Microsoft Outlook/365 providers.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID, uuid4


# Enums

class CalendarProvider(str, Enum):
    """Supported calendar providers."""
    GOOGLE = "google"
    OUTLOOK = "outlook"


class EventStatus(str, Enum):
    """Calendar event status."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class AttendeeStatus(str, Enum):
    """Attendee response status."""
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NEEDS_ACTION = "needs_action"


class SyncStatus(str, Enum):
    """Integration sync status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


# Pydantic Models for API Validation

class Attendee(BaseModel):
    """Meeting attendee information."""
    email: EmailStr
    name: Optional[str] = None
    status: AttendeeStatus = AttendeeStatus.NEEDS_ACTION
    is_organizer: bool = False
    is_optional: bool = False


class MeetingLink(BaseModel):
    """Video conferencing link information."""
    url: str
    provider: Optional[str] = None  # zoom, meet, teams, etc.
    meeting_id: Optional[str] = None
    passcode: Optional[str] = None


class CalendarEventBase(BaseModel):
    """Base calendar event model."""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    location: Optional[str] = None
    is_all_day: bool = False
    attendees: List[Attendee] = Field(default_factory=list)
    meeting_link: Optional[MeetingLink] = None
    recurrence_rule: Optional[str] = None


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a calendar event."""
    send_notifications: bool = True


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[Attendee]] = None
    meeting_link: Optional[MeetingLink] = None


class CalendarEvent(CalendarEventBase):
    """Full calendar event model."""
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    integration_id: UUID
    external_id: str  # ID from the calendar provider
    provider: CalendarProvider
    status: EventStatus = EventStatus.CONFIRMED
    html_link: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    synced_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Optional[Dict[str, Any]] = None  # Original provider data

    class Config:
        from_attributes = True


class CalendarEventResponse(BaseModel):
    """API response for calendar event."""
    id: UUID
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str
    location: Optional[str] = None
    is_all_day: bool
    attendees: List[Attendee]
    meeting_link: Optional[MeetingLink] = None
    status: EventStatus
    html_link: Optional[str] = None
    provider: CalendarProvider
    transcript_id: Optional[UUID] = None
    has_transcript: bool = False


# Calendar Integration Models

class CalendarIntegrationBase(BaseModel):
    """Base calendar integration model."""
    provider: CalendarProvider
    calendar_id: Optional[str] = None  # Specific calendar to sync
    sync_enabled: bool = True
    sync_past_days: int = 7
    sync_future_days: int = 30


class CalendarIntegrationCreate(CalendarIntegrationBase):
    """Schema for creating a calendar integration."""
    pass


class CalendarIntegration(CalendarIntegrationBase):
    """Full calendar integration model."""
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    user_id: UUID
    status: SyncStatus = SyncStatus.ACTIVE
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class CalendarIntegrationResponse(BaseModel):
    """API response for calendar integration (excludes sensitive data)."""
    id: UUID
    provider: CalendarProvider
    calendar_id: Optional[str] = None
    status: SyncStatus
    sync_enabled: bool
    last_sync_at: Optional[datetime] = None
    created_at: datetime


# Meeting-Transcript Link Models

class MeetingTranscriptLinkBase(BaseModel):
    """Base model for linking meetings to transcripts."""
    event_id: UUID
    transcript_id: UUID
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    link_type: str = "automatic"  # automatic, manual
    notes: Optional[str] = None


class MeetingTranscriptLinkCreate(MeetingTranscriptLinkBase):
    """Schema for creating a meeting-transcript link."""
    pass


class MeetingTranscriptLink(MeetingTranscriptLinkBase):
    """Full meeting-transcript link model."""
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class MeetingTranscriptLinkResponse(BaseModel):
    """API response for meeting-transcript link."""
    id: UUID
    event_id: UUID
    transcript_id: UUID
    confidence_score: float
    link_type: str
    created_at: datetime


# OAuth Models

class OAuthState(BaseModel):
    """OAuth state for CSRF protection."""
    state: str
    provider: CalendarProvider
    user_id: UUID
    org_id: UUID
    redirect_uri: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OAuthCallback(BaseModel):
    """OAuth callback data."""
    code: str
    state: str
    error: Optional[str] = None
    error_description: Optional[str] = None


class OAuthTokens(BaseModel):
    """OAuth tokens from provider."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None


# Sync Models

class SyncRequest(BaseModel):
    """Request to sync calendar events."""
    integration_id: UUID
    full_sync: bool = False
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SyncResult(BaseModel):
    """Result of a calendar sync operation."""
    integration_id: UUID
    events_synced: int
    events_created: int
    events_updated: int
    events_deleted: int
    errors: List[str] = Field(default_factory=list)
    synced_at: datetime = Field(default_factory=datetime.utcnow)


# Dashboard Widget Models

class UpcomingMeeting(BaseModel):
    """Upcoming meeting for dashboard widget."""
    id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    attendees_count: int
    has_transcript: bool
    meeting_link: Optional[str] = None
    provider: CalendarProvider


class CalendarWidgetData(BaseModel):
    """Data for the calendar dashboard widget."""
    upcoming_meetings: List[UpcomingMeeting]
    meetings_today: int
    meetings_this_week: int
    total_integrations: int
    next_meeting: Optional[UpcomingMeeting] = None


# List/Filter Models

class CalendarEventFilter(BaseModel):
    """Filter options for listing calendar events."""
    provider: Optional[CalendarProvider] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_transcript: Optional[bool] = None
    attendee_email: Optional[str] = None
    search: Optional[str] = None


class CalendarEventList(BaseModel):
    """Paginated list of calendar events."""
    items: List[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
