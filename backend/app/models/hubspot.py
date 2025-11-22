<<<<<<< HEAD
"""HubSpot Integration model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class HubSpotIntegration(Base, TimestampMixin):
    """HubSpot OAuth2 integration and sync tracking."""

    __tablename__ = "hubspot_integrations"

    # OAuth2 tokens
    access_token: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Scope and permissions
    scopes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # HubSpot account info
    hub_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hub_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hub_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Integration status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Sync tracking
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sync statistics
    contacts_synced: Mapped[int] = mapped_column(default=0, nullable=False)
    companies_synced: Mapped[int] = mapped_column(default=0, nullable=False)
    deals_synced: Mapped[int] = mapped_column(default=0, nullable=False)

    # Field mapping configuration (JSON)
    contact_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deal_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, unique=True
    )

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        return datetime.utcnow() >= self.token_expires_at.replace(tzinfo=None)

    def __repr__(self) -> str:
        return f"<HubSpotIntegration hub_id={self.hub_id}>"
=======
"""
HubSpot CRM Pydantic Models

This module defines data models for HubSpot CRM integration including
contacts, deals, notes, tasks, and related entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# Enums for HubSpot entity types and statuses

class DealStage(str, Enum):
    """HubSpot deal pipeline stages."""
    APPOINTMENT_SCHEDULED = "appointmentscheduled"
    QUALIFIED_TO_BUY = "qualifiedtobuy"
    PRESENTATION_SCHEDULED = "presentationscheduled"
    DECISION_MAKER_BOUGHT_IN = "decisionmakerboughtin"
    CONTRACT_SENT = "contractsent"
    CLOSED_WON = "closedwon"
    CLOSED_LOST = "closedlost"


class TaskStatus(str, Enum):
    """HubSpot task statuses."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    DEFERRED = "DEFERRED"


class TaskPriority(str, Enum):
    """HubSpot task priorities."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskType(str, Enum):
    """HubSpot task types."""
    TODO = "TODO"
    CALL = "CALL"
    EMAIL = "EMAIL"


class EngagementType(str, Enum):
    """HubSpot engagement types for notes and activities."""
    NOTE = "NOTE"
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    TASK = "TASK"


# Base models

class HubSpotBaseModel(BaseModel):
    """Base model for all HubSpot entities."""

    class Config:
        populate_by_name = True
        use_enum_values = True


# Contact models

class ContactProperties(HubSpotBaseModel):
    """Properties for a HubSpot contact."""
    email: EmailStr | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    company: str | None = None
    jobtitle: str | None = Field(None, alias="job_title")
    website: str | None = None
    lifecyclestage: str | None = Field(None, alias="lifecycle_stage")
    hs_lead_status: str | None = Field(None, alias="lead_status")
    city: str | None = None
    state: str | None = None
    country: str | None = None
    address: str | None = None
    zip: str | None = None
    linkedin_url: str | None = Field(None, alias="linkedinbio")
    twitter_handle: str | None = Field(None, alias="twitterhandle")
    notes_last_updated: datetime | None = None
    num_notes: int | None = None


class ContactCreate(HubSpotBaseModel):
    """Request model for creating a contact."""
    email: EmailStr
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    company: str | None = None
    jobtitle: str | None = None
    website: str | None = None
    lifecyclestage: str = "lead"
    city: str | None = None
    state: str | None = None
    country: str | None = None


class ContactUpdate(HubSpotBaseModel):
    """Request model for updating a contact."""
    email: EmailStr | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    company: str | None = None
    jobtitle: str | None = None
    website: str | None = None
    lifecyclestage: str | None = None
    hs_lead_status: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None


class Contact(HubSpotBaseModel):
    """HubSpot contact entity."""
    id: str
    properties: ContactProperties
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    archived: bool = False


class ContactResponse(HubSpotBaseModel):
    """Response model for contact operations."""
    contact: Contact
    success: bool = True
    message: str | None = None


class ContactSearchResult(HubSpotBaseModel):
    """Response model for contact search."""
    total: int
    contacts: list[Contact]


# Deal models

class DealProperties(HubSpotBaseModel):
    """Properties for a HubSpot deal."""
    dealname: str = Field(..., alias="deal_name")
    amount: float | None = None
    dealstage: DealStage | str = Field(DealStage.APPOINTMENT_SCHEDULED, alias="deal_stage")
    pipeline: str = "default"
    closedate: datetime | None = Field(None, alias="close_date")
    hubspot_owner_id: str | None = Field(None, alias="owner_id")
    description: str | None = None
    deal_currency_code: str = "USD"
    hs_priority: str | None = Field(None, alias="priority")


class DealCreate(HubSpotBaseModel):
    """Request model for creating a deal."""
    dealname: str
    amount: float | None = None
    dealstage: DealStage | str = DealStage.APPOINTMENT_SCHEDULED
    pipeline: str = "default"
    closedate: datetime | None = None
    hubspot_owner_id: str | None = None
    description: str | None = None
    associated_contact_ids: list[str] = Field(default_factory=list)
    associated_company_ids: list[str] = Field(default_factory=list)


class Deal(HubSpotBaseModel):
    """HubSpot deal entity."""
    id: str
    properties: DealProperties
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    archived: bool = False


class DealResponse(HubSpotBaseModel):
    """Response model for deal operations."""
    deal: Deal
    success: bool = True
    message: str | None = None


# Note/Engagement models

class NoteCreate(HubSpotBaseModel):
    """Request model for creating a note."""
    body: str = Field(..., description="Note content in HTML or plain text")
    contact_id: str | None = None
    company_id: str | None = None
    deal_id: str | None = None
    timestamp: datetime | None = None
    owner_id: str | None = None


class Note(HubSpotBaseModel):
    """HubSpot note/engagement entity."""
    id: str
    engagement_type: EngagementType = EngagementType.NOTE
    body: str
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    associations: dict[str, list[str]] = Field(default_factory=dict)


class NoteResponse(HubSpotBaseModel):
    """Response model for note operations."""
    note: Note
    success: bool = True
    message: str | None = None


# Task models

class TaskCreate(HubSpotBaseModel):
    """Request model for creating a task."""
    subject: str = Field(..., description="Task subject/title")
    body: str | None = Field(None, description="Task description")
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.TODO
    due_date: datetime | None = None
    contact_id: str | None = None
    company_id: str | None = None
    deal_id: str | None = None
    owner_id: str | None = None


class Task(HubSpotBaseModel):
    """HubSpot task entity."""
    id: str
    subject: str
    body: str | None = None
    status: TaskStatus
    priority: TaskPriority
    task_type: TaskType
    due_date: datetime | None = None
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    associations: dict[str, list[str]] = Field(default_factory=dict)


class TaskResponse(HubSpotBaseModel):
    """Response model for task operations."""
    task: Task
    success: bool = True
    message: str | None = None


# Search models

class SearchFilter(HubSpotBaseModel):
    """Filter for HubSpot search queries."""
    property_name: str = Field(..., alias="propertyName")
    operator: str  # EQ, NEQ, LT, LTE, GT, GTE, CONTAINS, NOT_CONTAINS, etc.
    value: str


class SearchFilterGroup(HubSpotBaseModel):
    """Group of filters (AND logic within group)."""
    filters: list[SearchFilter]


class ContactSearchRequest(HubSpotBaseModel):
    """Request model for searching contacts."""
    query: str | None = None
    filter_groups: list[SearchFilterGroup] = Field(default_factory=list, alias="filterGroups")
    sorts: list[dict[str, str]] = Field(default_factory=list)
    properties: list[str] = Field(default_factory=list)
    limit: int = Field(10, ge=1, le=100)
    after: str | None = None  # Pagination cursor


# OAuth models

class OAuthToken(HubSpotBaseModel):
    """HubSpot OAuth token response."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    expires_at: datetime | None = None


class OAuthTokenRefresh(HubSpotBaseModel):
    """Request model for refreshing OAuth token."""
    refresh_token: str
    client_id: str
    client_secret: str


# Error models

class HubSpotError(HubSpotBaseModel):
    """HubSpot API error response."""
    status: str
    message: str
    correlation_id: str | None = Field(None, alias="correlationId")
    category: str | None = None
    errors: list[dict[str, Any]] = Field(default_factory=list)


class HubSpotAPIResponse(HubSpotBaseModel):
    """Generic HubSpot API response wrapper."""
    success: bool
    data: dict[str, Any] | list[Any] | None = None
    error: HubSpotError | None = None


# Webhook models

class WebhookEvent(HubSpotBaseModel):
    """HubSpot webhook event payload."""
    event_id: str = Field(..., alias="eventId")
    subscription_id: int = Field(..., alias="subscriptionId")
    portal_id: int = Field(..., alias="portalId")
    app_id: int = Field(..., alias="appId")
    occurred_at: datetime = Field(..., alias="occurredAt")
    subscription_type: str = Field(..., alias="subscriptionType")
    attempt_number: int = Field(0, alias="attemptNumber")
    object_id: int = Field(..., alias="objectId")
    property_name: str | None = Field(None, alias="propertyName")
    property_value: str | None = Field(None, alias="propertyValue")
    change_source: str | None = Field(None, alias="changeSource")


# Association models

class AssociationType(str, Enum):
    """HubSpot association types."""
    CONTACT_TO_COMPANY = "contact_to_company"
    CONTACT_TO_DEAL = "contact_to_deal"
    DEAL_TO_COMPANY = "deal_to_company"
    NOTE_TO_CONTACT = "note_to_contact"
    TASK_TO_CONTACT = "task_to_contact"


class Association(HubSpotBaseModel):
    """HubSpot association between objects."""
    from_object_type: str
    from_object_id: str
    to_object_type: str
    to_object_id: str
    association_type: str


# Batch operation models

class BatchContactCreate(HubSpotBaseModel):
    """Request model for batch contact creation."""
    contacts: list[ContactCreate]


class BatchContactResponse(HubSpotBaseModel):
    """Response model for batch contact operations."""
    status: str
    results: list[Contact]
    errors: list[HubSpotError] = Field(default_factory=list)
    num_errors: int = 0
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
