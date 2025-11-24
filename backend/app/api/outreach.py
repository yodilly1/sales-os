"""Outreach campaign API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.outreach.campaign_generator import (
    CampaignGenerator,
    OutreachCampaign,
    ProspectInfo,
    get_campaign,
)
from app.services.outreach.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateCampaignRequest(BaseModel):
    """Request model for generating an outreach campaign."""

    prospect_id: str
    prospect_email: Optional[str] = None
    prospect_name: str
    prospect_title: Optional[str] = None
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    linkedin_url: Optional[str] = None
    recent_news: Optional[str] = None
    pain_points: Optional[list[str]] = None


class GenerateCampaignResponse(BaseModel):
    """Response model for campaign generation."""

    success: bool
    campaign_id: str
    prospect_id: str
    prospect_name: str
    preview: dict = Field(description="Preview of generated content")
    message: str


class CampaignPreview(BaseModel):
    """Preview of campaign content."""

    email_1_subject: str
    email_1_preview: str
    email_2_subject: str
    email_2_preview: str
    email_3_subject: str
    email_3_preview: str
    linkedin_connection: str
    linkedin_followup_1_preview: str


class BulkGenerateRequest(BaseModel):
    """Request model for generating campaigns for multiple prospects."""

    prospects: list[GenerateCampaignRequest]


class BulkGenerateResponse(BaseModel):
    """Response model for bulk campaign generation."""

    success: bool
    total_requested: int
    total_generated: int
    campaign_ids: list[str]
    failures: list[dict]


@router.post("/generate", response_model=GenerateCampaignResponse)
async def generate_campaign(request: GenerateCampaignRequest) -> GenerateCampaignResponse:
    """Generate an outreach campaign for a prospect.

    Creates personalized email and LinkedIn sequences using AI.
    """
    try:
        # Convert request to ProspectInfo
        prospect_info = ProspectInfo(
            prospect_id=request.prospect_id,
            prospect_email=request.prospect_email,
            prospect_name=request.prospect_name,
            prospect_title=request.prospect_title,
            company_name=request.company_name,
            company_description=request.company_description,
            company_industry=request.company_industry,
            company_size=request.company_size,
            linkedin_url=request.linkedin_url,
            recent_news=request.recent_news,
            pain_points=request.pain_points,
        )

        # Generate campaign
        generator = CampaignGenerator()
        campaign = await generator.generate_campaign(prospect_info)

        # Create preview
        emails = campaign.email_sequence.emails
        preview = {
            "email_1_subject": emails[0].subject if len(emails) > 0 else "",
            "email_1_preview": emails[0].body[:150] + "..." if len(emails) > 0 and len(emails[0].body) > 150 else (emails[0].body if len(emails) > 0 else ""),
            "email_2_subject": emails[1].subject if len(emails) > 1 else "",
            "email_2_preview": emails[1].body[:150] + "..." if len(emails) > 1 and len(emails[1].body) > 150 else (emails[1].body if len(emails) > 1 else ""),
            "email_3_subject": emails[2].subject if len(emails) > 2 else "",
            "email_3_preview": emails[2].body[:150] + "..." if len(emails) > 2 and len(emails[2].body) > 150 else (emails[2].body if len(emails) > 2 else ""),
            "linkedin_connection": campaign.linkedin_sequence.connection_request,
            "linkedin_followup_1_preview": campaign.linkedin_sequence.followup_1[:100] + "..." if len(campaign.linkedin_sequence.followup_1) > 100 else campaign.linkedin_sequence.followup_1,
        }

        return GenerateCampaignResponse(
            success=True,
            campaign_id=campaign.campaign_id,
            prospect_id=campaign.prospect_id,
            prospect_name=campaign.prospect_name,
            preview=preview,
            message="Campaign generated successfully",
        )

    except Exception as e:
        logger.error(f"Failed to generate campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate campaign: {str(e)}")


@router.post("/generate/bulk", response_model=BulkGenerateResponse)
async def generate_bulk_campaigns(request: BulkGenerateRequest) -> BulkGenerateResponse:
    """Generate outreach campaigns for multiple prospects."""
    generator = CampaignGenerator()
    campaign_ids = []
    failures = []

    for prospect_request in request.prospects:
        try:
            prospect_info = ProspectInfo(
                prospect_id=prospect_request.prospect_id,
                prospect_email=prospect_request.prospect_email,
                prospect_name=prospect_request.prospect_name,
                prospect_title=prospect_request.prospect_title,
                company_name=prospect_request.company_name,
                company_description=prospect_request.company_description,
                company_industry=prospect_request.company_industry,
                company_size=prospect_request.company_size,
                linkedin_url=prospect_request.linkedin_url,
                recent_news=prospect_request.recent_news,
                pain_points=prospect_request.pain_points,
            )

            campaign = await generator.generate_campaign(prospect_info)
            campaign_ids.append(campaign.campaign_id)

        except Exception as e:
            logger.error(f"Failed to generate campaign for {prospect_request.prospect_name}: {e}")
            failures.append({
                "prospect_id": prospect_request.prospect_id,
                "prospect_name": prospect_request.prospect_name,
                "error": str(e),
            })

    return BulkGenerateResponse(
        success=len(failures) == 0,
        total_requested=len(request.prospects),
        total_generated=len(campaign_ids),
        campaign_ids=campaign_ids,
        failures=failures,
    )


@router.get("/campaign/{campaign_id}")
async def get_campaign_details(campaign_id: str) -> OutreachCampaign:
    """Get details of a generated campaign."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/export/instantly/{campaign_id}")
async def export_instantly(campaign_id: str) -> StreamingResponse:
    """Download campaign as Instantly-compatible CSV."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    export_service = ExportService()
    csv_content = export_service.export_to_instantly(campaign)

    # Create streaming response
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=instantly_campaign_{campaign_id[:8]}.csv"
        },
    )


@router.get("/export/heyreach/{campaign_id}")
async def export_heyreach(campaign_id: str) -> StreamingResponse:
    """Download campaign as HeyReach-compatible CSV."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    export_service = ExportService()
    csv_content = export_service.export_to_heyreach(campaign)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=heyreach_campaign_{campaign_id[:8]}.csv"
        },
    )


@router.post("/export/instantly/bulk")
async def export_instantly_bulk(campaign_ids: list[str]) -> StreamingResponse:
    """Download multiple campaigns as a single Instantly CSV."""
    campaigns = []
    for campaign_id in campaign_ids:
        campaign = get_campaign(campaign_id)
        if campaign:
            campaigns.append(campaign)

    if not campaigns:
        raise HTTPException(status_code=404, detail="No valid campaigns found")

    export_service = ExportService()
    csv_content = export_service.export_multiple_to_instantly(campaigns)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=instantly_campaigns_bulk.csv"
        },
    )


@router.post("/export/heyreach/bulk")
async def export_heyreach_bulk(campaign_ids: list[str]) -> StreamingResponse:
    """Download multiple campaigns as a single HeyReach CSV."""
    campaigns = []
    for campaign_id in campaign_ids:
        campaign = get_campaign(campaign_id)
        if campaign:
            campaigns.append(campaign)

    if not campaigns:
        raise HTTPException(status_code=404, detail="No valid campaigns found")

    export_service = ExportService()
    csv_content = export_service.export_multiple_to_heyreach(campaigns)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=heyreach_campaigns_bulk.csv"
        },
    )
