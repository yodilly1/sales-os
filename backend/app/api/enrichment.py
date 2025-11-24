"""API routes for prospect and company enrichment."""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from app.schemas.enrichment import (
    ProspectCreate,
    ProspectEnriched,
    ProspectBulkImportResult,
    EnrichmentRequest,
    EnrichmentResult,
    EnrichmentSource,
    ContactInfo,
    SocialProfiles,
    SingleLookupRequest,
    SingleLookupResponse,
    ProspectResponse,
    CompanyResponse,
)
from app.models.company import CompanyCreate, CompanyEnriched

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances - lazy initialization to handle missing dependencies
_enrichment_service = None
_batch_processor = None
_hubspot_mapper = None


def get_enrichment_service():
    """Get or create the enrichment service instance."""
    global _enrichment_service
    if _enrichment_service is None:
        try:
            from app.services.enrichment.service import EnrichmentService
            _enrichment_service = EnrichmentService()
        except Exception as e:
            logger.warning(f"Could not initialize EnrichmentService: {e}")
            _enrichment_service = None
    return _enrichment_service


def get_batch_processor():
    """Get or create the batch processor instance."""
    global _batch_processor
    if _batch_processor is None:
        try:
            from app.services.enrichment.batch_processor import BatchProcessor
            service = get_enrichment_service()
            if service:
                _batch_processor = BatchProcessor(service)
        except Exception as e:
            logger.warning(f"Could not initialize BatchProcessor: {e}")
            _batch_processor = None
    return _batch_processor


def get_hubspot_mapper():
    """Get or create the HubSpot mapper instance."""
    global _hubspot_mapper
    if _hubspot_mapper is None:
        try:
            from app.services.enrichment.hubspot_mapper import HubSpotFieldMapper
            _hubspot_mapper = HubSpotFieldMapper()
        except Exception as e:
            logger.warning(f"Could not initialize HubSpotFieldMapper: {e}")
            _hubspot_mapper = None
    return _hubspot_mapper


def parse_csv_preview_safe(content: bytes) -> dict:
    """Safely parse CSV preview."""
    try:
        from app.services.enrichment.batch_processor import parse_csv_preview
        return parse_csv_preview(content)
    except Exception as e:
        logger.warning(f"Could not parse CSV preview: {e}")
        return {
            "headers": [],
            "detected_mapping": {},
            "sample_rows": [],
            "total_columns": 0,
        }


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
    service = get_enrichment_service()
    if service and hasattr(service, 'providers'):
        providers = list(service.providers.keys())
    else:
        providers = []
    return {
        "status": "ok",
        "service": "enrichment",
        "providers_configured": len(providers),
        "providers": providers,
        "service_available": service is not None,
    }


# Frontend-compatible single lookup endpoint
@router.post("/lookup", response_model=SingleLookupResponse)
async def lookup_prospect(request: SingleLookupRequest):
    """
    Single prospect lookup - frontend compatible endpoint.

    Enriches a prospect based on email, name, company information.
    Returns data in a format compatible with the frontend.
    """
    now = datetime.utcnow().isoformat() + "Z"

    # Parse name into first/last name
    first_name = None
    last_name = None
    if request.name:
        parts = request.name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else None

    service = get_enrichment_service()

    # Create a basic prospect response
    prospect_id = str(uuid4())

    if service and service.providers:
        # We have enrichment providers - try to enrich
        try:
            prospect_create = ProspectCreate(
                first_name=first_name,
                last_name=last_name,
                full_name=request.name,
                email=request.email,
                title=request.title,
                company_name=request.company,
                company_domain=request.company_domain,
                linkedin_url=request.linkedinUrl,
            )

            result = await service.enrich_prospect(
                prospect=prospect_create,
                include_company=True,
                include_linkedin=bool(request.linkedinUrl),
                include_news=True,
                include_contact_verification=bool(request.email),
            )

            # Convert to frontend format
            enriched = result.prospect
            prospect_response = ProspectResponse(
                id=enriched.id if enriched else prospect_id,
                name=request.name or f"{first_name or ''} {last_name or ''}".strip() or "Unknown",
                email=str(request.email) if request.email else (enriched.email if enriched else None),
                title=request.title or (enriched.title if enriched else None),
                company=request.company or (enriched.company_name if enriched else None),
                companyId=enriched.company_id if enriched else None,
                phone=enriched.contact_info.phone if enriched and enriched.contact_info else None,
                linkedinUrl=request.linkedinUrl or (enriched.social_profiles.linkedin_url if enriched and enriched.social_profiles else None),
                location=enriched.linkedin_insights.location if enriched and enriched.linkedin_insights else None,
                enrichmentStatus="completed" if enriched else "failed",
                enrichmentData={
                    "verifiedEmail": enriched.contact_info.email if enriched and enriched.contact_info else None,
                    "verifiedPhone": enriched.contact_info.phone if enriched and enriched.contact_info else None,
                    "linkedinProfile": {
                        "url": enriched.social_profiles.linkedin_url if enriched and enriched.social_profiles else None,
                        "headline": enriched.linkedin_insights.headline if enriched and enriched.linkedin_insights else None,
                        "summary": enriched.linkedin_insights.summary if enriched and enriched.linkedin_insights else None,
                    } if enriched else None,
                    "confidence": int(enriched.enrichment_confidence * 100) if enriched else 0,
                } if enriched else None,
                crmSyncStatus="not_synced",
                crmId=None,
                lastEnrichedAt=now if enriched else None,
                createdAt=now,
                updatedAt=now,
            )

            # Build company response if available
            company_response = None
            if result.company:
                company_data = result.company
                company_response = CompanyResponse(
                    id=company_data.get("id", str(uuid4())),
                    name=company_data.get("name", request.company or ""),
                    domain=company_data.get("domain"),
                    industry=company_data.get("industry"),
                    size=company_data.get("employee_range"),
                    employeeCount=company_data.get("employee_count"),
                    revenue=company_data.get("revenue_range"),
                    funding={
                        "totalRaised": company_data.get("funding_info", {}).get("total_raised"),
                        "lastRoundType": company_data.get("funding_info", {}).get("last_funding_stage"),
                    } if company_data.get("funding_info") else None,
                    techStack=company_data.get("tech_stack", {}).get("technologies", []) if company_data.get("tech_stack") else None,
                    headquarters=company_data.get("headquarters", {}).get("formatted_address") if company_data.get("headquarters") else None,
                    website=company_data.get("website"),
                    linkedinUrl=company_data.get("social_profiles", {}).get("linkedin_url") if company_data.get("social_profiles") else None,
                    description=company_data.get("description"),
                    logoUrl=company_data.get("logo_url"),
                    lastEnrichedAt=now,
                    createdAt=now,
                    updatedAt=now,
                )

            return SingleLookupResponse(
                success=True,
                prospect=prospect_response,
                company=company_response,
                error=None,
            )

        except Exception as e:
            logger.error(f"Enrichment error: {e}")
            # Fall through to basic response

    # No enrichment providers or enrichment failed - return basic prospect
    prospect_response = ProspectResponse(
        id=prospect_id,
        name=request.name or "Unknown",
        email=str(request.email) if request.email else None,
        title=request.title,
        company=request.company,
        companyId=None,
        phone=None,
        linkedinUrl=request.linkedinUrl,
        location=None,
        enrichmentStatus="pending",
        enrichmentData=None,
        crmSyncStatus="not_synced",
        crmId=None,
        lastEnrichedAt=None,
        createdAt=now,
        updatedAt=now,
    )

    # Build basic company response if company info provided
    company_response = None
    if request.company:
        company_response = CompanyResponse(
            id=str(uuid4()),
            name=request.company,
            domain=request.company_domain,
            industry=None,
            size=None,
            employeeCount=None,
            revenue=None,
            funding=None,
            techStack=None,
            headquarters=None,
            website=f"https://{request.company_domain}" if request.company_domain else None,
            linkedinUrl=None,
            description=None,
            logoUrl=None,
            lastEnrichedAt=None,
            createdAt=now,
            updatedAt=now,
        )

    return SingleLookupResponse(
        success=True,
        prospect=prospect_response,
        company=company_response,
        error=None,
        message="No enrichment providers configured. Basic prospect data returned." if not service or not service.providers else None,
    )


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
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    prospect = ProspectCreate(
        first_name=request.first_name,
        last_name=request.last_name,
        full_name=request.full_name,
        email=request.email,
        title=request.title,
        company_name=request.company_name,
        company_domain=request.company_domain,
    )

    result = await service.enrich_prospect(
        prospect=prospect,
        include_company=request.include_company,
        include_linkedin=request.include_linkedin,
        include_news=request.include_news,
        include_contact_verification=request.include_contact_verification,
    )

    # Map to HubSpot if requested
    if request.sync_to_hubspot and result.prospect:
        mapper = get_hubspot_mapper()
        if mapper:
            mapper.map_prospect_to_hubspot(result.prospect)

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
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    company = CompanyCreate(
        name=request.name,
        domain=request.domain,
    )

    result = await service.enrich_company(
        company=company,
        include_news=request.include_news,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Could not find company data for the provided information",
        )

    if request.sync_to_hubspot:
        mapper = get_hubspot_mapper()
        if mapper:
            mapper.map_company_to_hubspot(result)

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
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    mapper = get_hubspot_mapper()
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

        result = await service.enrich_prospect(
            prospect=prospect,
            include_company=prospect_request.include_company,
            include_linkedin=prospect_request.include_linkedin,
            include_news=prospect_request.include_news,
            include_contact_verification=prospect_request.include_contact_verification,
        )

        if request.sync_to_hubspot and result.prospect and mapper:
            mapper.map_prospect_to_hubspot(result.prospect)

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
    preview = parse_csv_preview_safe(content)
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
    processor = get_batch_processor()
    if not processor:
        raise HTTPException(
            status_code=503,
            detail="Batch processor not available",
        )

    content = await file.read()

    result = await processor.process_csv(
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
    processor = get_batch_processor()
    if not processor:
        raise HTTPException(
            status_code=503,
            detail="Batch processor not available",
        )

    result = await processor.process_event_list(
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
async def map_prospect_to_hubspot_endpoint(prospect: ProspectEnriched):
    """
    Map enriched prospect to HubSpot contact properties.

    Returns the property mapping and any custom properties that need to be created.
    """
    mapper = get_hubspot_mapper()
    if not mapper:
        raise HTTPException(
            status_code=503,
            detail="HubSpot mapper not available",
        )

    properties = mapper.map_prospect_to_hubspot(prospect)
    custom_properties = mapper.get_custom_properties_schema()

    return HubSpotMappingResponse(
        properties=properties,
        custom_properties_needed=custom_properties,
    )


@router.post("/hubspot/map/company", response_model=HubSpotMappingResponse)
async def map_company_to_hubspot_endpoint(company: CompanyEnriched):
    """
    Map enriched company to HubSpot company properties.

    Returns the property mapping and any custom properties that need to be created.
    """
    mapper = get_hubspot_mapper()
    if not mapper:
        raise HTTPException(
            status_code=503,
            detail="HubSpot mapper not available",
        )

    properties = mapper.map_company_to_hubspot(company)
    custom_properties = mapper.get_custom_properties_schema()

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
    mapper = get_hubspot_mapper()
    if not mapper:
        return {"contact": [], "company": []}
    return mapper.get_custom_properties_schema()


# Email Verification
@router.post("/verify/email")
async def verify_email(
    email: EmailStr = Query(..., description="Email address to verify"),
):
    """
    Verify if an email address is valid and deliverable.

    Uses Hunter.io for verification when configured.
    """
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    hunter = service.providers.get("hunter")

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
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    hunter = service.providers.get("hunter")

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
    service = get_enrichment_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enrichment service not available",
        )

    news_provider = service.providers.get("news")

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


# Provider Status
@router.get("/providers")
async def get_provider_status():
    """
    Get status of all configured enrichment providers.
    """
    service = get_enrichment_service()
    providers = {}

    if service:
        for name, provider in service.providers.items():
            providers[name] = {
                "name": provider.name,
                "configured": provider.is_configured,
                "source": provider.source.value,
            }

    return {
        "total_providers": len(providers),
        "providers": providers,
        "service_available": service is not None,
    }


# Additional endpoints for frontend compatibility

@router.get("/prospects")
async def get_prospects_list(
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get list of prospects (placeholder - needs database integration).
    """
    # TODO: Implement database storage for prospects
    return {
        "prospects": [],
        "total": 0,
        "message": "Prospect storage not yet implemented. Use /lookup to enrich prospects.",
    }


@router.get("/prospects/{prospect_id}")
async def get_prospect_by_id(prospect_id: str):
    """
    Get a single prospect by ID (placeholder - needs database integration).
    """
    raise HTTPException(
        status_code=404,
        detail="Prospect storage not yet implemented",
    )


@router.get("/companies/{company_id}")
async def get_company_by_id(company_id: str):
    """
    Get a single company by ID (placeholder - needs database integration).
    """
    raise HTTPException(
        status_code=404,
        detail="Company storage not yet implemented",
    )


@router.post("/sync-crm")
async def sync_to_crm(
    prospect_ids: list[str],
    target_crm: str = "hubspot",
):
    """
    Sync prospects to CRM (placeholder - needs CRM integration).
    """
    return {
        "success": True,
        "synced": 0,
        "failed": len(prospect_ids),
        "message": "CRM sync not yet implemented",
    }


@router.post("/prospects/{prospect_id}/re-enrich")
async def re_enrich_prospect(prospect_id: str):
    """
    Re-enrich a prospect (placeholder - needs database integration).
    """
    raise HTTPException(
        status_code=404,
        detail="Prospect re-enrichment requires database storage",
    )


@router.get("/batches")
async def list_enrichment_batches(
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List enrichment batches (placeholder - needs database integration).
    """
    return {
        "batches": [],
        "total": 0,
    }


@router.post("/batches/{batch_id}/cancel")
async def cancel_enrichment_batch(batch_id: str):
    """
    Cancel an enrichment batch (placeholder - needs database integration).
    """
    return {"success": True, "message": "Batch cancellation not implemented"}


@router.get("/progress/{batch_id}")
async def get_batch_progress(batch_id: str):
    """
    Get progress of an enrichment batch (placeholder - needs database integration).
    """
    return {
        "batchId": batch_id,
        "status": "unknown",
        "totalCount": 0,
        "completedCount": 0,
        "failedCount": 0,
        "currentProspect": None,
        "estimatedTimeRemaining": 0,
        "errors": [],
    }


@router.get("/results/{batch_id}")
async def get_batch_results(batch_id: str):
    """
    Get results of an enrichment batch (placeholder - needs database integration).
    """
    return {
        "id": batch_id,
        "name": "Unknown",
        "type": "csv",
        "status": "unknown",
        "totalCount": 0,
        "completedCount": 0,
        "failedCount": 0,
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat(),
        "completedAt": None,
        "prospects": [],
    }


@router.post("/export")
async def export_prospects(
    prospect_ids: list[str] = [],
    format: str = "csv",
    include_company_data: bool = True,
):
    """
    Export prospects (placeholder - needs implementation).
    """
    return {
        "downloadUrl": None,
        "message": "Export not yet implemented",
    }
