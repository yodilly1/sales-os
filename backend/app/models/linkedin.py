"""
LinkedIn Models and Pydantic Schemas

This module defines the data models for LinkedIn integration including:
- Profile data structures
- Company data structures
- Connection tracking
- Outreach activity tracking
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re


# Enums
class ConnectionStatus(str, Enum):
    """LinkedIn connection status between user and prospect"""
    NOT_CONNECTED = "not_connected"
    PENDING_SENT = "pending_sent"
    PENDING_RECEIVED = "pending_received"
    CONNECTED = "connected"
    FOLLOWING = "following"


class OutreachType(str, Enum):
    """Types of LinkedIn outreach activities"""
    CONNECTION_REQUEST = "connection_request"
    INMAIL = "inmail"
    MESSAGE = "message"
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    PROFILE_VIEW = "profile_view"


class OutreachStatus(str, Enum):
    """Status of outreach activities"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class CompanySize(str, Enum):
    """Company size categories"""
    SELF_EMPLOYED = "1"
    SMALL_2_10 = "2-10"
    SMALL_11_50 = "11-50"
    MEDIUM_51_200 = "51-200"
    MEDIUM_201_500 = "201-500"
    LARGE_501_1000 = "501-1000"
    LARGE_1001_5000 = "1001-5000"
    ENTERPRISE_5001_10000 = "5001-10000"
    ENTERPRISE_10000_PLUS = "10000+"


class ActivityType(str, Enum):
    """Types of LinkedIn activities to monitor"""
    POST = "post"
    ARTICLE = "article"
    REACTION = "reaction"
    COMMENT = "comment"
    SHARE = "share"
    JOB_CHANGE = "job_change"
    PROMOTION = "promotion"
    WORK_ANNIVERSARY = "work_anniversary"
    NEW_CONNECTION = "new_connection"


# Base Models
class LinkedInExperience(BaseModel):
    """Work experience entry from LinkedIn profile"""
    title: str
    company_name: str
    company_linkedin_url: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False
    description: Optional[str] = None

    @property
    def duration_months(self) -> Optional[int]:
        """Calculate duration in months"""
        if not self.start_date:
            return None
        end = self.end_date or datetime.now()
        return (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)


class LinkedInEducation(BaseModel):
    """Education entry from LinkedIn profile"""
    school_name: str
    school_linkedin_url: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    activities: Optional[str] = None


class LinkedInSkill(BaseModel):
    """Skill entry from LinkedIn profile"""
    name: str
    endorsement_count: int = 0


class LinkedInCertification(BaseModel):
    """Certification entry from LinkedIn profile"""
    name: str
    issuing_organization: str
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


# Profile Models
class LinkedInProfile(BaseModel):
    """Complete LinkedIn profile data"""
    linkedin_id: Optional[str] = None
    linkedin_url: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    profile_picture_url: Optional[str] = None
    banner_image_url: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    current_company_linkedin_url: Optional[str] = None

    # Contact info (if available)
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    twitter_handle: Optional[str] = None

    # Network stats
    connections_count: Optional[int] = None
    followers_count: Optional[int] = None

    # Experience and education
    experiences: List[LinkedInExperience] = Field(default_factory=list)
    education: List[LinkedInEducation] = Field(default_factory=list)
    skills: List[LinkedInSkill] = Field(default_factory=list)
    certifications: List[LinkedInCertification] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    # Engagement metrics
    is_open_to_work: bool = False
    is_hiring: bool = False
    is_creator: bool = False

    # Connection status with our user
    connection_status: ConnectionStatus = ConnectionStatus.NOT_CONNECTED

    # Metadata
    last_enriched_at: Optional[datetime] = None
    enrichment_source: Optional[str] = None

    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin_url(cls, v: str) -> str:
        """Normalize and validate LinkedIn URL"""
        return normalize_linkedin_url(v)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def total_experience_years(self) -> float:
        """Calculate total years of experience"""
        total_months = sum(
            exp.duration_months or 0
            for exp in self.experiences
        )
        return round(total_months / 12, 1)


class LinkedInProfileSummary(BaseModel):
    """Condensed profile info for list views"""
    linkedin_url: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connection_status: ConnectionStatus = ConnectionStatus.NOT_CONNECTED


# Company Models
class LinkedInCompany(BaseModel):
    """LinkedIn company page data"""
    linkedin_id: Optional[str] = None
    linkedin_url: str
    name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySize] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None

    # Location
    headquarters_location: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_country: Optional[str] = None

    # Company details
    founded_year: Optional[int] = None
    company_type: Optional[str] = None  # Public, Private, Nonprofit, etc.
    specialties: List[str] = Field(default_factory=list)

    # Branding
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None

    # Social metrics
    followers_count: Optional[int] = None

    # Associated pages
    showcase_pages: List[str] = Field(default_factory=list)
    affiliated_companies: List[str] = Field(default_factory=list)

    # Key people (if available)
    key_employees: List[LinkedInProfileSummary] = Field(default_factory=list)

    # Metadata
    last_enriched_at: Optional[datetime] = None
    enrichment_source: Optional[str] = None

    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin_url(cls, v: str) -> str:
        """Normalize and validate LinkedIn company URL"""
        return normalize_linkedin_company_url(v)


# Outreach Models
class OutreachActivity(BaseModel):
    """Track individual outreach activities"""
    id: Optional[str] = None
    prospect_linkedin_url: str
    prospect_name: Optional[str] = None
    outreach_type: OutreachType
    status: OutreachStatus = OutreachStatus.PENDING

    # Content
    message_content: Optional[str] = None
    subject: Optional[str] = None  # For InMails

    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

    # Response tracking
    response_content: Optional[str] = None

    # Campaign association
    campaign_id: Optional[str] = None
    sequence_step: Optional[int] = None

    # Sales Navigator fields
    sales_navigator_activity_id: Optional[str] = None
    is_sales_navigator: bool = False

    # User tracking
    user_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OutreachCampaign(BaseModel):
    """Group related outreach activities into campaigns"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None

    # Campaign settings
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Targeting
    target_profiles: List[str] = Field(default_factory=list)  # LinkedIn URLs

    # Sequence
    message_templates: List[str] = Field(default_factory=list)
    delay_between_steps_days: int = 3

    # Stats
    total_prospects: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    replied_count: int = 0
    accepted_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None

    @property
    def reply_rate(self) -> float:
        """Calculate reply rate percentage"""
        if self.sent_count == 0:
            return 0.0
        return round((self.replied_count / self.sent_count) * 100, 2)

    @property
    def acceptance_rate(self) -> float:
        """Calculate connection acceptance rate"""
        if self.sent_count == 0:
            return 0.0
        return round((self.accepted_count / self.sent_count) * 100, 2)


# Activity Monitoring Models
class LinkedInActivity(BaseModel):
    """Track LinkedIn activities from prospects"""
    id: Optional[str] = None
    profile_linkedin_url: str
    activity_type: ActivityType

    # Content
    activity_url: Optional[str] = None
    content_text: Optional[str] = None
    media_url: Optional[str] = None

    # Engagement metrics
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0

    # For job changes/promotions
    old_title: Optional[str] = None
    old_company: Optional[str] = None
    new_title: Optional[str] = None
    new_company: Optional[str] = None

    # Timing
    activity_date: datetime
    discovered_at: datetime = Field(default_factory=datetime.now)

    # Alert settings
    is_alert_sent: bool = False
    alert_sent_at: Optional[datetime] = None


# Connection Tracking
class ConnectionRecord(BaseModel):
    """Track connection status changes over time"""
    id: Optional[str] = None
    prospect_linkedin_url: str
    prospect_name: Optional[str] = None

    # Status
    previous_status: ConnectionStatus
    new_status: ConnectionStatus
    changed_at: datetime = Field(default_factory=datetime.now)

    # Context
    connection_request_message: Optional[str] = None
    connection_note: Optional[str] = None

    # User tracking
    user_id: Optional[str] = None


# Request/Response Models
class ProfileEnrichmentRequest(BaseModel):
    """Request to enrich a LinkedIn profile"""
    linkedin_url: str
    force_refresh: bool = False
    include_experiences: bool = True
    include_education: bool = True
    include_skills: bool = True
    include_certifications: bool = False

    @field_validator('linkedin_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return normalize_linkedin_url(v)


class CompanyEnrichmentRequest(BaseModel):
    """Request to enrich a LinkedIn company"""
    linkedin_url: str
    force_refresh: bool = False
    include_key_employees: bool = False
    key_employee_limit: int = 10

    @field_validator('linkedin_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return normalize_linkedin_company_url(v)


class BulkEnrichmentRequest(BaseModel):
    """Request to enrich multiple profiles"""
    linkedin_urls: List[str]
    force_refresh: bool = False

    @field_validator('linkedin_urls')
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        return [normalize_linkedin_url(url) for url in v]


class EnrichmentResponse(BaseModel):
    """Response from enrichment operation"""
    success: bool
    profile: Optional[LinkedInProfile] = None
    company: Optional[LinkedInCompany] = None
    error_message: Optional[str] = None
    cached: bool = False
    enrichment_source: Optional[str] = None


class BulkEnrichmentResponse(BaseModel):
    """Response from bulk enrichment"""
    total_requested: int
    successful: int
    failed: int
    results: List[EnrichmentResponse]


class OutreachTrackingRequest(BaseModel):
    """Request to track an outreach activity"""
    prospect_linkedin_url: str
    outreach_type: OutreachType
    message_content: Optional[str] = None
    subject: Optional[str] = None
    campaign_id: Optional[str] = None


class ProfileMatchRequest(BaseModel):
    """Request to match a LinkedIn profile to a prospect"""
    linkedin_url: str
    prospect_id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None


class ProfileMatchResponse(BaseModel):
    """Response from profile matching"""
    matched: bool
    confidence_score: float
    prospect_id: Optional[str] = None
    profile: Optional[LinkedInProfileSummary] = None
    match_reasons: List[str] = Field(default_factory=list)


# Utility Functions
def normalize_linkedin_url(url: str) -> str:
    """
    Normalize a LinkedIn profile URL to standard format.
    Handles various LinkedIn URL formats:
    - https://www.linkedin.com/in/username
    - https://linkedin.com/in/username/
    - linkedin.com/in/username
    - /in/username
    """
    if not url:
        raise ValueError("LinkedIn URL cannot be empty")

    # Remove whitespace
    url = url.strip()

    # Extract username from various formats
    patterns = [
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/([^/?\s]+)',
        r'^/in/([^/?\s]+)',
        r'^in/([^/?\s]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            username = match.group(1)
            return f"https://www.linkedin.com/in/{username}"

    # If URL doesn't match patterns, assume it's just a username
    if '/' not in url and '.' not in url:
        return f"https://www.linkedin.com/in/{url}"

    raise ValueError(f"Invalid LinkedIn profile URL: {url}")


def normalize_linkedin_company_url(url: str) -> str:
    """
    Normalize a LinkedIn company URL to standard format.
    Handles various LinkedIn company URL formats:
    - https://www.linkedin.com/company/company-name
    - https://linkedin.com/company/company-name/
    - linkedin.com/company/company-name
    """
    if not url:
        raise ValueError("LinkedIn company URL cannot be empty")

    # Remove whitespace
    url = url.strip()

    # Extract company slug from various formats
    patterns = [
        r'(?:https?://)?(?:www\.)?linkedin\.com/company/([^/?\s]+)',
        r'^/company/([^/?\s]+)',
        r'^company/([^/?\s]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            company_slug = match.group(1)
            return f"https://www.linkedin.com/company/{company_slug}"

    # If URL doesn't match patterns, assume it's just a company slug
    if '/' not in url and '.' not in url:
        return f"https://www.linkedin.com/company/{url}"

    raise ValueError(f"Invalid LinkedIn company URL: {url}")


def extract_linkedin_username(url: str) -> Optional[str]:
    """Extract just the username from a LinkedIn URL"""
    try:
        normalized = normalize_linkedin_url(url)
        return normalized.split('/in/')[-1]
    except ValueError:
        return None


def extract_company_slug(url: str) -> Optional[str]:
    """Extract just the company slug from a LinkedIn URL"""
    try:
        normalized = normalize_linkedin_company_url(url)
        return normalized.split('/company/')[-1]
    except ValueError:
        return None
