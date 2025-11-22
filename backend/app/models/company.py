"""Company data models for enrichment service."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CompanySize(str, Enum):
    """Company size categories."""

    STARTUP = "1-10"
    SMALL = "11-50"
    MEDIUM = "51-200"
    LARGE = "201-500"
    ENTERPRISE = "501-1000"
    LARGE_ENTERPRISE = "1001-5000"
    MEGA_ENTERPRISE = "5000+"


class FundingStage(str, Enum):
    """Company funding stages."""

    BOOTSTRAPPED = "bootstrapped"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"
    PUBLIC = "public"
    ACQUIRED = "acquired"
    UNKNOWN = "unknown"


class FundingRound(BaseModel):
    """Individual funding round details."""

    stage: FundingStage
    amount: Optional[float] = None
    currency: str = "USD"
    date: Optional[datetime] = None
    investors: list[str] = Field(default_factory=list)
    lead_investor: Optional[str] = None


class FundingInfo(BaseModel):
    """Company funding information."""

    total_raised: Optional[float] = None
    currency: str = "USD"
    last_funding_stage: Optional[FundingStage] = None
    last_funding_date: Optional[datetime] = None
    last_funding_amount: Optional[float] = None
    funding_rounds: list[FundingRound] = Field(default_factory=list)
    investors: list[str] = Field(default_factory=list)
    is_funded: bool = False


class TechStack(BaseModel):
    """Company technology stack information."""

    technologies: list[str] = Field(default_factory=list)
    categories: dict[str, list[str]] = Field(default_factory=dict)
    # Categories like: {"crm": ["Salesforce"], "marketing": ["HubSpot", "Marketo"]}
    cloud_providers: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)


class CompanyLocation(BaseModel):
    """Company location details."""

    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    formatted_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class CompanySocialProfiles(BaseModel):
    """Company social media profiles."""

    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    github_url: Optional[str] = None
    youtube_url: Optional[str] = None


class CompanyBase(BaseModel):
    """Base company model with common fields."""

    name: str
    domain: Optional[str] = None
    website: Optional[str] = None


class CompanyCreate(CompanyBase):
    """Model for creating a new company for enrichment."""

    pass


class CompanyUpdate(BaseModel):
    """Model for updating company data."""

    name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None


class Company(CompanyBase):
    """Full company model with all fields."""

    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enriched_at: Optional[datetime] = None


class CompanyEnriched(Company):
    """Enriched company with all gathered data."""

    # Basic info
    legal_name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    founded_year: Optional[int] = None

    # Industry and categorization
    industry: Optional[str] = None
    industry_group: Optional[str] = None
    sub_industry: Optional[str] = None
    sector: Optional[str] = None
    sic_codes: list[str] = Field(default_factory=list)
    naics_codes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Size and revenue
    company_size: Optional[CompanySize] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    annual_revenue: Optional[float] = None
    revenue_range: Optional[str] = None
    market_cap: Optional[float] = None

    # Location
    headquarters: Optional[CompanyLocation] = None
    locations: list[CompanyLocation] = Field(default_factory=list)
    geo_regions: list[str] = Field(default_factory=list)

    # Funding
    funding_info: FundingInfo = Field(default_factory=FundingInfo)

    # Tech stack
    tech_stack: TechStack = Field(default_factory=TechStack)

    # Social profiles
    social_profiles: CompanySocialProfiles = Field(default_factory=CompanySocialProfiles)

    # Company type
    company_type: Optional[str] = None  # e.g., "public", "private", "nonprofit"
    stock_symbol: Optional[str] = None
    stock_exchange: Optional[str] = None

    # Key people
    ceo_name: Optional[str] = None
    founders: list[str] = Field(default_factory=list)
    key_executives: list[dict] = Field(default_factory=list)

    # News and events
    recent_news: list[dict] = Field(default_factory=list)
    recent_events: list[dict] = Field(default_factory=list)
    press_releases: list[dict] = Field(default_factory=list)

    # Competitors and market position
    competitors: list[str] = Field(default_factory=list)
    market_position: Optional[str] = None

    # Data quality
    enrichment_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    last_verified: Optional[datetime] = None
    data_sources: list[str] = Field(default_factory=list)

    # HubSpot mapping
    hubspot_company_id: Optional[str] = None
    hubspot_mapped: bool = False
    hubspot_field_mapping: dict = Field(default_factory=dict)


class CompanySearchResult(BaseModel):
    """Company search result from enrichment sources."""

    company: CompanyEnriched
    match_confidence: float = Field(ge=0.0, le=1.0)
    source: str
    matched_on: list[str] = Field(default_factory=list)  # e.g., ["domain", "name"]


class NewsArticle(BaseModel):
    """News article related to a company or prospect."""

    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    topics: list[str] = Field(default_factory=list)
    mentions_company: bool = True
    mentions_person: Optional[str] = None
