"""API routes for outreach campaign generation and export."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from app.services.outreach.service import get_outreach_service
from app.services.outreach.models import (
    OutreachCampaign,
    OutreachFormat,
    ExportFormat,
    CampaignGenerateRequest,
    CampaignGenerateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Get service instance
outreach_service = get_outreach_service()


# Request/Response Models
class GenerateCampaignRequest(BaseModel):
    """Request model for generating an outreach campaign."""

    prospect_email: EmailStr
    prospect_name: str
    prospect_first_name: Optional[str] = None
    prospect_last_name: Optional[str] = None
    prospect_title: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None

    # Optional enrichment data
    company_data: Optional[dict] = None
    prospect_data: Optional[dict] = None
    web_research: Optional[dict] = None
    ai_insights: Optional[dict] = None

    # Generation options
    format: OutreachFormat = OutreachFormat.MULTI_CHANNEL
    num_email_steps: int = Field(default=3, ge=1, le=10)
    num_linkedin_steps: int = Field(default=2, ge=1, le=5)
    tone: str = Field(default="professional", pattern="^(professional|casual|formal)$")

    # Product/sender info for personalization
    product_info: Optional[dict] = None
    sender_info: Optional[dict] = None


class CampaignListResponse(BaseModel):
    """Response model for listing campaigns."""

    total: int
    campaigns: list[OutreachCampaign]


# Health check
@router.get("/health")
async def outreach_health():
    """Health check for outreach service."""
    return {
        "status": "ok",
        "service": "outreach",
    }


# Generate Campaign
@router.post("/generate", response_model=CampaignGenerateResponse)
async def generate_campaign(request: GenerateCampaignRequest):
    """
    Generate a personalized outreach campaign for a prospect.

    Creates email and/or LinkedIn sequences based on prospect and company data.
    Optionally includes enrichment data for better personalization.
    """
    # Parse first/last name if not provided
    first_name = request.prospect_first_name
    last_name = request.prospect_last_name

    if not first_name and request.prospect_name:
        name_parts = request.prospect_name.split()
        first_name = name_parts[0] if name_parts else None
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None

    campaign_request = CampaignGenerateRequest(
        prospect_email=request.prospect_email,
        prospect_name=request.prospect_name,
        prospect_first_name=first_name,
        prospect_last_name=last_name,
        prospect_title=request.prospect_title,
        company_name=request.company_name,
        company_domain=request.company_domain,
        company_data=request.company_data,
        prospect_data=request.prospect_data,
        web_research=request.web_research,
        ai_insights=request.ai_insights,
        format=request.format,
        num_email_steps=request.num_email_steps,
        num_linkedin_steps=request.num_linkedin_steps,
        tone=request.tone,
        product_info=request.product_info,
        sender_info=request.sender_info,
    )

    result = await outreach_service.generate_campaign(campaign_request)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate campaign: {result.error}",
        )

    return result


# Get Campaign
@router.get("/campaigns/{campaign_id}", response_model=OutreachCampaign)
async def get_campaign(campaign_id: str):
    """Get a specific campaign by ID."""
    campaign = outreach_service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {campaign_id}",
        )

    return campaign


# List Campaigns
@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all campaigns."""
    campaigns = outreach_service.list_campaigns()

    # Apply pagination
    paginated = campaigns[offset : offset + limit]

    return CampaignListResponse(
        total=len(campaigns),
        campaigns=paginated,
    )


# Export to Instantly
@router.get("/export/instantly/{campaign_id}")
async def export_to_instantly(campaign_id: str):
    """
    Export campaign to Instantly CSV format.

    Returns a CSV file that can be imported into Instantly
    for cold email automation.
    """
    campaign = outreach_service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {campaign_id}",
        )

    csv_content = outreach_service.export_to_instantly(campaign)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=instantly_campaign_{campaign_id}.csv"
        },
    )


# Export to HeyReach
@router.get("/export/heyreach/{campaign_id}")
async def export_to_heyreach(campaign_id: str):
    """
    Export campaign to HeyReach CSV format.

    Returns a CSV file that can be imported into HeyReach
    for LinkedIn automation.
    """
    campaign = outreach_service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {campaign_id}",
        )

    csv_content = outreach_service.export_to_heyreach(campaign)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=heyreach_campaign_{campaign_id}.csv"
        },
    )


# Generic Export
@router.get("/export/{format}/{campaign_id}")
async def export_campaign(
    campaign_id: str,
    format: ExportFormat,
):
    """
    Export campaign to specified format.

    Supported formats:
    - instantly: Instantly cold email CSV
    - heyreach: HeyReach LinkedIn CSV
    - csv: Generic CSV format
    """
    campaign = outreach_service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {campaign_id}",
        )

    csv_content = outreach_service.export_campaign(campaign, format)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={format.value}_campaign_{campaign_id}.csv"
        },
    )


# Bulk Export
@router.post("/export/bulk")
async def export_bulk_campaigns(
    campaign_ids: list[str],
    format: ExportFormat = ExportFormat.INSTANTLY,
):
    """
    Export multiple campaigns to a single CSV file.

    Combines all campaigns into one export file for bulk import.
    """
    import csv
    import io

    campaigns = []
    for campaign_id in campaign_ids:
        campaign = outreach_service.get_campaign(campaign_id)
        if campaign:
            campaigns.append(campaign)

    if not campaigns:
        raise HTTPException(
            status_code=404,
            detail="No valid campaigns found",
        )

    # Combine exports
    output = io.StringIO()

    if format == ExportFormat.INSTANTLY:
        writer = csv.writer(output)
        headers = [
            "email", "first_name", "last_name", "company_name",
            "personalization1", "personalization2", "personalization3",
            "personalization4", "personalization5",
        ]
        writer.writerow(headers)

        for campaign in campaigns:
            personalizations = []
            if campaign.email_sequence and campaign.email_sequence.steps:
                for step in campaign.email_sequence.steps[:5]:
                    personalizations.append(step.body)
            while len(personalizations) < 5:
                personalizations.append("")

            writer.writerow([
                campaign.prospect_email,
                campaign.prospect_first_name or "",
                campaign.prospect_last_name or "",
                campaign.company_name or "",
                personalizations[0],
                personalizations[1],
                personalizations[2],
                personalizations[3],
                personalizations[4],
            ])

    elif format == ExportFormat.HEYREACH:
        writer = csv.writer(output)
        headers = [
            "linkedin_url", "first_name", "last_name", "email",
            "company", "title", "personalization_snippet", "custom_message",
        ]
        writer.writerow(headers)

        for campaign in campaigns:
            custom_message = ""
            personalization = ""
            if campaign.linkedin_sequence and campaign.linkedin_sequence.steps:
                custom_message = campaign.linkedin_sequence.steps[0].body
            if campaign.company_insights and campaign.company_insights.get("description"):
                personalization = campaign.company_insights["description"][:100]

            writer.writerow([
                "",  # linkedin_url
                campaign.prospect_first_name or "",
                campaign.prospect_last_name or "",
                campaign.prospect_email or "",
                campaign.company_name or "",
                campaign.prospect_title or "",
                personalization,
                custom_message,
            ])

    csv_content = output.getvalue()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bulk_{format.value}_export.csv"
        },
    )
