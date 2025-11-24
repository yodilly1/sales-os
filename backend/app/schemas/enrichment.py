"""Pydantic schemas for prospect enrichment service."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class EnrichmentSource(str, Enum):
    """Enrichment data source identifiers."""

    CLEARBIT = "clearbit"
    APOLLO = "apollo"
    HUNTER = "hunter"
    LINKEDIN = "linkedin"
    NEWS = "news"
    NEWS_API = "news_api"
    MANUAL = "manual"
    INTERNAL = "internal"


class ContactInfo(BaseModel):
    """Contact information for a prospect."""

    email: Optional[str] = None
    email_verified: bool = False
    email_verification_date: Optional[datetime] = None
    phone: Optional[str] = None
    phone_verified: bool = False
    mobile: Optional[str] = None


class SocialProfiles(BaseModel):
    """Social media profiles for a prospect."""

    linkedin_url: Optional[str] = None
    linkedin_username: Optional[str] = None
    twitter_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    github_url: Optional[str] = None
    facebook_url: Optional[str] = None


class LinkedInInsights(BaseModel):
    """LinkedIn profile insights."""

    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    connections_count: Optional[int] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    recommendations_count: Optional[int] = None


class ProspectCreate(BaseModel):
    """Schema for creating a prospect for enrichment.

    All fields are optional to support partial data input.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


class ProspectEnriched(BaseModel):
    """Enriched prospect with data from all sources."""

    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_id: Optional[str] = None

    # Professional info
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    role_function: Optional[str] = None

    # Contact info
    contact_info: ContactInfo = Field(default_factory=ContactInfo)

    # Social profiles
    social_profiles: SocialProfiles = Field(default_factory=SocialProfiles)

    # LinkedIn insights
    linkedin_insights: Optional[LinkedInInsights] = None

    # News mentions
    recent_news_mentions: list[dict] = Field(default_factory=list)

    # Enrichment metadata
    enrichment_sources: list[EnrichmentSource] = Field(default_factory=list)
    enriched_at: Optional[datetime] = None
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    enrichment_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_verified: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # CRM mapping
    hubspot_contact_id: Optional[str] = None
    hubspot_mapped: bool = False


class EnrichmentRequest(BaseModel):
    """Request to enrich a prospect or company."""

    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    force_refresh: bool = False


class EnrichmentResult(BaseModel):
    """Result from an enrichment operation."""

    success: bool = True
    prospect: Optional[ProspectEnriched] = None
    company: Optional[dict[str, Any]] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources_used: list[EnrichmentSource] = Field(default_factory=list)
    enrichment_duration_ms: int = 0


class ProspectBulkImport(BaseModel):
    """Request for bulk prospect import."""

    prospects: list[ProspectCreate]
    source: str = "csv_import"
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    auto_enrich: bool = True
    sync_to_hubspot: bool = False


class ProspectBulkImportResult(BaseModel):
    """Result from bulk prospect import."""

    total_records: int = 0
    successful: int = 0
    failed: int = 0
    duplicates: int = 0
    enriched: int = 0
    errors: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    prospects: list[ProspectEnriched] = Field(default_factory=list)


# Frontend-compatible response models

class SingleLookupRequest(BaseModel):
    """Request for single prospect lookup (frontend compatible)."""

    email: Optional[EmailStr] = None
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    linkedinUrl: Optional[str] = None
    company_domain: Optional[str] = None


class ProspectResponse(BaseModel):
    """Frontend-compatible prospect response."""

    id: str
    name: str
    email: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    companyId: Optional[str] = None
    phone: Optional[str] = None
    linkedinUrl: Optional[str] = None
    location: Optional[str] = None
    enrichmentStatus: str = "pending"
    enrichmentData: Optional[dict] = None
    crmSyncStatus: str = "not_synced"
    crmId: Optional[str] = None
    lastEnrichedAt: Optional[str] = None
    createdAt: str
    updatedAt: str


class CompanyResponse(BaseModel):
    """Frontend-compatible company response."""

    id: str
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    employeeCount: Optional[int] = None
    revenue: Optional[str] = None
    funding: Optional[dict] = None
    techStack: Optional[list[str]] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedinUrl: Optional[str] = None
    description: Optional[str] = None
    logoUrl: Optional[str] = None
    lastEnrichedAt: Optional[str] = None
    createdAt: str
    updatedAt: str


class SingleLookupResponse(BaseModel):
    """Response for single prospect lookup (frontend compatible)."""

    success: bool
    prospect: Optional[ProspectResponse] = None
    company: Optional[CompanyResponse] = None
    error: Optional[str] = None
    message: Optional[str] = None
