"""Outreach campaign models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class OutreachFormat(str, Enum):
    """Type of outreach."""

    EMAIL = "email"
    LINKEDIN = "linkedin"
    MULTI_CHANNEL = "multi_channel"


class ExportFormat(str, Enum):
    """Export format for campaigns."""

    INSTANTLY = "instantly"
    HEYREACH = "heyreach"
    CSV = "csv"


class OutreachStep(BaseModel):
    """A single step in an outreach sequence."""

    step_number: int
    channel: str  # email, linkedin_message, linkedin_connection, etc.
    delay_days: int = 0
    subject: Optional[str] = None  # For emails
    body: str
    variant: str = "A"  # For A/B testing
    personalization_fields: list[str] = Field(default_factory=list)


class OutreachSequence(BaseModel):
    """A sequence of outreach steps."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    format: OutreachFormat
    steps: list[OutreachStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OutreachCampaign(BaseModel):
    """Outreach campaign for a prospect."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    prospect_email: str
    prospect_name: str
    prospect_first_name: Optional[str] = None
    prospect_last_name: Optional[str] = None
    prospect_title: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None

    # Generated content
    email_sequence: Optional[OutreachSequence] = None
    linkedin_sequence: Optional[OutreachSequence] = None

    # Personalization data
    company_insights: Optional[dict] = None
    prospect_insights: Optional[dict] = None
    pain_points: list[str] = Field(default_factory=list)
    value_propositions: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"  # draft, active, paused, completed


class CampaignGenerateRequest(BaseModel):
    """Request to generate an outreach campaign."""

    prospect_email: str
    prospect_name: str
    prospect_first_name: Optional[str] = None
    prospect_last_name: Optional[str] = None
    prospect_title: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None

    # Optional enrichment data
    company_data: Optional[dict] = None
    prospect_data: Optional[dict] = None
    web_research: Optional[dict] = None
    ai_insights: Optional[dict] = None

    # Generation options
    format: OutreachFormat = OutreachFormat.MULTI_CHANNEL
    num_email_steps: int = 3
    num_linkedin_steps: int = 2
    tone: str = "professional"  # professional, casual, formal
    product_info: Optional[dict] = None
    sender_info: Optional[dict] = None


class CampaignGenerateResponse(BaseModel):
    """Response from campaign generation."""

    success: bool
    campaign: Optional[OutreachCampaign] = None
    error: Optional[str] = None


class InstantlyCSVRow(BaseModel):
    """Row format for Instantly CSV export."""

    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    personalization1: Optional[str] = None  # Custom field 1
    personalization2: Optional[str] = None  # Custom field 2
    personalization3: Optional[str] = None  # Custom field 3
    personalization4: Optional[str] = None  # Custom field 4
    personalization5: Optional[str] = None  # Custom field 5


class HeyReachCSVRow(BaseModel):
    """Row format for HeyReach CSV export."""

    linkedin_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    personalization_snippet: Optional[str] = None
    custom_message: Optional[str] = None
