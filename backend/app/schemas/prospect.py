"""Prospect and Company Pydantic schemas."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import EmailStr, Field, field_validator

from app.models.prospect import CompanySize, FundingStage, ProspectStatus
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


# ==================== Company Schemas ====================


class CompanyBase(BaseSchema):
    """Base company schema."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""

    sub_industry: Optional[str] = Field(None, max_length=100)
    size: Optional[CompanySize] = None
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[float] = Field(None, ge=0)
    funding_stage: Optional[FundingStage] = None
    total_funding: Optional[float] = Field(None, ge=0)
    founded_year: Optional[int] = Field(None, ge=1800)
    headquarters_city: Optional[str] = Field(None, max_length=100)
    headquarters_state: Optional[str] = Field(None, max_length=100)
    headquarters_country: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    tagline: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    tech_stack: Optional[List[str]] = None
    hubspot_id: Optional[str] = None
    salesforce_id: Optional[str] = None


class CompanyUpdate(BaseSchema):
    """Schema for updating a company."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    sub_industry: Optional[str] = Field(None, max_length=100)
    size: Optional[CompanySize] = None
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[float] = Field(None, ge=0)
    funding_stage: Optional[FundingStage] = None
    description: Optional[str] = None
    headquarters_city: Optional[str] = Field(None, max_length=100)
    headquarters_country: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    tech_stack: Optional[List[str]] = None


class CompanyResponse(CompanyBase, IDSchema, TimestampSchema):
    """Schema for company response."""

    sub_industry: Optional[str] = None
    size: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    funding_stage: Optional[str] = None
    total_funding: Optional[float] = None
    founded_year: Optional[int] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    headquarters_country: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    crunchbase_url: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    tools_used: Optional[List[str]] = None
    recent_news: Optional[List[dict]] = None
    recent_events: Optional[List[dict]] = None
    key_initiatives: Optional[List[str]] = None
    is_verified: bool
    last_enriched_at: Optional[datetime] = None
    hubspot_id: Optional[str] = None
    salesforce_id: Optional[str] = None

    @field_validator("tech_stack", "tools_used", "key_initiatives", "recent_news", "recent_events", mode="before")
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


# ==================== Prospect Schemas ====================


class ProspectBase(BaseSchema):
    """Base prospect schema."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class ProspectCreate(ProspectBase):
    """Schema for creating a prospect."""

    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    seniority: Optional[str] = Field(None, max_length=50)
    status: ProspectStatus = ProspectStatus.NEW
    linkedin_url: Optional[str] = Field(None, max_length=500)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    company_id: Optional[str] = None
    notes: Optional[str] = None
    hubspot_id: Optional[str] = None
    salesforce_id: Optional[str] = None


class ProspectUpdate(BaseSchema):
    """Schema for updating a prospect."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    seniority: Optional[str] = Field(None, max_length=50)
    status: Optional[ProspectStatus] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    company_id: Optional[str] = None
    notes: Optional[str] = None


class ProspectResponse(ProspectBase, IDSchema, TimestampSchema):
    """Schema for prospect response."""

    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    status: str
    lead_score: Optional[int] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    avatar_url: Optional[str] = None
    work_history: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    interests: Optional[List[str]] = None
    recent_posts: Optional[List[dict]] = None
    notes: Optional[str] = None
    pain_points: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    is_verified: bool
    last_enriched_at: Optional[datetime] = None
    last_contacted_at: Optional[datetime] = None
    company_id: Optional[str] = None
    hubspot_id: Optional[str] = None
    salesforce_id: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get prospect's full name."""
        return f"{self.first_name} {self.last_name}"

    @field_validator("work_history", "education", "recent_posts", "interests", "pain_points", "goals", mode="before")
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class ProspectWithCompany(ProspectResponse):
    """Prospect response with company details."""

    company: Optional[CompanyResponse] = None


class EnrichmentRequest(BaseSchema):
    """Request to enrich a prospect or company."""

    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    force_refresh: bool = False


class EnrichmentResponse(BaseSchema):
    """Response from enrichment."""

    prospect: Optional[ProspectResponse] = None
    company: Optional[CompanyResponse] = None
    enrichment_sources: List[str]
    processing_time_ms: int
