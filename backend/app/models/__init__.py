"""
Sales OS Data Models

This module contains all Pydantic schemas and SQLAlchemy models.
"""

from .linkedin import (
    # Enums
    ConnectionStatus,
    OutreachType,
    OutreachStatus,
    CompanySize,
    ActivityType,
    # Profile Models
    LinkedInProfile,
    LinkedInProfileSummary,
    LinkedInExperience,
    LinkedInEducation,
    LinkedInSkill,
    LinkedInCertification,
    # Company Models
    LinkedInCompany,
    # Outreach Models
    OutreachActivity,
    OutreachCampaign,
    # Activity Models
    LinkedInActivity,
    ConnectionRecord,
    # Request/Response Models
    ProfileEnrichmentRequest,
    CompanyEnrichmentRequest,
    BulkEnrichmentRequest,
    EnrichmentResponse,
    BulkEnrichmentResponse,
    ProfileMatchRequest,
    ProfileMatchResponse,
    OutreachTrackingRequest,
    # Utility Functions
    normalize_linkedin_url,
    normalize_linkedin_company_url,
    extract_linkedin_username,
    extract_company_slug,
)

__all__ = [
    # Enums
    "ConnectionStatus",
    "OutreachType",
    "OutreachStatus",
    "CompanySize",
    "ActivityType",
    # Profile Models
    "LinkedInProfile",
    "LinkedInProfileSummary",
    "LinkedInExperience",
    "LinkedInEducation",
    "LinkedInSkill",
    "LinkedInCertification",
    # Company Models
    "LinkedInCompany",
    # Outreach Models
    "OutreachActivity",
    "OutreachCampaign",
    # Activity Models
    "LinkedInActivity",
    "ConnectionRecord",
    # Request/Response Models
    "ProfileEnrichmentRequest",
    "CompanyEnrichmentRequest",
    "BulkEnrichmentRequest",
    "EnrichmentResponse",
    "BulkEnrichmentResponse",
    "ProfileMatchRequest",
    "ProfileMatchResponse",
    "OutreachTrackingRequest",
    # Utility Functions
    "normalize_linkedin_url",
    "normalize_linkedin_company_url",
    "extract_linkedin_username",
    "extract_company_slug",
]
