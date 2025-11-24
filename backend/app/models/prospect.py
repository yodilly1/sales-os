"""Prospect and Company models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.transcript import Call


class CompanySize(str, Enum):
    """Company size categories."""

    STARTUP = "startup"  # 1-10
    SMALL = "small"  # 11-50
    MEDIUM = "medium"  # 51-200
    LARGE = "large"  # 201-1000
    ENTERPRISE = "enterprise"  # 1000+


class FundingStage(str, Enum):
    """Company funding stages."""

    BOOTSTRAPPED = "bootstrapped"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"
    IPO = "ipo"
    PRIVATE_EQUITY = "private_equity"
    UNKNOWN = "unknown"


class ProspectStatus(str, Enum):
    """Prospect engagement status."""

    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CHURNED = "churned"


class Company(Base, TimestampMixin, SoftDeleteMixin):
    """Company model for prospect organizations."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Company details
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    funding_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_funding: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Location
    headquarters_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headquarters_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headquarters_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Description and overview
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Technology and tools (JSON arrays)
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Social and public presence
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitter_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crunchbase_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Enrichment data (JSON)
    enrichment_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recent_news: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    recent_events: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    key_initiatives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Verification and sync
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # External IDs
    hubspot_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    salesforce_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    prospects: Mapped[List["Prospect"]] = relationship(
        "Prospect", back_populates="company", cascade="all, delete-orphan"
    )
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="company")
    content: Mapped[List["Content"]] = relationship("Content", back_populates="company")

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


class Prospect(Base, TimestampMixin, SoftDeleteMixin):
    """Prospect model for individual contacts."""

    __tablename__ = "prospects"

    # Basic info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Professional info
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seniority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default=ProspectStatus.NEW.value, nullable=False)
    lead_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Social profiles
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitter_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Enrichment data (JSON)
    enrichment_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    education: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    recent_posts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Notes and context
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pain_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Verification and sync
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # External IDs
    hubspot_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    salesforce_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Foreign Keys
    company_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="prospects")
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="prospect")
    content: Mapped[List["Content"]] = relationship("Content", back_populates="prospect")

    @property
    def full_name(self) -> str:
        """Get prospect's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Prospect {self.full_name}>"


# ==================== Pydantic Models for Enrichment Service ====================

from pydantic import BaseModel, EmailStr, Field


class EnrichmentSource(str, Enum):
    """Data source for enrichment."""

    CLEARBIT = "clearbit"
    APOLLO = "apollo"
    HUNTER = "hunter"
    LINKEDIN = "linkedin"
    NEWS = "news"
    WEB_RESEARCH = "web_research"
    MANUAL = "manual"


class ContactInfo(BaseModel):
    """Contact information model."""

    email: Optional[str] = None
    email_verified: bool = False
    email_verification_date: Optional[datetime] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None


class SocialProfiles(BaseModel):
    """Social media profiles."""

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
    skills: List[str] = Field(default_factory=list)
    experience: List[dict] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)


class ProspectCreate(BaseModel):
    """Model for creating a prospect for enrichment."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None


class ProspectEnriched(BaseModel):
    """Enriched prospect with all gathered data."""

    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_id: Optional[str] = None

    # Professional details
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    role_function: Optional[str] = None

    # Contact and social
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    social_profiles: SocialProfiles = Field(default_factory=SocialProfiles)
    linkedin_insights: Optional[LinkedInInsights] = None

    # News and mentions
    recent_news_mentions: List[dict] = Field(default_factory=list)

    # Web research data
    web_research: Optional[dict] = None
    ai_insights: Optional[dict] = None

    # Data quality
    enrichment_sources: List[EnrichmentSource] = Field(default_factory=list)
    enriched_at: Optional[datetime] = None
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    enrichment_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_verified: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EnrichmentRequest(BaseModel):
    """Request for enrichment."""

    email: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    include_company: bool = True
    include_linkedin: bool = True
    include_news: bool = True
    include_contact_verification: bool = True
    include_web_research: bool = False
    include_ai_insights: bool = False


class EnrichmentResult(BaseModel):
    """Result from enrichment."""

    success: bool
    prospect: Optional[ProspectEnriched] = None
    company: Optional[dict] = None
    web_research: Optional[dict] = None
    ai_insights: Optional[dict] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sources_used: List[EnrichmentSource] = Field(default_factory=list)
    enrichment_duration_ms: int = 0


class ProspectBulkImport(BaseModel):
    """Model for bulk import prospect data."""

    prospects: List[ProspectCreate]
    source: str = "csv_import"
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None


class ProspectBulkImportResult(BaseModel):
    """Result from bulk import."""

    total_rows: int
    successful: int
    failed: int
    errors: List[dict] = Field(default_factory=list)
    prospects: List[ProspectEnriched] = Field(default_factory=list)
