"""
Deal Room Models

This module defines SQLAlchemy ORM models and Pydantic schemas for the deal room feature.
Deal rooms are branded shareable spaces for sharing sales content with prospects.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

# Assuming base model exists - will be created by AGENT-011
try:
    from backend.app.db.base import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================

class DealRoomStatus(str, Enum):
    """Status of a deal room"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class ContentType(str, Enum):
    """Types of content that can be added to a deal room"""
    PROPOSAL = "proposal"
    DECK = "deck"
    CASE_STUDY = "case_study"
    PRICING = "pricing"
    CONTRACT = "contract"
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"


class AccessLevel(str, Enum):
    """Access levels for deal room content"""
    PUBLIC = "public"           # Anyone with link can view
    PASSWORD = "password"       # Requires password
    EMAIL_GATE = "email_gate"   # Requires email to view
    INVITE_ONLY = "invite_only" # Only invited emails can access


class ActionPlanItemStatus(str, Enum):
    """Status of mutual action plan items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ActionPlanItemOwner(str, Enum):
    """Owner type for action plan items"""
    SELLER = "seller"
    BUYER = "buyer"
    BOTH = "both"


# =============================================================================
# SQLALCHEMY ORM MODELS
# =============================================================================

class DealRoom(Base):
    """
    Main deal room entity.
    Represents a branded shareable space for prospect engagement.
    """
    __tablename__ = "deal_rooms"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Identification
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Deal association
    deal_id = Column(String(100), nullable=True)  # HubSpot deal ID
    deal_name = Column(String(255), nullable=True)
    deal_value = Column(Integer, nullable=True)  # Value in cents

    # Prospect information
    prospect_company = Column(String(255), nullable=True)
    prospect_name = Column(String(255), nullable=True)
    prospect_email = Column(String(255), nullable=True)

    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#0066FF")  # Hex color
    secondary_color = Column(String(7), default="#1A1A2E")
    custom_css = Column(Text, nullable=True)
    favicon_url = Column(String(500), nullable=True)

    # Access control
    status = Column(SQLEnum(DealRoomStatus), default=DealRoomStatus.DRAFT)
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.PUBLIC)
    password_hash = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    max_views = Column(Integer, nullable=True)
    allowed_emails = Column(JSON, default=list)  # List of allowed email addresses

    # Settings
    show_action_plan = Column(Boolean, default=True)
    show_timeline = Column(Boolean, default=True)
    enable_comments = Column(Boolean, default=True)
    notify_on_view = Column(Boolean, default=True)
    require_nda = Column(Boolean, default=False)

    # Owner
    owner_id = Column(PGUUID(as_uuid=True), nullable=False)
    team_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)

    # Relationships
    sections = relationship("DealRoomSection", back_populates="deal_room", cascade="all, delete-orphan")
    contents = relationship("DealRoomContent", back_populates="deal_room", cascade="all, delete-orphan")
    action_plan_items = relationship("ActionPlanItem", back_populates="deal_room", cascade="all, delete-orphan")
    view_events = relationship("DealRoomViewEvent", back_populates="deal_room", cascade="all, delete-orphan")
    invitations = relationship("DealRoomInvitation", back_populates="deal_room", cascade="all, delete-orphan")


class DealRoomSection(Base):
    """
    Sections for organizing content within a deal room.
    Supports nested folder-like structure.
    """
    __tablename__ = "deal_room_sections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_room_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_rooms.id"), nullable=False)
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_room_sections.id"), nullable=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon identifier
    order_index = Column(Integer, default=0)
    is_collapsed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="sections")
    parent = relationship("DealRoomSection", remote_side=[id], backref="children")
    contents = relationship("DealRoomContent", back_populates="section")


class DealRoomContent(Base):
    """
    Individual content items within a deal room.
    Supports various content types: proposals, decks, case studies, etc.
    """
    __tablename__ = "deal_room_contents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_room_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_rooms.id"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_room_sections.id"), nullable=True)

    # Content details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(SQLEnum(ContentType), nullable=False)

    # File/Link information
    file_url = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_mime_type = Column(String(100), nullable=True)
    external_link = Column(String(1000), nullable=True)
    embed_code = Column(Text, nullable=True)

    # Thumbnail
    thumbnail_url = Column(String(500), nullable=True)

    # Display settings
    order_index = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)

    # Version tracking
    version = Column(Integer, default=1)

    # Metadata
    metadata = Column(JSON, default=dict)  # Flexible metadata storage

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploaded_by = Column(PGUUID(as_uuid=True), nullable=True)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="contents")
    section = relationship("DealRoomSection", back_populates="contents")
    view_events = relationship("ContentViewEvent", back_populates="content", cascade="all, delete-orphan")


class ActionPlanItem(Base):
    """
    Mutual action plan items for deal progression.
    Tracks tasks, milestones, and responsibilities.
    """
    __tablename__ = "action_plan_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_room_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_rooms.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Task details
    status = Column(SQLEnum(ActionPlanItemStatus), default=ActionPlanItemStatus.PENDING)
    owner = Column(SQLEnum(ActionPlanItemOwner), default=ActionPlanItemOwner.SELLER)
    assignee_name = Column(String(255), nullable=True)
    assignee_email = Column(String(255), nullable=True)

    # Timeline
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Organization
    order_index = Column(Integer, default=0)
    is_milestone = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="action_plan_items")


class DealRoomViewEvent(Base):
    """
    Analytics tracking for deal room views.
    Records who viewed what and when.
    """
    __tablename__ = "deal_room_view_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_room_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_rooms.id"), nullable=False)

    # Viewer information
    viewer_email = Column(String(255), nullable=True)
    viewer_name = Column(String(255), nullable=True)
    viewer_ip = Column(String(45), nullable=True)  # Supports IPv6
    viewer_user_agent = Column(Text, nullable=True)

    # Session tracking
    session_id = Column(String(100), nullable=True)

    # Device/Location info
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    city = Column(String(100), nullable=True)

    # Engagement metrics
    time_spent_seconds = Column(Integer, default=0)
    pages_viewed = Column(Integer, default=0)

    # Timestamps
    viewed_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="view_events")
    content_views = relationship("ContentViewEvent", back_populates="view_event", cascade="all, delete-orphan")


class ContentViewEvent(Base):
    """
    Analytics tracking for individual content views within a deal room.
    """
    __tablename__ = "content_view_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    view_event_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_room_view_events.id"), nullable=False)
    content_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_room_contents.id"), nullable=False)

    # Engagement metrics
    time_spent_seconds = Column(Integer, default=0)
    scroll_depth_percent = Column(Integer, default=0)  # 0-100
    downloaded = Column(Boolean, default=False)

    # Timestamps
    viewed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    view_event = relationship("DealRoomViewEvent", back_populates="content_views")
    content = relationship("DealRoomContent", back_populates="view_events")


class DealRoomInvitation(Base):
    """
    Invitations sent to prospects for deal room access.
    """
    __tablename__ = "deal_room_invitations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_room_id = Column(PGUUID(as_uuid=True), ForeignKey("deal_rooms.id"), nullable=False)

    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)

    # Invitation details
    message = Column(Text, nullable=True)
    token = Column(String(100), unique=True, nullable=False)

    # Status
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="invitations")


# =============================================================================
# PYDANTIC SCHEMAS - Request/Response Models
# =============================================================================

# --- Base Schemas ---

class DealRoomBrandingSchema(BaseModel):
    """Branding configuration for a deal room"""
    logo_url: Optional[str] = None
    primary_color: str = "#0066FF"
    secondary_color: str = "#1A1A2E"
    custom_css: Optional[str] = None
    favicon_url: Optional[str] = None


class DealRoomSettingsSchema(BaseModel):
    """Settings for a deal room"""
    show_action_plan: bool = True
    show_timeline: bool = True
    enable_comments: bool = True
    notify_on_view: bool = True
    require_nda: bool = False


class AccessControlSchema(BaseModel):
    """Access control settings"""
    access_level: AccessLevel = AccessLevel.PUBLIC
    password: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_views: Optional[int] = None
    allowed_emails: List[str] = Field(default_factory=list)


# --- Deal Room Schemas ---

class DealRoomCreateRequest(BaseModel):
    """Request schema for creating a deal room"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    # Deal info
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None
    deal_value: Optional[int] = None

    # Prospect info
    prospect_company: Optional[str] = None
    prospect_name: Optional[str] = None
    prospect_email: Optional[EmailStr] = None

    # Optional configurations
    branding: Optional[DealRoomBrandingSchema] = None
    settings: Optional[DealRoomSettingsSchema] = None
    access_control: Optional[AccessControlSchema] = None


class DealRoomUpdateRequest(BaseModel):
    """Request schema for updating a deal room"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

    deal_id: Optional[str] = None
    deal_name: Optional[str] = None
    deal_value: Optional[int] = None

    prospect_company: Optional[str] = None
    prospect_name: Optional[str] = None
    prospect_email: Optional[EmailStr] = None

    status: Optional[DealRoomStatus] = None
    branding: Optional[DealRoomBrandingSchema] = None
    settings: Optional[DealRoomSettingsSchema] = None
    access_control: Optional[AccessControlSchema] = None


class DealRoomResponse(BaseModel):
    """Response schema for a deal room"""
    id: UUID
    slug: str
    title: str
    description: Optional[str]

    deal_id: Optional[str]
    deal_name: Optional[str]
    deal_value: Optional[int]

    prospect_company: Optional[str]
    prospect_name: Optional[str]
    prospect_email: Optional[str]

    status: DealRoomStatus
    access_level: AccessLevel
    expires_at: Optional[datetime]

    branding: DealRoomBrandingSchema
    settings: DealRoomSettingsSchema

    owner_id: UUID
    team_id: Optional[UUID]

    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    last_viewed_at: Optional[datetime]

    # Computed fields
    share_url: Optional[str] = None
    total_views: int = 0
    unique_viewers: int = 0

    class Config:
        from_attributes = True


class DealRoomListResponse(BaseModel):
    """Response schema for listing deal rooms"""
    items: List[DealRoomResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# --- Section Schemas ---

class SectionCreateRequest(BaseModel):
    """Request schema for creating a section"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    order_index: int = 0


class SectionUpdateRequest(BaseModel):
    """Request schema for updating a section"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    order_index: Optional[int] = None
    is_collapsed: Optional[bool] = None


class SectionResponse(BaseModel):
    """Response schema for a section"""
    id: UUID
    deal_room_id: UUID
    parent_id: Optional[UUID]
    name: str
    description: Optional[str]
    icon: Optional[str]
    order_index: int
    is_collapsed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Content Schemas ---

class ContentCreateRequest(BaseModel):
    """Request schema for creating content"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: ContentType
    section_id: Optional[UUID] = None

    # File/Link (one of these should be provided)
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_mime_type: Optional[str] = None
    external_link: Optional[str] = None
    embed_code: Optional[str] = None

    thumbnail_url: Optional[str] = None
    order_index: int = 0
    is_featured: bool = False
    is_pinned: bool = False
    metadata: dict = Field(default_factory=dict)


class ContentUpdateRequest(BaseModel):
    """Request schema for updating content"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    section_id: Optional[UUID] = None

    file_url: Optional[str] = None
    external_link: Optional[str] = None
    thumbnail_url: Optional[str] = None

    order_index: Optional[int] = None
    is_featured: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_hidden: Optional[bool] = None
    metadata: Optional[dict] = None


class ContentResponse(BaseModel):
    """Response schema for content"""
    id: UUID
    deal_room_id: UUID
    section_id: Optional[UUID]

    title: str
    description: Optional[str]
    content_type: ContentType

    file_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    file_mime_type: Optional[str]
    external_link: Optional[str]

    thumbnail_url: Optional[str]
    order_index: int
    is_featured: bool
    is_pinned: bool
    is_hidden: bool
    version: int

    metadata: dict

    created_at: datetime
    updated_at: datetime

    # Computed
    view_count: int = 0
    download_count: int = 0

    class Config:
        from_attributes = True


# --- Action Plan Schemas ---

class ActionPlanItemCreateRequest(BaseModel):
    """Request schema for creating an action plan item"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner: ActionPlanItemOwner = ActionPlanItemOwner.SELLER
    assignee_name: Optional[str] = None
    assignee_email: Optional[EmailStr] = None
    due_date: Optional[datetime] = None
    order_index: int = 0
    is_milestone: bool = False


class ActionPlanItemUpdateRequest(BaseModel):
    """Request schema for updating an action plan item"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ActionPlanItemStatus] = None
    owner: Optional[ActionPlanItemOwner] = None
    assignee_name: Optional[str] = None
    assignee_email: Optional[EmailStr] = None
    due_date: Optional[datetime] = None
    order_index: Optional[int] = None
    is_milestone: Optional[bool] = None


class ActionPlanItemResponse(BaseModel):
    """Response schema for an action plan item"""
    id: UUID
    deal_room_id: UUID
    title: str
    description: Optional[str]
    status: ActionPlanItemStatus
    owner: ActionPlanItemOwner
    assignee_name: Optional[str]
    assignee_email: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    order_index: int
    is_milestone: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Analytics Schemas ---

class ViewEventResponse(BaseModel):
    """Response schema for a view event"""
    id: UUID
    deal_room_id: UUID
    viewer_email: Optional[str]
    viewer_name: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    country: Optional[str]
    city: Optional[str]
    time_spent_seconds: int
    pages_viewed: int
    viewed_at: datetime
    last_activity_at: datetime

    class Config:
        from_attributes = True


class ContentViewResponse(BaseModel):
    """Response schema for content view analytics"""
    content_id: UUID
    content_title: str
    view_count: int
    unique_viewers: int
    total_time_spent: int
    avg_scroll_depth: float
    download_count: int


class AnalyticsSummaryResponse(BaseModel):
    """Summary analytics for a deal room"""
    deal_room_id: UUID
    total_views: int
    unique_viewers: int
    total_time_spent_seconds: int
    avg_time_per_visit_seconds: float
    most_viewed_content: List[ContentViewResponse]
    recent_views: List[ViewEventResponse]
    views_by_day: dict  # date string -> count
    views_by_device: dict  # device type -> count


# --- Invitation Schemas ---

class InvitationCreateRequest(BaseModel):
    """Request schema for creating an invitation"""
    email: EmailStr
    name: Optional[str] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class InvitationResponse(BaseModel):
    """Response schema for an invitation"""
    id: UUID
    deal_room_id: UUID
    email: str
    name: Optional[str]
    message: Optional[str]
    token: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    accepted_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Public View Schemas ---

class PublicDealRoomResponse(BaseModel):
    """Public response schema for viewing a deal room (no sensitive data)"""
    slug: str
    title: str
    description: Optional[str]

    prospect_company: Optional[str]

    branding: DealRoomBrandingSchema

    show_action_plan: bool
    show_timeline: bool
    enable_comments: bool

    # Content organized by sections
    sections: List["PublicSectionResponse"]
    action_plan: List["PublicActionPlanItemResponse"]


class PublicSectionResponse(BaseModel):
    """Public section response"""
    id: UUID
    name: str
    description: Optional[str]
    icon: Optional[str]
    order_index: int
    contents: List["PublicContentResponse"]
    children: List["PublicSectionResponse"] = Field(default_factory=list)


class PublicContentResponse(BaseModel):
    """Public content response"""
    id: UUID
    title: str
    description: Optional[str]
    content_type: ContentType
    file_url: Optional[str]
    external_link: Optional[str]
    thumbnail_url: Optional[str]
    order_index: int
    is_featured: bool


class PublicActionPlanItemResponse(BaseModel):
    """Public action plan item response"""
    id: UUID
    title: str
    description: Optional[str]
    status: ActionPlanItemStatus
    owner: ActionPlanItemOwner
    due_date: Optional[datetime]
    is_milestone: bool
    order_index: int


class AccessVerificationRequest(BaseModel):
    """Request to verify access to a deal room"""
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    invitation_token: Optional[str] = None


class AccessVerificationResponse(BaseModel):
    """Response for access verification"""
    granted: bool
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None


# Update forward references
PublicDealRoomResponse.model_rebuild()
PublicSectionResponse.model_rebuild()
