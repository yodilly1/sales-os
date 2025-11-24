"""API routes for prospect and company enrichment."""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from app.models.prospect import (
    ProspectCreate,
    ProspectEnriched,
    ProspectBulkImportResult,
    EnrichmentRequest,
    EnrichmentResult,
)
from app.models.company import CompanyCreate, CompanyEnriched
from app.services.enrichment.service import EnrichmentService
from app.services.enrichment.batch_processor import BatchProcessor, parse_csv_preview
from app.services.enrichment.hubspot_mapper import (
    HubSpotFieldMapper,
    create_hubspot_contact_payload,
    create_hubspot_company_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (in production, use dependency injection)
enrichment_service = EnrichmentService()
batch_processor = BatchProcessor(enrichment_service)
hubspot_mapper = HubSpotFieldMapper()


# Request/Response Models
class EnrichProspectRequest(BaseModel):
    """Request model for enriching a single prospect."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    include_company: bool = True
    include_linkedin: bool = True
    include_news: bool = True
    include_contact_verification: bool = True
    include_web_research: bool = False
    include_ai_insights: bool = False
    sync_to_hubspot: bool = False


class EnrichCompanyRequest(BaseModel):
    """Request model for enriching a company."""

    name: str
    domain: Optional[str] = None
    include_news: bool = True
    sync_to_hubspot: bool = False


class BulkEnrichRequest(BaseModel):
    """Request model for bulk prospect enrichment."""

    prospects: list[EnrichProspectRequest]
    sync_to_hubspot: bool = False


class EventListRequest(BaseModel):
    """Request model for processing event attendee lists."""

    attendees: list[dict[str, Any]]
    event_name: str
    event_date: Optional[datetime] = None
    platform: Optional[str] = None
    auto_enrich: bool = True
    sync_to_hubspot: bool = False


class CSVPreviewResponse(BaseModel):
    """Response model for CSV preview."""

    headers: list[str]
    detected_mapping: dict[str, Optional[str]]
    sample_rows: list[dict[str, Any]]
    total_columns: int


class HubSpotMappingResponse(BaseModel):
    """Response model for HubSpot field mapping."""

    properties: dict[str, Any]
    custom_properties_needed: dict[str, list[dict]]


# Health check
@router.get("/health")
async def enrichment_health():
    """Health check for enrichment service."""
    providers = list(enrichment_service.providers.keys())
    return {
        "status": "ok",
        "service": "enrichment",
        "providers_configured": len(providers),
        "providers": providers,
    }


# Individual Prospect Enrichment
@router.post("/prospect", response_model=EnrichmentResult)
async def enrich_prospect(request: EnrichProspectRequest):
    """
    Enrich a single prospect with data from multiple sources.

    Gathers and verifies:
    - Contact information validation
    - Company data (size, industry, funding, tech stack)
    - LinkedIn profile insights
    - Recent news and events
    """
    prospect = ProspectCreate(
        first_name=request.first_name,
        last_name=request.last_name,
        full_name=request.full_name,
        email=request.email,
        title=request.title,
        company_name=request.company_name,
        company_domain=request.company_domain,
    )

    result = await enrichment_service.enrich_prospect(
        prospect=prospect,
        include_company=request.include_company,
        include_linkedin=request.include_linkedin,
        include_news=request.include_news,
        include_contact_verification=request.include_contact_verification,
        include_web_research=request.include_web_research,
        include_ai_insights=request.include_ai_insights,
    )

    # Map to HubSpot if requested
    if request.sync_to_hubspot and result.prospect:
        hubspot_mapper.map_prospect_to_hubspot(result.prospect)

    return result


# Company Enrichment
@router.post("/company", response_model=CompanyEnriched)
async def enrich_company(request: EnrichCompanyRequest):
    """
    Enrich company data from multiple sources.

    Gathers:
    - Company size, industry, funding info
    - Tech stack
    - Recent news and press releases
    - Social profiles
    - Key executives
    """
    company = CompanyCreate(
        name=request.name,
        domain=request.domain,
    )

    result = await enrichment_service.enrich_company(
        company=company,
        include_news=request.include_news,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Could not find company data for the provided information",
        )

    if request.sync_to_hubspot:
        hubspot_mapper.map_company_to_hubspot(result)

    return result


# Bulk Enrichment
@router.post("/bulk", response_model=list[EnrichmentResult])
async def enrich_bulk(
    request: BulkEnrichRequest,
    background_tasks: BackgroundTasks,
):
    """
    Enrich multiple prospects in batch.

    Processes prospects concurrently with rate limiting.
    """
    results = []

    for prospect_request in request.prospects:
        prospect = ProspectCreate(
            first_name=prospect_request.first_name,
            last_name=prospect_request.last_name,
            full_name=prospect_request.full_name,
            email=prospect_request.email,
            title=prospect_request.title,
            company_name=prospect_request.company_name,
            company_domain=prospect_request.company_domain,
        )

        result = await enrichment_service.enrich_prospect(
            prospect=prospect,
            include_company=prospect_request.include_company,
            include_linkedin=prospect_request.include_linkedin,
            include_news=prospect_request.include_news,
            include_contact_verification=prospect_request.include_contact_verification,
        )

        if request.sync_to_hubspot and result.prospect:
            hubspot_mapper.map_prospect_to_hubspot(result.prospect)

        results.append(result)

    return results


# CSV Import
@router.post("/import/csv/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    platform: Optional[str] = Query(None, description="Event platform (eventbrite, hopin, zoom, etc.)"),
):
    """
    Preview CSV file and show detected column mappings.

    Returns headers, detected field mappings, and sample rows.
    """
    content = await file.read()
    preview = parse_csv_preview(content)
    return CSVPreviewResponse(**preview)


@router.post("/import/csv", response_model=ProspectBulkImportResult)
async def import_csv(
    file: UploadFile = File(...),
    source: str = Form("csv_import"),
    event_name: Optional[str] = Form(None),
    event_date: Optional[datetime] = Form(None),
    auto_enrich: bool = Form(True),
    sync_to_hubspot: bool = Form(False),
    platform: Optional[str] = Form(None),
    delimiter: str = Form(","),
):
    """
    Import and optionally enrich prospects from CSV file.

    Supports various CSV formats and event platforms:
    - Eventbrite attendee exports
    - Hopin attendee lists
    - Zoom webinar registrants
    - HubSpot contact exports
    - Salesforce lead exports
    - Custom CSV files
    """
    content = await file.read()

    result = await batch_processor.process_csv(
        file_content=content,
        source=source,
        event_name=event_name,
        event_date=event_date,
        auto_enrich=auto_enrich,
        sync_to_hubspot=sync_to_hubspot,
        platform=platform,
        delimiter=delimiter,
    )

    return result


# Event List Processing
@router.post("/import/event", response_model=ProspectBulkImportResult)
async def import_event_list(request: EventListRequest):
    """
    Process event attendee list and optionally enrich.

    Accepts attendee data from various event platforms.
    """
    result = await batch_processor.process_event_list(
        attendees=request.attendees,
        event_name=request.event_name,
        event_date=request.event_date,
        platform=request.platform,
        auto_enrich=request.auto_enrich,
        sync_to_hubspot=request.sync_to_hubspot,
    )

    return result


# HubSpot Field Mapping
@router.post("/hubspot/map/prospect", response_model=HubSpotMappingResponse)
async def map_prospect_to_hubspot(prospect: ProspectEnriched):
    """
    Map enriched prospect to HubSpot contact properties.

    Returns the property mapping and any custom properties that need to be created.
    """
    properties = hubspot_mapper.map_prospect_to_hubspot(prospect)
    custom_properties = hubspot_mapper.get_custom_properties_schema()

    return HubSpotMappingResponse(
        properties=properties,
        custom_properties_needed=custom_properties,
    )


@router.post("/hubspot/map/company", response_model=HubSpotMappingResponse)
async def map_company_to_hubspot(company: CompanyEnriched):
    """
    Map enriched company to HubSpot company properties.

    Returns the property mapping and any custom properties that need to be created.
    """
    properties = hubspot_mapper.map_company_to_hubspot(company)
    custom_properties = hubspot_mapper.get_custom_properties_schema()

    return HubSpotMappingResponse(
        properties=properties,
        custom_properties_needed=custom_properties,
    )


@router.get("/hubspot/custom-properties")
async def get_hubspot_custom_properties():
    """
    Get schema for custom HubSpot properties that need to be created.

    Returns property definitions for both contacts and companies.
    """
    return hubspot_mapper.get_custom_properties_schema()


# Email Verification
@router.post("/verify/email")
async def verify_email(
    email: EmailStr = Query(..., description="Email address to verify"),
):
    """
    Verify if an email address is valid and deliverable.

    Uses Hunter.io for verification when configured.
    """
    hunter = enrichment_service.providers.get("hunter")

    if not hunter:
        raise HTTPException(
            status_code=503,
            detail="Email verification service not configured",
        )

    result = await hunter.verify_email(email)
    return result


# Find Email
@router.post("/find/email")
async def find_email(
    first_name: str = Query(..., description="Person's first name"),
    last_name: str = Query(..., description="Person's last name"),
    domain: str = Query(..., description="Company domain"),
):
    """
    Find email address for a person at a company.

    Uses Hunter.io email finder when configured.
    """
    hunter = enrichment_service.providers.get("hunter")

    if not hunter:
        raise HTTPException(
            status_code=503,
            detail="Email finder service not configured",
        )

    result = await hunter.enrich_prospect(
        name=f"{first_name} {last_name}",
        domain=domain,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Could not find email for the provided person and company",
        )

    return result


# Company News
@router.get("/news/company/{company_name}")
async def get_company_news(
    company_name: str,
    days_back: int = Query(30, ge=1, le=90, description="Days to look back for news"),
    limit: int = Query(10, ge=1, le=50, description="Maximum articles to return"),
):
    """
    Get recent news articles about a company.
    """
    news_provider = enrichment_service.providers.get("news")

    if not news_provider:
        raise HTTPException(
            status_code=503,
            detail="News service not configured",
        )

    articles = await news_provider.search_news(
        query=f'"{company_name}"',
        days_back=days_back,
        limit=limit,
    )

    return {
        "company": company_name,
        "article_count": len(articles),
        "articles": articles,
    }


# Company Lookup with Web Research
class LookupRequest(BaseModel):
    """Request model for quick company lookup."""

    company_name: str
    company_domain: Optional[str] = None
    include_web_research: bool = False
    include_ai_insights: bool = False


class LookupResponse(BaseModel):
    """Response model for company lookup."""

    company_name: str
    company_domain: Optional[str] = None
    company_data: Optional[dict] = None
    web_research: Optional[dict] = None
    ai_insights: Optional[dict] = None
    sources_used: list[str] = []
    lookup_duration_ms: int = 0


@router.post("/lookup", response_model=LookupResponse)
async def lookup_company(request: LookupRequest):
    """
    Quick company lookup with optional web research and AI insights.

    This endpoint provides a simplified way to get company information
    with web research data when `include_web_research=true`.
    """
    import time
    start_time = time.time()

    sources_used = []
    web_research = None
    ai_insights = None
    company_data = None

    # Get company enrichment
    from app.models.company import CompanyCreate
    company = CompanyCreate(
        name=request.company_name,
        domain=request.company_domain,
    )
    company_result = await enrichment_service.enrich_company(company, include_news=True)

    if company_result:
        company_data = company_result.model_dump()
        sources_used.extend(company_result.data_sources)

    # Get web research if requested
    if request.include_web_research:
        web_provider = enrichment_service.providers.get("web_research")
        if web_provider:
            research = await web_provider.research_company(
                company_name=request.company_name,
                domain=request.company_domain,
            )
            if research:
                web_research = research
                sources_used.append("web_research")

    # Get AI insights if requested
    if request.include_ai_insights:
        try:
            insights = await enrichment_service.ai_insights.analyze_company(
                company_name=request.company_name,
                web_research=web_research,
                enrichment_data=company_data,
            )
            if insights:
                ai_insights = insights
                sources_used.append("ai_insights")
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")

    duration_ms = int((time.time() - start_time) * 1000)

    return LookupResponse(
        company_name=request.company_name,
        company_domain=request.company_domain,
        company_data=company_data,
        web_research=web_research,
        ai_insights=ai_insights,
        sources_used=list(set(sources_used)),
        lookup_duration_ms=duration_ms,
    )


# Provider Status
@router.get("/providers")
async def get_provider_status():
    """
    Get status of all configured enrichment providers.
    """
    providers = {}

    for name, provider in enrichment_service.providers.items():
        providers[name] = {
            "name": provider.name,
            "configured": provider.is_configured,
            "source": provider.source.value,
        }

    return {
        "total_providers": len(providers),
        "providers": providers,
    }
