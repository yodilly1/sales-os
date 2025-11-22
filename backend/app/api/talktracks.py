"""
Talk Track API Endpoints

REST API for talk track generation, management, and performance tracking.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.models.talktrack import (
    TalkTrackRequest,
    TalkTrackResponse,
    TalkTrack,
    TalkTrackLibrary,
    TalkTrackLibraryItem,
    ScriptType,
    PersonaType,
    Industry,
    DealStage,
    ScriptUsageEvent,
    ScriptPerformanceMetrics,
)
from backend.app.services.talktracks import (
    TalkTrackGenerator,
    TalkTrackPerformanceTracker,
)

router = APIRouter(prefix="/api/talktracks", tags=["Talk Tracks"])

# Dependency injection for services
_generator: Optional[TalkTrackGenerator] = None
_tracker: Optional[TalkTrackPerformanceTracker] = None


def get_generator() -> TalkTrackGenerator:
    """Get or create the talk track generator."""
    global _generator
    if _generator is None:
        _generator = TalkTrackGenerator()
    return _generator


def get_tracker() -> TalkTrackPerformanceTracker:
    """Get or create the performance tracker."""
    global _tracker
    if _tracker is None:
        _tracker = TalkTrackPerformanceTracker()
    return _tracker


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateResponse(BaseModel):
    """Response for talk track generation."""
    success: bool
    data: TalkTrackResponse
    message: str = "Talk track generated successfully"


class UsageEventRequest(BaseModel):
    """Request to record a usage event."""
    talktrack_id: UUID
    user_id: UUID
    deal_id: Optional[UUID] = None
    call_duration_minutes: Optional[int] = None
    variant_used: Optional[str] = None
    outcome: Optional[str] = None
    next_step_scheduled: bool = False
    deal_advanced: bool = False
    user_rating: Optional[int] = None
    user_notes: Optional[str] = None


class RecommendationRequest(BaseModel):
    """Request for talk track recommendations."""
    script_type: ScriptType
    persona: PersonaType
    industry: Industry
    deal_stage: Optional[DealStage] = None


class ABTestResult(BaseModel):
    """A/B test result for variants."""
    variant: str
    total_uses: int
    meetings_scheduled_rate: float
    deal_advancement_rate: float
    average_rating: Optional[float]
    is_winner: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# =============================================================================
# Talk Track Generation Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a talk track",
    description="Generate a new talk track based on script type, persona, industry, and context.",
)
async def generate_talktrack(
    request: TalkTrackRequest,
    generator: TalkTrackGenerator = Depends(get_generator),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> GenerateResponse:
    """
    Generate a new talk track.

    Supports:
    - Discovery call scripts with SPICED questions
    - Demo scripts with value focus
    - Objection response playbooks
    - Closing conversation guides
    - Follow-up call frameworks

    Options:
    - Persona-based customization
    - Industry-specific language
    - A/B variant generation
    - Coaching notes inclusion
    """
    try:
        response = await generator.generate(request)

        # Register the generated talk track for tracking
        await tracker.register_talktrack(
            talktrack_id=response.primary.id,
            title=response.primary.title,
            script_type=response.primary.script_type,
            persona=response.primary.persona,
            industry=response.primary.industry,
            version=response.primary.version,
        )

        # Register variants if any
        for variant in response.variants:
            await tracker.register_talktrack(
                talktrack_id=variant.id,
                title=variant.title,
                script_type=variant.script_type,
                persona=variant.persona,
                industry=variant.industry,
                version=variant.version,
            )

        return GenerateResponse(
            success=True,
            data=response,
            message=f"Generated {request.script_type.value} talk track with {len(response.variants)} variants",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate talk track: {str(e)}",
        )


@router.get(
    "/types",
    summary="Get available script types",
    description="List all available script types for generation.",
)
async def get_script_types() -> dict:
    """Get available script types and their descriptions."""
    return {
        "script_types": [
            {
                "value": ScriptType.DISCOVERY_CALL.value,
                "name": "Discovery Call",
                "description": "SPICED-aligned discovery call with probing questions",
            },
            {
                "value": ScriptType.DEMO_SCRIPT.value,
                "name": "Demo Script",
                "description": "Value-focused demo connecting features to pain points",
            },
            {
                "value": ScriptType.OBJECTION_RESPONSE.value,
                "name": "Objection Response",
                "description": "Playbook for handling common objections",
            },
            {
                "value": ScriptType.CLOSING_CONVERSATION.value,
                "name": "Closing Conversation",
                "description": "Framework for closing deals effectively",
            },
            {
                "value": ScriptType.FOLLOW_UP_GUIDE.value,
                "name": "Follow-Up Guide",
                "description": "Multi-touch follow-up framework",
            },
        ]
    }


@router.get(
    "/personas",
    summary="Get available personas",
    description="List all available buyer personas for customization.",
)
async def get_personas() -> dict:
    """Get available personas and their characteristics."""
    return {
        "personas": [
            {
                "value": PersonaType.EXECUTIVE.value,
                "name": "Executive",
                "description": "C-level and VP-level decision makers focused on strategy",
            },
            {
                "value": PersonaType.TECHNICAL.value,
                "name": "Technical",
                "description": "Technical evaluators focused on implementation details",
            },
            {
                "value": PersonaType.FINANCIAL.value,
                "name": "Financial",
                "description": "Finance stakeholders focused on ROI and budget",
            },
            {
                "value": PersonaType.OPERATIONS.value,
                "name": "Operations",
                "description": "Operations leaders focused on efficiency and process",
            },
            {
                "value": PersonaType.END_USER.value,
                "name": "End User",
                "description": "Day-to-day users focused on usability",
            },
            {
                "value": PersonaType.CHAMPION.value,
                "name": "Champion",
                "description": "Internal advocates helping drive the deal",
            },
            {
                "value": PersonaType.ECONOMIC_BUYER.value,
                "name": "Economic Buyer",
                "description": "Final decision maker with budget authority",
            },
        ]
    }


@router.get(
    "/industries",
    summary="Get available industries",
    description="List all available industries for language customization.",
)
async def get_industries() -> dict:
    """Get available industries."""
    return {
        "industries": [
            {"value": i.value, "name": i.value.replace("_", " ").title()}
            for i in Industry
        ]
    }


# =============================================================================
# Talk Track Library Endpoints
# =============================================================================

@router.get(
    "/library",
    response_model=TalkTrackLibrary,
    summary="Get talk track library",
    description="Get paginated list of talk tracks with optional filters.",
)
async def get_library(
    script_type: Optional[ScriptType] = Query(None, description="Filter by script type"),
    persona: Optional[PersonaType] = Query(None, description="Filter by persona"),
    industry: Optional[Industry] = Query(None, description="Filter by industry"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> TalkTrackLibrary:
    """Get paginated library of talk tracks."""
    return await tracker.get_library(
        script_type=script_type,
        persona=persona,
        industry=industry,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/library/{talktrack_id}",
    response_model=TalkTrack,
    summary="Get talk track by ID",
    description="Retrieve a specific talk track by its ID.",
)
async def get_talktrack(
    talktrack_id: UUID,
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> TalkTrack:
    """Get a specific talk track."""
    # In a real implementation, this would fetch from database
    if talktrack_id not in tracker._talk_tracks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Talk track {talktrack_id} not found",
        )

    # For now, return a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Full talk track retrieval requires database implementation",
    )


@router.get(
    "/recommendations",
    response_model=List[TalkTrackLibraryItem],
    summary="Get talk track recommendations",
    description="Get recommended talk tracks based on context and performance.",
)
async def get_recommendations(
    script_type: ScriptType = Query(..., description="Type of script needed"),
    persona: PersonaType = Query(..., description="Target buyer persona"),
    industry: Industry = Query(..., description="Target industry"),
    deal_stage: Optional[DealStage] = Query(None, description="Current deal stage"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> List[TalkTrackLibraryItem]:
    """Get recommended talk tracks for the given context."""
    from backend.app.services.talktracks.performance import TalkTrackRecommender

    recommender = TalkTrackRecommender(tracker)
    return await recommender.recommend(
        script_type=script_type,
        persona=persona,
        industry=industry,
        deal_stage=deal_stage,
    )


# =============================================================================
# Performance Tracking Endpoints
# =============================================================================

@router.post(
    "/usage",
    status_code=status.HTTP_201_CREATED,
    summary="Record usage event",
    description="Record when a talk track is used.",
)
async def record_usage(
    request: UsageEventRequest,
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> dict:
    """Record a talk track usage event."""
    event = ScriptUsageEvent(
        talktrack_id=request.talktrack_id,
        user_id=request.user_id,
        deal_id=request.deal_id,
        call_duration_minutes=request.call_duration_minutes,
        variant_used=request.variant_used,
        outcome=request.outcome,
        next_step_scheduled=request.next_step_scheduled,
        deal_advanced=request.deal_advanced,
        user_rating=request.user_rating,
        user_notes=request.user_notes,
    )

    recorded = await tracker.record_usage(event)

    return {
        "success": True,
        "event_id": str(recorded.id),
        "message": "Usage event recorded",
    }


@router.get(
    "/performance/{talktrack_id}",
    response_model=ScriptPerformanceMetrics,
    summary="Get performance metrics",
    description="Get performance metrics for a specific talk track.",
)
async def get_performance(
    talktrack_id: UUID,
    period_days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> ScriptPerformanceMetrics:
    """Get performance metrics for a talk track."""
    return await tracker.get_performance_metrics(talktrack_id, period_days)


@router.get(
    "/performance/{talktrack_id}/trends",
    summary="Get performance trends",
    description="Get performance trends over time for a talk track.",
)
async def get_trends(
    talktrack_id: UUID,
    period_days: int = Query(90, ge=7, le=365, description="Total period"),
    interval_days: int = Query(7, ge=1, le=30, description="Interval for data points"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> dict:
    """Get performance trends over time."""
    trends = await tracker.get_trend_analysis(talktrack_id, period_days, interval_days)
    return {
        "talktrack_id": str(talktrack_id),
        "period_days": period_days,
        "interval_days": interval_days,
        "data_points": trends,
    }


@router.get(
    "/performance/{talktrack_id}/ab-test",
    summary="Get A/B test results",
    description="Get A/B test results for talk track variants.",
)
async def get_ab_results(
    talktrack_id: UUID,
    period_days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> dict:
    """Get A/B test results for variants."""
    results = await tracker.get_ab_test_results(talktrack_id, period_days)

    if not results:
        return {
            "talktrack_id": str(talktrack_id),
            "message": "No variant data available",
            "variants": [],
        }

    variants = [
        ABTestResult(
            variant=variant,
            total_uses=data["total_uses"],
            meetings_scheduled_rate=data["meetings_scheduled_rate"],
            deal_advancement_rate=data["deal_advancement_rate"],
            average_rating=data.get("average_rating"),
            is_winner=data.get("is_winner", False),
        )
        for variant, data in results.items()
    ]

    return {
        "talktrack_id": str(talktrack_id),
        "period_days": period_days,
        "variants": [v.model_dump() for v in variants],
    }


@router.get(
    "/best-performers",
    response_model=List[TalkTrackLibraryItem],
    summary="Get best performing talk tracks",
    description="Get the best performing talk tracks based on metrics.",
)
async def get_best_performers(
    script_type: Optional[ScriptType] = Query(None, description="Filter by script type"),
    persona: Optional[PersonaType] = Query(None, description="Filter by persona"),
    industry: Optional[Industry] = Query(None, description="Filter by industry"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    tracker: TalkTrackPerformanceTracker = Depends(get_tracker),
) -> List[TalkTrackLibraryItem]:
    """Get best performing talk tracks."""
    return await tracker.get_best_performers(
        script_type=script_type,
        persona=persona,
        industry=industry,
        limit=limit,
    )


# =============================================================================
# Health Check
# =============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Check if the talk track service is healthy.",
)
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "talk-tracks",
        "version": "1.0.0",
    }
