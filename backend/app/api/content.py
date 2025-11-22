"""Content generation API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.constants import ContentStatus, ContentType
from app.models.content import (
    AudienceInfo,
    CompetitorInfo,
    ContentGenerationRequest,
    ContentGenerationResponse,
    ObjectionInfo,
    ProductInfo,
    SPICEDContext,
)
from app.services.content.generator import ContentGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

# In-memory storage for async jobs (replace with database in production)
_content_cache: dict[UUID, ContentGenerationResponse] = {}
_job_status: dict[UUID, ContentStatus] = {}


# =============================================================================
# Request/Response Models for API
# =============================================================================


class ContentGenerateRequest(BaseModel):
    """API request model for content generation."""

    content_type: ContentType = Field(..., description="Type of content to generate")
    goal: str = Field(..., description="Goal or purpose of the content")
    product_info: ProductInfo = Field(..., description="Product information")

    # Optional fields
    audience: Optional[AudienceInfo] = Field(None, description="Target audience")
    brand_voice: Optional[str] = Field(None, description="Brand voice (professional, conversational, technical, executive)")
    spiced_context: Optional[SPICEDContext] = Field(None, description="SPICED framework context")
    custom_instructions: Optional[str] = Field(None, description="Additional instructions")

    # Type-specific inputs
    competitors: Optional[list[CompetitorInfo]] = Field(None, description="Competitor info for battlecards")
    objections: Optional[list[ObjectionInfo]] = Field(None, description="Objections for objection battlecards")
    case_study_data: Optional[dict] = Field(None, description="Case study data")

    # Output preferences
    include_speaker_notes: bool = Field(True, description="Include speaker notes for decks")
    include_visual_suggestions: bool = Field(True, description="Include visual suggestions")
    max_slides: Optional[int] = Field(None, description="Max slides for decks")

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "deck_pitch",
                "goal": "Convince the prospect to schedule a demo",
                "product_info": {
                    "name": "Sales OS",
                    "description": "AI-powered sales enablement platform",
                    "key_features": ["AI content generation", "CRM integration", "Sales coaching"],
                    "value_propositions": ["Save 10 hours per week", "Increase close rates by 25%"],
                },
                "audience": {
                    "audience_type": "vp_director",
                    "company_name": "Acme Corp",
                    "industry": "Technology",
                },
            }
        }


class AsyncJobResponse(BaseModel):
    """Response for async job creation."""

    job_id: UUID = Field(..., description="Job ID to check status")
    status: ContentStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response for job status check."""

    job_id: UUID = Field(..., description="Job ID")
    status: ContentStatus = Field(..., description="Current job status")
    result: Optional[ContentGenerationResponse] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


# =============================================================================
# Synchronous Endpoints
# =============================================================================


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    summary="Generate content synchronously",
    description="Generate sales content and return the result immediately. Use for shorter generation tasks.",
)
async def generate_content(request: ContentGenerateRequest) -> ContentGenerationResponse:
    """Generate content synchronously.

    Args:
        request: Content generation request.

    Returns:
        Generated content response.
    """
    try:
        generator = ContentGenerator()

        # Convert API request to internal request
        internal_request = ContentGenerationRequest(
            content_type=request.content_type,
            goal=request.goal,
            product_info=request.product_info,
            audience=request.audience or AudienceInfo(),
            spiced_context=request.spiced_context,
            custom_instructions=request.custom_instructions,
            competitors=request.competitors,
            objections=request.objections,
            case_study_data=request.case_study_data,
            include_speaker_notes=request.include_speaker_notes,
            include_visual_suggestions=request.include_visual_suggestions,
            max_slides=request.max_slides,
        )

        result = await generator.generate(internal_request)
        return result

    except ValueError as e:
        logger.error(f"Validation error in content generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content. Please try again.",
        )


# =============================================================================
# Asynchronous Endpoints
# =============================================================================


async def _generate_content_async(job_id: UUID, request: ContentGenerationRequest) -> None:
    """Background task to generate content.

    Args:
        job_id: Job ID for tracking.
        request: Content generation request.
    """
    try:
        _job_status[job_id] = ContentStatus.GENERATING
        generator = ContentGenerator()
        result = await generator.generate(request)
        _content_cache[job_id] = result
        _job_status[job_id] = ContentStatus.COMPLETED
    except Exception as e:
        logger.error(f"Async content generation failed for job {job_id}: {e}")
        _job_status[job_id] = ContentStatus.FAILED


@router.post(
    "/generate/async",
    response_model=AsyncJobResponse,
    summary="Generate content asynchronously",
    description="Start content generation in background and return a job ID for status checking.",
)
async def generate_content_async(
    request: ContentGenerateRequest,
    background_tasks: BackgroundTasks,
) -> AsyncJobResponse:
    """Generate content asynchronously.

    Args:
        request: Content generation request.
        background_tasks: FastAPI background tasks.

    Returns:
        Job ID and status.
    """
    from uuid import uuid4

    job_id = uuid4()
    _job_status[job_id] = ContentStatus.PENDING

    # Convert API request to internal request
    internal_request = ContentGenerationRequest(
        content_type=request.content_type,
        goal=request.goal,
        product_info=request.product_info,
        audience=request.audience or AudienceInfo(),
        spiced_context=request.spiced_context,
        custom_instructions=request.custom_instructions,
        competitors=request.competitors,
        objections=request.objections,
        case_study_data=request.case_study_data,
        include_speaker_notes=request.include_speaker_notes,
        include_visual_suggestions=request.include_visual_suggestions,
        max_slides=request.max_slides,
    )

    background_tasks.add_task(_generate_content_async, job_id, internal_request)

    return AsyncJobResponse(
        job_id=job_id,
        status=ContentStatus.PENDING,
        message="Content generation started. Use the job ID to check status.",
    )


@router.get(
    "/job/{job_id}",
    response_model=JobStatusResponse,
    summary="Check job status",
    description="Check the status of an async content generation job.",
)
async def get_job_status(job_id: UUID) -> JobStatusResponse:
    """Get the status of an async job.

    Args:
        job_id: Job ID to check.

    Returns:
        Job status and result if completed.
    """
    if job_id not in _job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    current_status = _job_status[job_id]
    result = _content_cache.get(job_id) if current_status == ContentStatus.COMPLETED else None

    return JobStatusResponse(
        job_id=job_id,
        status=current_status,
        result=result,
        error="Generation failed" if current_status == ContentStatus.FAILED else None,
    )


# =============================================================================
# Convenience Endpoints by Content Type
# =============================================================================


@router.post(
    "/deck",
    response_model=ContentGenerationResponse,
    summary="Generate sales deck",
    description="Generate a sales deck (pitch, renewal, or QBR).",
)
async def generate_deck(
    deck_type: str = Query("pitch", description="Deck type: pitch, renewal, qbr"),
    goal: str = Query(..., description="Goal of the deck"),
    product_info: ProductInfo = ...,
    audience: Optional[AudienceInfo] = None,
    max_slides: Optional[int] = None,
) -> ContentGenerationResponse:
    """Generate a sales deck.

    Args:
        deck_type: Type of deck (pitch, renewal, qbr).
        goal: Goal of the deck.
        product_info: Product information.
        audience: Optional audience info.
        max_slides: Optional max slides.

    Returns:
        Generated deck content.
    """
    type_map = {
        "pitch": ContentType.DECK_PITCH,
        "renewal": ContentType.DECK_RENEWAL,
        "qbr": ContentType.DECK_QBR,
    }

    if deck_type not in type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid deck type: {deck_type}. Must be one of: pitch, renewal, qbr",
        )

    request = ContentGenerateRequest(
        content_type=type_map[deck_type],
        goal=goal,
        product_info=product_info,
        audience=audience,
        max_slides=max_slides,
    )

    return await generate_content(request)


@router.post(
    "/proposal",
    response_model=ContentGenerationResponse,
    summary="Generate proposal",
    description="Generate a sales proposal (custom or templated).",
)
async def generate_proposal(
    proposal_type: str = Query("custom", description="Proposal type: custom, templated"),
    goal: str = Query(..., description="Goal of the proposal"),
    product_info: ProductInfo = ...,
    audience: Optional[AudienceInfo] = None,
) -> ContentGenerationResponse:
    """Generate a proposal.

    Args:
        proposal_type: Type of proposal (custom, templated).
        goal: Goal of the proposal.
        product_info: Product information.
        audience: Optional audience info.

    Returns:
        Generated proposal content.
    """
    type_map = {
        "custom": ContentType.PROPOSAL_CUSTOM,
        "templated": ContentType.PROPOSAL_TEMPLATED,
    }

    if proposal_type not in type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid proposal type: {proposal_type}. Must be one of: custom, templated",
        )

    request = ContentGenerateRequest(
        content_type=type_map[proposal_type],
        goal=goal,
        product_info=product_info,
        audience=audience,
    )

    return await generate_content(request)


@router.post(
    "/one-pager",
    response_model=ContentGenerationResponse,
    summary="Generate one-pager",
    description="Generate a one-pager (product, solution, or case study).",
)
async def generate_one_pager(
    one_pager_type: str = Query("product", description="One-pager type: product, solution, case_study"),
    goal: str = Query(..., description="Goal of the one-pager"),
    product_info: ProductInfo = ...,
    audience: Optional[AudienceInfo] = None,
    case_study_data: Optional[dict] = None,
) -> ContentGenerationResponse:
    """Generate a one-pager.

    Args:
        one_pager_type: Type of one-pager (product, solution, case_study).
        goal: Goal of the one-pager.
        product_info: Product information.
        audience: Optional audience info.
        case_study_data: Optional case study data.

    Returns:
        Generated one-pager content.
    """
    type_map = {
        "product": ContentType.ONE_PAGER_PRODUCT,
        "solution": ContentType.ONE_PAGER_SOLUTION,
        "case_study": ContentType.ONE_PAGER_CASE_STUDY,
    }

    if one_pager_type not in type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid one-pager type: {one_pager_type}. Must be one of: product, solution, case_study",
        )

    request = ContentGenerateRequest(
        content_type=type_map[one_pager_type],
        goal=goal,
        product_info=product_info,
        audience=audience,
        case_study_data=case_study_data,
    )

    return await generate_content(request)


@router.post(
    "/battlecard",
    response_model=ContentGenerationResponse,
    summary="Generate battlecard",
    description="Generate a battlecard (competitive or objection handling).",
)
async def generate_battlecard(
    battlecard_type: str = Query("competitive", description="Battlecard type: competitive, objection"),
    goal: str = Query(..., description="Goal of the battlecard"),
    product_info: ProductInfo = ...,
    audience: Optional[AudienceInfo] = None,
    competitors: Optional[list[CompetitorInfo]] = None,
    objections: Optional[list[ObjectionInfo]] = None,
) -> ContentGenerationResponse:
    """Generate a battlecard.

    Args:
        battlecard_type: Type of battlecard (competitive, objection).
        goal: Goal of the battlecard.
        product_info: Product information.
        audience: Optional audience info.
        competitors: Optional competitor info.
        objections: Optional objection info.

    Returns:
        Generated battlecard content.
    """
    type_map = {
        "competitive": ContentType.BATTLECARD_COMPETITIVE,
        "objection": ContentType.BATTLECARD_OBJECTION,
    }

    if battlecard_type not in type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid battlecard type: {battlecard_type}. Must be one of: competitive, objection",
        )

    request = ContentGenerateRequest(
        content_type=type_map[battlecard_type],
        goal=goal,
        product_info=product_info,
        audience=audience,
        competitors=competitors,
        objections=objections,
    )

    return await generate_content(request)


# =============================================================================
# Content Management Endpoints
# =============================================================================


@router.get(
    "/{content_id}",
    response_model=ContentGenerationResponse,
    summary="Get content by ID",
    description="Retrieve previously generated content by its ID.",
)
async def get_content(content_id: UUID) -> ContentGenerationResponse:
    """Get content by ID.

    Args:
        content_id: Content ID.

    Returns:
        Content response.
    """
    # In production, this would query a database
    if content_id not in _content_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content {content_id} not found",
        )

    return _content_cache[content_id]


@router.get(
    "/types",
    summary="List content types",
    description="Get all available content types.",
)
async def list_content_types() -> dict:
    """List all available content types.

    Returns:
        Dictionary of content types by category.
    """
    return {
        "decks": [
            {"value": "deck_pitch", "label": "Pitch Deck", "description": "Initial sales pitch presentation"},
            {"value": "deck_renewal", "label": "Renewal Deck", "description": "Customer renewal presentation"},
            {"value": "deck_qbr", "label": "QBR Deck", "description": "Quarterly business review presentation"},
        ],
        "proposals": [
            {"value": "proposal_custom", "label": "Custom Proposal", "description": "Fully customized proposal"},
            {"value": "proposal_templated", "label": "Templated Proposal", "description": "Template-based proposal"},
        ],
        "one_pagers": [
            {"value": "one_pager_product", "label": "Product One-Pager", "description": "Product overview"},
            {"value": "one_pager_solution", "label": "Solution One-Pager", "description": "Solution overview"},
            {"value": "one_pager_case_study", "label": "Case Study", "description": "Customer success story"},
        ],
        "battlecards": [
            {"value": "battlecard_competitive", "label": "Competitive Battlecard", "description": "Competitor comparison"},
            {"value": "battlecard_objection", "label": "Objection Battlecard", "description": "Objection handling guide"},
        ],
    }
