"""
LinkedIn API Routes

FastAPI routes for LinkedIn integration including:
- Profile enrichment endpoints
- Company enrichment endpoints
- Outreach tracking endpoints
- Connection status tracking
- Activity monitoring
- Campaign management
- Analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field

# Import models
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.linkedin import (
    LinkedInProfile,
    LinkedInProfileSummary,
    LinkedInCompany,
    OutreachActivity,
    OutreachCampaign,
    LinkedInActivity,
    ConnectionRecord,
    ConnectionStatus,
    OutreachType,
    OutreachStatus,
    ActivityType,
    ProfileEnrichmentRequest,
    CompanyEnrichmentRequest,
    BulkEnrichmentRequest,
    EnrichmentResponse,
    BulkEnrichmentResponse,
    ProfileMatchRequest,
    ProfileMatchResponse,
    OutreachTrackingRequest,
)
from integrations.linkedin import LinkedInService
from integrations.linkedin.service import get_linkedin_service

# Create router
router = APIRouter(
    prefix="/linkedin",
    tags=["linkedin"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"},
        429: {"description": "Rate limit exceeded"},
    },
)


# ==================== Dependencies ====================

async def get_service() -> LinkedInService:
    """Dependency to get LinkedIn service"""
    return get_linkedin_service()


async def get_current_user_id() -> str:
    """
    Dependency to get current user ID.
    Replace with actual auth implementation.
    """
    # TODO: Implement actual authentication
    return "user_001"


# ==================== Request/Response Models ====================

class EnrichProfileRequest(BaseModel):
    """API request for profile enrichment"""
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    force_refresh: bool = Field(False, description="Bypass cache")
    include_experiences: bool = Field(True, description="Include work history")
    include_education: bool = Field(True, description="Include education")
    include_skills: bool = Field(True, description="Include skills")


class EnrichCompanyRequest(BaseModel):
    """API request for company enrichment"""
    linkedin_url: str = Field(..., description="LinkedIn company URL")
    force_refresh: bool = Field(False, description="Bypass cache")
    include_key_employees: bool = Field(False, description="Include key employees")


class BulkEnrichRequest(BaseModel):
    """API request for bulk enrichment"""
    linkedin_urls: List[str] = Field(..., description="List of LinkedIn URLs")
    force_refresh: bool = Field(False, description="Bypass cache")


class TrackOutreachRequest(BaseModel):
    """API request for tracking outreach"""
    prospect_linkedin_url: str = Field(..., description="Prospect's LinkedIn URL")
    outreach_type: OutreachType = Field(..., description="Type of outreach")
    message_content: Optional[str] = Field(None, description="Message content")
    subject: Optional[str] = Field(None, description="Subject line (for InMails)")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    is_sales_navigator: bool = Field(False, description="Via Sales Navigator")


class UpdateOutreachStatusRequest(BaseModel):
    """API request for updating outreach status"""
    status: OutreachStatus = Field(..., description="New status")
    response_content: Optional[str] = Field(None, description="Response content")


class UpdateConnectionStatusRequest(BaseModel):
    """API request for updating connection status"""
    prospect_linkedin_url: str = Field(..., description="Prospect's LinkedIn URL")
    status: ConnectionStatus = Field(..., description="New connection status")
    note: Optional[str] = Field(None, description="Note about the connection")


class CreateCampaignRequest(BaseModel):
    """API request for creating a campaign"""
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    target_profiles: Optional[List[str]] = Field(None, description="Target LinkedIn URLs")
    message_templates: Optional[List[str]] = Field(None, description="Message templates")


class RecordActivityRequest(BaseModel):
    """API request for recording prospect activity"""
    profile_linkedin_url: str = Field(..., description="Prospect's LinkedIn URL")
    activity_type: ActivityType = Field(..., description="Type of activity")
    content_text: Optional[str] = Field(None, description="Activity content")
    activity_url: Optional[str] = Field(None, description="URL to the activity")
    activity_date: Optional[datetime] = Field(None, description="When activity occurred")
    # For job changes
    old_title: Optional[str] = Field(None, description="Previous job title")
    old_company: Optional[str] = Field(None, description="Previous company")
    new_title: Optional[str] = Field(None, description="New job title")
    new_company: Optional[str] = Field(None, description="New company")


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


# ==================== Profile Enrichment Endpoints ====================

@router.post("/profiles/enrich", response_model=EnrichmentResponse)
async def enrich_profile(
    request: EnrichProfileRequest,
    service: LinkedInService = Depends(get_service),
):
    """
    Enrich a LinkedIn profile with full data.

    Returns profile information including:
    - Basic info (name, headline, location)
    - Work experience
    - Education
    - Skills
    - Contact information (if available)
    """
    enrichment_request = ProfileEnrichmentRequest(
        linkedin_url=request.linkedin_url,
        force_refresh=request.force_refresh,
        include_experiences=request.include_experiences,
        include_education=request.include_education,
        include_skills=request.include_skills,
    )

    response = await service.enrich_profile(enrichment_request)

    if not response.success:
        raise HTTPException(
            status_code=404 if "not found" in (response.error_message or "").lower() else 400,
            detail=response.error_message,
        )

    return response


@router.post("/profiles/enrich/bulk", response_model=BulkEnrichmentResponse)
async def bulk_enrich_profiles(
    request: BulkEnrichRequest,
    background_tasks: BackgroundTasks,
    service: LinkedInService = Depends(get_service),
):
    """
    Enrich multiple LinkedIn profiles.

    Rate-limited and processed in batches.
    Large requests may be processed in the background.
    """
    if len(request.linkedin_urls) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 URLs per request",
        )

    enrichment_request = BulkEnrichmentRequest(
        linkedin_urls=request.linkedin_urls,
        force_refresh=request.force_refresh,
    )

    return await service.bulk_enrich_profiles(enrichment_request)


@router.get("/profiles/{linkedin_username}", response_model=EnrichmentResponse)
async def get_profile(
    linkedin_username: str,
    force_refresh: bool = Query(False),
    service: LinkedInService = Depends(get_service),
):
    """
    Get a LinkedIn profile by username.

    Example: /profiles/johndoe
    """
    linkedin_url = f"https://www.linkedin.com/in/{linkedin_username}"

    enrichment_request = ProfileEnrichmentRequest(
        linkedin_url=linkedin_url,
        force_refresh=force_refresh,
    )

    response = await service.enrich_profile(enrichment_request)

    if not response.success:
        raise HTTPException(status_code=404, detail=response.error_message)

    return response


# ==================== Company Enrichment Endpoints ====================

@router.post("/companies/enrich", response_model=EnrichmentResponse)
async def enrich_company(
    request: EnrichCompanyRequest,
    service: LinkedInService = Depends(get_service),
):
    """
    Enrich a LinkedIn company page with full data.

    Returns company information including:
    - Basic info (name, description, website)
    - Size and employee count
    - Industry and specialties
    - Headquarters location
    - Key employees (optional)
    """
    enrichment_request = CompanyEnrichmentRequest(
        linkedin_url=request.linkedin_url,
        force_refresh=request.force_refresh,
        include_key_employees=request.include_key_employees,
    )

    response = await service.enrich_company(enrichment_request)

    if not response.success:
        raise HTTPException(
            status_code=404 if "not found" in (response.error_message or "").lower() else 400,
            detail=response.error_message,
        )

    return response


@router.get("/companies/{company_slug}", response_model=EnrichmentResponse)
async def get_company(
    company_slug: str,
    force_refresh: bool = Query(False),
    service: LinkedInService = Depends(get_service),
):
    """
    Get a LinkedIn company by slug.

    Example: /companies/acme-corporation
    """
    linkedin_url = f"https://www.linkedin.com/company/{company_slug}"

    enrichment_request = CompanyEnrichmentRequest(
        linkedin_url=linkedin_url,
        force_refresh=force_refresh,
    )

    response = await service.enrich_company(enrichment_request)

    if not response.success:
        raise HTTPException(status_code=404, detail=response.error_message)

    return response


# ==================== Outreach Tracking Endpoints ====================

@router.post("/outreach/track", response_model=OutreachActivity)
async def track_outreach(
    request: TrackOutreachRequest,
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    Track a new outreach activity.

    Track InMails, connection requests, messages, and other
    LinkedIn outreach activities.
    """
    try:
        activity = await service.track_outreach(
            prospect_linkedin_url=request.prospect_linkedin_url,
            outreach_type=request.outreach_type,
            message_content=request.message_content,
            subject=request.subject,
            campaign_id=request.campaign_id,
            user_id=user_id,
            is_sales_navigator=request.is_sales_navigator,
        )
        return activity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/outreach/{activity_id}/status", response_model=OutreachActivity)
async def update_outreach_status(
    activity_id: str,
    request: UpdateOutreachStatusRequest,
    service: LinkedInService = Depends(get_service),
):
    """
    Update the status of an outreach activity.

    Update when:
    - Message is delivered
    - Recipient reads the message
    - Recipient replies
    - Connection request is accepted/declined
    """
    activity = await service.update_outreach_status(
        activity_id=activity_id,
        new_status=request.status,
        response_content=request.response_content,
    )

    if not activity:
        raise HTTPException(status_code=404, detail="Outreach activity not found")

    return activity


@router.get("/outreach", response_model=List[OutreachActivity])
async def list_outreach_activities(
    prospect_linkedin_url: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    outreach_type: Optional[OutreachType] = Query(None),
    limit: int = Query(50, le=200),
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    List outreach activities with optional filters.
    """
    return await service.get_outreach_history(
        prospect_linkedin_url=prospect_linkedin_url,
        campaign_id=campaign_id,
        user_id=user_id,
        outreach_type=outreach_type,
        limit=limit,
    )


@router.get("/outreach/analytics")
async def get_outreach_analytics(
    campaign_id: Optional[str] = Query(None),
    days: int = Query(30, le=365),
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    Get outreach analytics and metrics.

    Returns:
    - Total outreach count
    - Breakdown by type
    - Breakdown by status
    - Reply rate
    - Acceptance rate
    """
    return await service.get_outreach_analytics(
        campaign_id=campaign_id,
        user_id=user_id,
        days=days,
    )


# ==================== Connection Tracking Endpoints ====================

@router.post("/connections/status", response_model=ConnectionRecord)
async def update_connection_status(
    request: UpdateConnectionStatusRequest,
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    Update connection status with a prospect.
    """
    try:
        record = await service.update_connection_status(
            prospect_linkedin_url=request.prospect_linkedin_url,
            new_status=request.status,
            note=request.note,
            user_id=user_id,
        )
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connections/status")
async def get_connection_status(
    prospect_linkedin_url: str = Query(...),
    service: LinkedInService = Depends(get_service),
):
    """
    Get current connection status with a prospect.
    """
    status = await service.get_connection_status(prospect_linkedin_url)
    return {"status": status}


@router.get("/connections/history", response_model=List[ConnectionRecord])
async def get_connection_history(
    prospect_linkedin_url: str = Query(...),
    service: LinkedInService = Depends(get_service),
):
    """
    Get connection status history for a prospect.
    """
    return await service.get_connection_history(prospect_linkedin_url)


# ==================== Campaign Management Endpoints ====================

@router.post("/campaigns", response_model=OutreachCampaign)
async def create_campaign(
    request: CreateCampaignRequest,
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    Create a new outreach campaign.
    """
    return await service.create_campaign(
        name=request.name,
        description=request.description,
        target_profiles=request.target_profiles,
        message_templates=request.message_templates,
        user_id=user_id,
    )


@router.get("/campaigns", response_model=List[OutreachCampaign])
async def list_campaigns(
    active_only: bool = Query(False),
    user_id: str = Depends(get_current_user_id),
    service: LinkedInService = Depends(get_service),
):
    """
    List all campaigns.
    """
    return await service.list_campaigns(
        user_id=user_id,
        active_only=active_only,
    )


@router.get("/campaigns/{campaign_id}", response_model=OutreachCampaign)
async def get_campaign(
    campaign_id: str,
    service: LinkedInService = Depends(get_service),
):
    """
    Get a campaign by ID.
    """
    campaign = await service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.patch("/campaigns/{campaign_id}", response_model=OutreachCampaign)
async def update_campaign(
    campaign_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    service: LinkedInService = Depends(get_service),
):
    """
    Update a campaign.
    """
    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if is_active is not None:
        updates["is_active"] = is_active

    campaign = await service.update_campaign(campaign_id, **updates)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


# ==================== Activity Monitoring Endpoints ====================

@router.post("/activities", response_model=LinkedInActivity)
async def record_activity(
    request: RecordActivityRequest,
    service: LinkedInService = Depends(get_service),
):
    """
    Record a LinkedIn activity from a prospect.

    Track posts, job changes, promotions, etc.
    """
    try:
        activity = await service.record_activity(
            profile_linkedin_url=request.profile_linkedin_url,
            activity_type=request.activity_type,
            content_text=request.content_text,
            activity_url=request.activity_url,
            activity_date=request.activity_date,
            old_title=request.old_title,
            old_company=request.old_company,
            new_title=request.new_title,
            new_company=request.new_company,
        )
        return activity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activities", response_model=List[LinkedInActivity])
async def list_activities(
    prospect_linkedin_url: str = Query(...),
    activity_type: Optional[ActivityType] = Query(None),
    since_days: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    service: LinkedInService = Depends(get_service),
):
    """
    Get activities for a prospect.
    """
    from datetime import timedelta

    since = None
    if since_days:
        since = datetime.now() - timedelta(days=since_days)

    activity_types = [activity_type] if activity_type else None

    return await service.get_prospect_activities(
        profile_linkedin_url=prospect_linkedin_url,
        activity_types=activity_types,
        since=since,
        limit=limit,
    )


@router.get("/activities/job-changes", response_model=List[LinkedInActivity])
async def get_job_changes(
    since_days: int = Query(30, le=365),
    limit: int = Query(50, le=200),
    service: LinkedInService = Depends(get_service),
):
    """
    Get recent job changes across all tracked prospects.

    Useful for identifying sales opportunities.
    """
    from datetime import timedelta

    since = datetime.now() - timedelta(days=since_days)

    return await service.get_job_changes(since=since, limit=limit)


# ==================== Profile Matching Endpoints ====================

@router.post("/profiles/match", response_model=ProfileMatchResponse)
async def match_profile_to_prospect(
    request: ProfileMatchRequest,
    service: LinkedInService = Depends(get_service),
):
    """
    Match a LinkedIn profile to an existing prospect.

    Uses email, name, and company matching to find correlations.
    """
    return await service.match_profile_to_prospect(request)


# ==================== Search Endpoints ====================

@router.get("/search/profiles", response_model=List[LinkedInProfileSummary])
async def search_profiles(
    query: Optional[str] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(10, le=100),
    service: LinkedInService = Depends(get_service),
):
    """
    Search for LinkedIn profiles.

    Note: Requires enrichment provider with search capability.
    """
    results = await service.client.search_profiles(
        query=query,
        first_name=first_name,
        last_name=last_name,
        company=company,
        title=title,
        location=location,
        limit=limit,
    )

    return [
        LinkedInProfileSummary(
            linkedin_url=r.get("linkedin_url", ""),
            first_name=r.get("first_name", ""),
            last_name=r.get("last_name", ""),
            headline=r.get("headline"),
            current_company=r.get("company"),
            location=r.get("location"),
            profile_picture_url=r.get("profile_picture_url"),
        )
        for r in results
    ]


# ==================== Health Check ====================

@router.get("/health")
async def health_check(
    service: LinkedInService = Depends(get_service),
):
    """
    Health check endpoint for LinkedIn integration.
    """
    rate_limit_status = service.client.rate_limiter.check("default")

    return {
        "status": "healthy",
        "service": "linkedin_integration",
        "rate_limit": rate_limit_status,
        "cache_enabled": service.client.cache_enabled,
        "enrichment_provider": service.client.enrichment_provider,
    }
