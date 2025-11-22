"""
Meeting Prep Models

Pydantic schemas and SQLAlchemy models for the meeting preparation service.
Supports auto-generated prep briefs including attendee profiles, company research,
previous call history, SPICED context, agenda suggestions, and content recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


# ============================================================================
# Enums
# ============================================================================

class MeetingType(str, Enum):
    """Types of sales meetings."""
    DISCOVERY = "discovery"
    DEMO = "demo"
    FOLLOW_UP = "follow_up"
    NEGOTIATION = "negotiation"
    QBR = "qbr"
    RENEWAL = "renewal"
    KICKOFF = "kickoff"
    CHECK_IN = "check_in"
    OTHER = "other"


class PrepStatus(str, Enum):
    """Status of prep brief generation."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DeliveryMethod(str, Enum):
    """Methods for delivering prep briefs."""
    EMAIL = "email"
    IN_APP = "in_app"
    CALENDAR = "calendar"
    ALL = "all"


class AttendeeRole(str, Enum):
    """Role of meeting attendee."""
    CHAMPION = "champion"
    ECONOMIC_BUYER = "economic_buyer"
    TECHNICAL_BUYER = "technical_buyer"
    INFLUENCER = "influencer"
    BLOCKER = "blocker"
    END_USER = "end_user"
    UNKNOWN = "unknown"


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class Meeting(Base):
    """Database model for calendar meetings."""
    __tablename__ = "meetings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Calendar integration
    calendar_event_id = Column(String(255), nullable=True, index=True)
    calendar_provider = Column(String(50), nullable=True)  # google, outlook

    # Meeting details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    meeting_type = Column(SQLEnum(MeetingType), default=MeetingType.OTHER)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(String(10), default="30")
    location = Column(String(500), nullable=True)
    meeting_link = Column(String(1000), nullable=True)

    # Related entities
    deal_id = Column(PGUUID(as_uuid=True), ForeignKey("deals.id"), nullable=True)
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prep_brief = relationship("MeetingPrepBrief", back_populates="meeting", uselist=False)
    attendees = relationship("MeetingAttendee", back_populates="meeting")


class MeetingAttendee(Base):
    """Database model for meeting attendees."""
    __tablename__ = "meeting_attendees"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)

    # Contact info
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)

    # Enriched data
    linkedin_url = Column(String(500), nullable=True)
    role = Column(SQLEnum(AttendeeRole), default=AttendeeRole.UNKNOWN)
    profile_summary = Column(Text, nullable=True)

    # Link to prospect/contact
    prospect_id = Column(PGUUID(as_uuid=True), ForeignKey("prospects.id"), nullable=True)
    hubspot_contact_id = Column(String(100), nullable=True)

    # Response status
    response_status = Column(String(50), nullable=True)  # accepted, declined, tentative
    is_organizer = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="attendees")


class MeetingPrepBrief(Base):
    """Database model for generated meeting prep briefs."""
    __tablename__ = "meeting_prep_briefs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False, unique=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Generation status
    status = Column(SQLEnum(PrepStatus), default=PrepStatus.PENDING)
    generated_at = Column(DateTime, nullable=True)
    generation_error = Column(Text, nullable=True)

    # Brief content (JSON for flexibility)
    attendee_profiles = Column(JSON, nullable=True)
    company_research = Column(JSON, nullable=True)
    call_history = Column(JSON, nullable=True)
    spiced_context = Column(JSON, nullable=True)
    suggested_agenda = Column(JSON, nullable=True)
    suggested_questions = Column(JSON, nullable=True)
    content_recommendations = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)

    # Delivery tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    calendar_attached = Column(Boolean, default=False)
    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="prep_brief")


# ============================================================================
# Pydantic Request/Response Schemas
# ============================================================================

class AttendeeProfileSchema(BaseModel):
    """Schema for an attendee's enriched profile."""
    email: str
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: AttendeeRole = AttendeeRole.UNKNOWN

    # Enriched data
    background: Optional[str] = None
    career_highlights: Optional[list[str]] = None
    mutual_connections: Optional[list[str]] = None
    recent_activity: Optional[list[str]] = None
    communication_style: Optional[str] = None
    talking_points: Optional[list[str]] = None


class CompanyResearchSchema(BaseModel):
    """Schema for company research summary."""
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None

    # Business context
    description: Optional[str] = None
    recent_news: Optional[list[str]] = None
    key_initiatives: Optional[list[str]] = None
    competitors: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None

    # Financial info
    funding_stage: Optional[str] = None
    annual_revenue: Optional[str] = None

    # Relationship context
    existing_customer: bool = False
    current_products: Optional[list[str]] = None


class CallHistoryItemSchema(BaseModel):
    """Schema for a previous call/interaction."""
    date: datetime
    call_type: str
    attendees: list[str]
    summary: str
    key_outcomes: Optional[list[str]] = None
    action_items: Optional[list[str]] = None
    transcript_id: Optional[UUID] = None


class SPICEDContextSchema(BaseModel):
    """Schema for SPICED methodology context from previous interactions."""
    situation: Optional[str] = None
    pain: Optional[list[str]] = None
    impact: Optional[str] = None
    critical_event: Optional[str] = None
    decision_process: Optional[str] = None
    decision_criteria: Optional[list[str]] = None

    # Scoring from coaching
    overall_score: Optional[float] = None
    gaps: Optional[list[str]] = None
    last_updated: Optional[datetime] = None


class AgendaItemSchema(BaseModel):
    """Schema for a suggested agenda item."""
    topic: str
    duration_minutes: int
    description: Optional[str] = None
    owner: Optional[str] = None
    priority: int = 1


class QuestionSchema(BaseModel):
    """Schema for a suggested question."""
    question: str
    category: str  # discovery, pain, impact, etc.
    context: Optional[str] = None
    follow_ups: Optional[list[str]] = None


class ContentRecommendationSchema(BaseModel):
    """Schema for recommended content to share."""
    title: str
    content_type: str  # case_study, one_pager, demo, etc.
    relevance: str
    url: Optional[str] = None
    content_id: Optional[UUID] = None


class MeetingPrepBriefSchema(BaseModel):
    """Complete meeting prep brief response schema."""
    id: UUID
    meeting_id: UUID
    status: PrepStatus
    generated_at: Optional[datetime] = None

    # Brief content
    executive_summary: Optional[str] = None
    attendee_profiles: Optional[list[AttendeeProfileSchema]] = None
    company_research: Optional[CompanyResearchSchema] = None
    call_history: Optional[list[CallHistoryItemSchema]] = None
    spiced_context: Optional[SPICEDContextSchema] = None
    suggested_agenda: Optional[list[AgendaItemSchema]] = None
    suggested_questions: Optional[list[QuestionSchema]] = None
    content_recommendations: Optional[list[ContentRecommendationSchema]] = None

    # Delivery status
    email_sent: bool = False
    calendar_attached: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Request Schemas
# ============================================================================

class MeetingCreateRequest(BaseModel):
    """Request schema for creating a meeting."""
    title: str
    scheduled_at: datetime
    duration_minutes: int = 30
    meeting_type: MeetingType = MeetingType.OTHER
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendee_emails: list[str] = Field(default_factory=list)
    deal_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    calendar_event_id: Optional[str] = None
    calendar_provider: Optional[str] = None


class MeetingSyncRequest(BaseModel):
    """Request schema for syncing meetings from calendar."""
    calendar_provider: str  # google, outlook
    sync_days_ahead: int = 7
    include_past_days: int = 0


class PrepBriefGenerateRequest(BaseModel):
    """Request schema for generating a prep brief."""
    meeting_id: UUID
    force_regenerate: bool = False
    delivery_methods: list[DeliveryMethod] = Field(default=[DeliveryMethod.IN_APP])
    include_sections: Optional[list[str]] = None  # If None, include all


class PrepBriefDeliveryRequest(BaseModel):
    """Request schema for delivering a prep brief."""
    brief_id: UUID
    delivery_methods: list[DeliveryMethod]
    recipient_email: Optional[str] = None  # Override default


class BulkPrepGenerateRequest(BaseModel):
    """Request schema for bulk generating prep briefs."""
    meeting_ids: Optional[list[UUID]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    auto_deliver: bool = False
    delivery_methods: list[DeliveryMethod] = Field(default=[DeliveryMethod.IN_APP])


# ============================================================================
# Response Schemas
# ============================================================================

class MeetingSchema(BaseModel):
    """Response schema for a meeting."""
    id: UUID
    title: str
    meeting_type: MeetingType
    scheduled_at: datetime
    duration_minutes: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: list[AttendeeProfileSchema] = Field(default_factory=list)
    has_prep_brief: bool = False
    prep_brief_status: Optional[PrepStatus] = None
    deal_id: Optional[UUID] = None
    company_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class MeetingListResponse(BaseModel):
    """Response schema for listing meetings."""
    meetings: list[MeetingSchema]
    total: int
    page: int = 1
    per_page: int = 20


class PrepBriefStatusResponse(BaseModel):
    """Response schema for prep brief generation status."""
    meeting_id: UUID
    brief_id: Optional[UUID] = None
    status: PrepStatus
    message: Optional[str] = None
    generated_at: Optional[datetime] = None


class DeliveryStatusResponse(BaseModel):
    """Response schema for delivery status."""
    brief_id: UUID
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    calendar_attached: bool = False
    in_app_available: bool = True
