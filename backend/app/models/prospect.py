<<<<<<< HEAD
<<<<<<< HEAD
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
=======
"""Prospect and Company models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Boolean

from .base import BaseDBModel, BaseModel, TimestampedSchema


class ProspectStatus(str, Enum):
    """Status of a prospect."""
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3

    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
<<<<<<< HEAD
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
=======
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    CHURNED = "churned"


class CompanySize(str, Enum):
    """Company size classification."""

    STARTUP = "startup"  # 1-10
    SMALL = "small"  # 11-50
    MID_MARKET = "mid_market"  # 51-500
    ENTERPRISE = "enterprise"  # 501-5000
    LARGE_ENTERPRISE = "large_enterprise"  # 5000+


class Company(BaseDBModel):
    """Company/account model."""

    __tablename__ = "companies"

    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True)
    industry = Column(String(100))
    size = Column(SQLEnum(CompanySize))
    employee_count = Column(Integer)
    annual_revenue = Column(String(50))
    funding_stage = Column(String(50))
    funding_amount = Column(String(50))
    tech_stack = Column(JSON, default=list)
    linkedin_url = Column(String(500))
    website = Column(String(500))
    description = Column(Text)
    headquarters = Column(String(255))

    # CRM integration
    hubspot_id = Column(String(100))

    # Enrichment metadata
    enriched_at = Column(String(50))
    enrichment_source = Column(String(100))

    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


class Prospect(BaseDBModel):
    """Individual prospect/contact model."""
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3

    __tablename__ = "prospects"

    # Basic info
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/prospect-enrichment-service-01JExTPwjSsxpVLfgBPfwBrE
=======
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    title = Column(String(255))
    department = Column(String(100))
    linkedin_url = Column(String(500))

    # Status
    status = Column(SQLEnum(ProspectStatus), default=ProspectStatus.NEW)
    is_decision_maker = Column(Boolean, default=False)
    is_champion = Column(Boolean, default=False)

    # Company association
    company_id = Column(String(36), ForeignKey("companies.id"))

    # CRM integration
    hubspot_id = Column(String(100))

    # Enrichment data
    enriched_at = Column(String(50))
    enrichment_data = Column(JSON, default=dict)

    # Notes and context
    notes = Column(Text)
    tags = Column(JSON, default=list)

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


# Pydantic Schemas
class CompanySchema(TimestampedSchema):
    """Company response schema."""

    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[CompanySize] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    funding_stage: Optional[str] = None
    funding_amount: Optional[str] = None
    tech_stack: List[str] = []
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None
    hubspot_id: Optional[str] = None
    organization_id: str


class ProspectSchema(TimestampedSchema):
    """Prospect response schema."""

    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: ProspectStatus
    is_decision_maker: bool = False
    is_champion: bool = False
    company_id: Optional[str] = None
    hubspot_id: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    user_id: Optional[str] = None
    organization_id: str
    company: Optional[CompanySchema] = None


class ProspectCreate(BaseModel):
    """Prospect creation schema."""

    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_id: Optional[str] = None
    status: ProspectStatus = ProspectStatus.NEW
    is_decision_maker: bool = False
    is_champion: bool = False
    tags: List[str] = []


class ProspectExport(BaseModel):
    """Prospect export data format (matches HubSpot import format)."""

    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: str
    is_decision_maker: bool = False
    tags: str = ""  # Comma-separated for CSV
    created_at: str


class ProspectImportRow(BaseModel):
    """Single row for prospect import with field mapping."""

    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3
