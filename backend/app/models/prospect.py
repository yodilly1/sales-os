"""Prospect and Company models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Boolean

from .base import BaseDBModel, BaseModel, TimestampedSchema


class ProspectStatus(str, Enum):
    """Status of a prospect."""

    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
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

    __tablename__ = "prospects"

    # Basic info
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
