"""Prospect data models for enrichment service."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class EnrichmentSource(str, Enum):
    """Sources of enrichment data."""

    CLEARBIT = "clearbit"
    APOLLO = "apollo"
    HUNTER = "hunter"
    LINKEDIN = "linkedin"
    NEWS_API = "news_api"
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"


class ContactInfo(BaseModel):
    """Verified contact information."""

    email: Optional[EmailStr] = None
    email_verified: bool = False
    email_verification_date: Optional[datetime] = None
    phone: Optional[str] = None
    phone_verified: bool = False
    mobile: Optional[str] = None
    work_phone: Optional[str] = None


class SocialProfiles(BaseModel):
    """Social media profile URLs."""

    linkedin_url: Optional[str] = None
    linkedin_username: Optional[str] = None
    twitter_url: Optional[str] = None
    twitter_username: Optional[str] = None
    github_url: Optional[str] = None
    personal_website: Optional[str] = None


class LinkedInInsights(BaseModel):
    """Insights extracted from LinkedIn profile."""

    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    connections_count: Optional[int] = None
    experience_years: Optional[int] = None
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    recent_posts: list[str] = Field(default_factory=list)
    mutual_connections: list[str] = Field(default_factory=list)


class ProspectBase(BaseModel):
    """Base prospect model with common fields."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def set_full_name(cls, v, info):
        """Auto-generate full name if not provided."""
        if v:
            return v
        first_name = info.data.get("first_name", "")
        last_name = info.data.get("last_name", "")
        if first_name or last_name:
            return f"{first_name or ''} {last_name or ''}".strip()
        return None


class ProspectCreate(ProspectBase):
    """Model for creating a new prospect for enrichment."""

    pass


class ProspectUpdate(BaseModel):
    """Model for updating prospect data."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None


class Prospect(ProspectBase):
    """Full prospect model with all fields."""

    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enriched_at: Optional[datetime] = None
    enrichment_sources: list[EnrichmentSource] = Field(default_factory=list)


class ProspectEnriched(Prospect):
    """Enriched prospect with all gathered data."""

    # Contact information
    contact_info: ContactInfo = Field(default_factory=ContactInfo)

    # Social profiles
    social_profiles: SocialProfiles = Field(default_factory=SocialProfiles)

    # LinkedIn insights
    linkedin_insights: Optional[LinkedInInsights] = None

    # Professional details
    seniority_level: Optional[str] = None  # e.g., "VP", "Director", "Manager", "IC"
    department: Optional[str] = None  # e.g., "Sales", "Engineering", "Marketing"
    role_function: Optional[str] = None  # e.g., "Sales Leader", "Technical IC"

    # Company association
    company_id: Optional[str] = None

    # Engagement signals
    recent_news_mentions: list[dict] = Field(default_factory=list)
    recent_activity: list[dict] = Field(default_factory=list)

    # Data quality
    enrichment_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    last_verified: Optional[datetime] = None

    # HubSpot mapping
    hubspot_contact_id: Optional[str] = None
    hubspot_mapped: bool = False
    hubspot_field_mapping: dict = Field(default_factory=dict)


class ProspectBulkImport(BaseModel):
    """Model for bulk prospect import from CSV or event lists."""

    prospects: list[ProspectCreate]
    source: str = "csv_import"
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    auto_enrich: bool = True
    sync_to_hubspot: bool = False


class ProspectBulkImportResult(BaseModel):
    """Result of bulk prospect import operation."""

    total_records: int
    successful: int
    failed: int
    duplicates: int
    enriched: int
    errors: list[dict] = Field(default_factory=list)
    prospects: list[ProspectEnriched] = Field(default_factory=list)


class EnrichmentRequest(BaseModel):
    """Request model for prospect enrichment."""

    prospect: ProspectCreate
    include_company: bool = True
    include_linkedin: bool = True
    include_news: bool = True
    include_contact_verification: bool = True
    sync_to_hubspot: bool = False


class EnrichmentResult(BaseModel):
    """Result of enrichment operation."""

    success: bool
    prospect: Optional[ProspectEnriched] = None
    company: Optional[dict] = None  # Will be CompanyEnriched when imported
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources_used: list[EnrichmentSource] = Field(default_factory=list)
    enrichment_duration_ms: int = 0
