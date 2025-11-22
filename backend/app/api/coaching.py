"""
Coaching API Endpoints

FastAPI routes for SPICED coaching functionality including:
- Per-call analysis and feedback
- Gap analysis
- Trend analysis over time
- Team benchmarking
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..models.coaching import (
    BulkCoachingRequest,
    CallType,
    CoachingReport,
    CoachingRequest,
    GapAnalysisReport,
    RepScoreHistory,
    SPICEDElement,
    TeamBenchmarkReport,
    TeamBenchmarkRequest,
    TrendAnalysisReport,
    TrendAnalysisRequest,
)
from ..services.coaching import CoachingService, CoachingServiceFactory

# Create router
router = APIRouter(prefix="/coaching", tags=["Coaching"])


# ============================================================================
# Response Models
# ============================================================================

class CoachingAnalysisResponse(BaseModel):
    """Response for call analysis endpoint."""

    report: CoachingReport
    gap_analysis: Optional[GapAnalysisReport] = None


class BulkAnalysisResponse(BaseModel):
    """Response for bulk call analysis."""

    reports: list[CoachingReport]
    total_analyzed: int
    average_score: float


class ScoresSummary(BaseModel):
    """Summary of SPICED scores."""

    situation: float
    pain: float
    impact: float
    critical_event: float
    expected_decision: float
    decision_criteria: float
    overall: float


class RepSummary(BaseModel):
    """Summary of a rep's coaching data."""

    rep_id: UUID
    rep_name: str
    total_calls: int
    average_score: Optional[float]
    recent_trend: Optional[str]
    last_call_date: Optional[datetime]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


# ============================================================================
# Dependency
# ============================================================================

def get_coaching_service() -> CoachingService:
    """Get the coaching service instance."""
    return CoachingServiceFactory.get_instance()


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check if the coaching service is healthy.
    """
    return HealthResponse(
        status="healthy",
        service="coaching",
        version="1.0.0",
    )


# ============================================================================
# Call Analysis Endpoints
# ============================================================================

@router.post(
    "/analyze",
    response_model=CoachingAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a sales call",
    description="Analyze a sales call transcript against the SPICED framework and generate coaching feedback.",
)
async def analyze_call(
    request: CoachingRequest,
) -> CoachingAnalysisResponse:
    """
    Analyze a sales call transcript and generate SPICED coaching feedback.

    This endpoint:
    - Scores each SPICED element (1-5)
    - Identifies strengths and improvement areas
    - Provides WbD-aligned coaching tips
    - Generates actionable talk tracks
    - Optionally includes detailed gap analysis

    Args:
        request: Coaching request with transcript and metadata

    Returns:
        Coaching report with optional gap analysis
    """
    service = get_coaching_service()

    try:
        if request.include_gap_analysis:
            report, gap_analysis = await service.analyze_call_with_gaps(request)
            return CoachingAnalysisResponse(report=report, gap_analysis=gap_analysis)
        else:
            report = await service.analyze_call(request)
            return CoachingAnalysisResponse(report=report)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post(
    "/analyze/bulk",
    response_model=BulkAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze multiple calls",
    description="Analyze multiple sales calls in batch.",
)
async def analyze_calls_bulk(
    request: BulkCoachingRequest,
) -> BulkAnalysisResponse:
    """
    Analyze multiple sales calls in a single request.

    Limited to 10 calls per request to manage processing time.

    Args:
        request: Bulk coaching request with list of calls

    Returns:
        Reports for all analyzed calls with summary statistics
    """
    service = get_coaching_service()

    reports = []
    for call_request in request.calls:
        try:
            report = await service.analyze_call(call_request)
            reports.append(report)
        except Exception as e:
            # Log error but continue with other calls
            pass

    if not reports:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No calls could be analyzed",
        )

    avg_score = sum(r.feedback.overall_score for r in reports) / len(reports)

    return BulkAnalysisResponse(
        reports=reports,
        total_analyzed=len(reports),
        average_score=round(avg_score, 2),
    )


@router.get(
    "/reports/{report_id}",
    response_model=CoachingReport,
    summary="Get coaching report",
    description="Retrieve a specific coaching report by ID.",
)
async def get_report(
    report_id: UUID,
) -> CoachingReport:
    """
    Retrieve a coaching report by its ID.

    Args:
        report_id: UUID of the coaching report

    Returns:
        The requested coaching report
    """
    service = get_coaching_service()
    report = service.get_coaching_report(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return report


@router.get(
    "/reports/rep/{rep_id}",
    response_model=list[CoachingReport],
    summary="Get rep's reports",
    description="Retrieve recent coaching reports for a specific rep.",
)
async def get_rep_reports(
    rep_id: UUID,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum reports to return"),
) -> list[CoachingReport]:
    """
    Get recent coaching reports for a sales rep.

    Args:
        rep_id: UUID of the sales rep
        limit: Maximum number of reports to return (1-50)

    Returns:
        List of recent coaching reports, newest first
    """
    service = get_coaching_service()
    reports = service.get_rep_reports(rep_id, limit=limit)

    return reports


# ============================================================================
# Trend Analysis Endpoints
# ============================================================================

@router.post(
    "/trends",
    response_model=TrendAnalysisReport,
    summary="Generate trend analysis",
    description="Analyze SPICED score trends for a rep over time.",
)
async def generate_trends(
    request: TrendAnalysisRequest,
) -> TrendAnalysisReport:
    """
    Generate trend analysis for a rep's SPICED scores over time.

    Requires at least 3 calls for meaningful analysis. Identifies:
    - Score trends by element (improving, declining, stable)
    - Strongest and weakest areas
    - Patterns and insights
    - Recommended goals and focus areas

    Args:
        request: Trend analysis request with rep ID and date range

    Returns:
        Comprehensive trend analysis report
    """
    service = get_coaching_service()

    try:
        report = await service.generate_trend_analysis(request)
        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}",
        )


@router.get(
    "/trends/{rep_id}",
    response_model=TrendAnalysisReport,
    summary="Get rep trend analysis",
    description="Get trend analysis for a specific rep with default parameters.",
)
async def get_rep_trends(
    rep_id: UUID,
    start_date: Optional[datetime] = Query(default=None, description="Start of analysis period"),
    end_date: Optional[datetime] = Query(default=None, description="End of analysis period"),
    min_calls: int = Query(default=3, ge=3, le=50, description="Minimum calls for analysis"),
) -> TrendAnalysisReport:
    """
    Get trend analysis for a rep using query parameters.

    Args:
        rep_id: UUID of the sales rep
        start_date: Optional start of analysis period
        end_date: Optional end of analysis period
        min_calls: Minimum calls required (default 3)

    Returns:
        Trend analysis report
    """
    request = TrendAnalysisRequest(
        rep_id=rep_id,
        start_date=start_date,
        end_date=end_date,
        min_calls=min_calls,
    )

    service = get_coaching_service()

    try:
        return await service.generate_trend_analysis(request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Team Benchmarking Endpoints
# ============================================================================

@router.post(
    "/benchmark",
    response_model=TeamBenchmarkReport,
    summary="Generate team benchmark",
    description="Compare SPICED scores across team members.",
)
async def generate_benchmark(
    request: TeamBenchmarkRequest,
) -> TeamBenchmarkReport:
    """
    Generate a team benchmarking report.

    Compares individual performance against team averages and identifies:
    - High performers, solid performers, and developing reps
    - Individual strengths and gaps relative to team
    - Mentoring opportunities
    - Best practices from top performers
    - Recommended team actions

    Args:
        request: Team benchmark request with team info and rep IDs

    Returns:
        Comprehensive team benchmark report
    """
    service = get_coaching_service()

    try:
        report = await service.generate_team_benchmark(request)
        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmarking failed: {str(e)}",
        )


# ============================================================================
# Score History Endpoints
# ============================================================================

@router.get(
    "/history/{rep_id}",
    response_model=RepScoreHistory,
    summary="Get score history",
    description="Retrieve complete SPICED score history for a rep.",
)
async def get_score_history(
    rep_id: UUID,
) -> RepScoreHistory:
    """
    Get complete score history for a sales rep.

    Returns all historical SPICED scores with call metadata.

    Args:
        rep_id: UUID of the sales rep

    Returns:
        Complete score history
    """
    service = get_coaching_service()
    history = service._get_score_history(rep_id)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score history found for rep {rep_id}",
        )

    return history


@router.get(
    "/history/{rep_id}/summary",
    response_model=ScoresSummary,
    summary="Get score summary",
    description="Get average scores across all SPICED elements for a rep.",
)
async def get_score_summary(
    rep_id: UUID,
) -> ScoresSummary:
    """
    Get average scores summary for a rep.

    Args:
        rep_id: UUID of the sales rep

    Returns:
        Average scores for each SPICED element
    """
    service = get_coaching_service()
    history = service._get_score_history(rep_id)

    if not history or not history.entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score history found for rep {rep_id}",
        )

    # Calculate averages
    element_totals = {
        "situation": [],
        "pain": [],
        "impact": [],
        "critical_event": [],
        "expected_decision": [],
        "decision_criteria": [],
    }

    for entry in history.entries:
        for element, score in entry.scores.items():
            if element in element_totals:
                element_totals[element].append(score)

    def avg(scores: list) -> float:
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    all_overall = [e.overall_score for e in history.entries]

    return ScoresSummary(
        situation=avg(element_totals["situation"]),
        pain=avg(element_totals["pain"]),
        impact=avg(element_totals["impact"]),
        critical_event=avg(element_totals["critical_event"]),
        expected_decision=avg(element_totals["expected_decision"]),
        decision_criteria=avg(element_totals["decision_criteria"]),
        overall=avg(all_overall),
    )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get(
    "/elements",
    response_model=list[str],
    summary="List SPICED elements",
    description="Get the list of SPICED framework elements.",
)
async def list_elements() -> list[str]:
    """
    Get the list of SPICED framework elements.

    Returns the six elements that make up the SPICED framework:
    - Situation
    - Pain
    - Impact
    - Critical Event
    - Expected Decision
    - Decision Criteria
    """
    return [element.value for element in SPICEDElement]


@router.get(
    "/call-types",
    response_model=list[str],
    summary="List call types",
    description="Get the list of supported call types.",
)
async def list_call_types() -> list[str]:
    """
    Get the list of supported call types for analysis.
    """
    return [call_type.value for call_type in CallType]


@router.get(
    "/scoring-rubric",
    summary="Get scoring rubric",
    description="Get the SPICED scoring rubric and descriptions.",
)
async def get_scoring_rubric() -> dict:
    """
    Get the SPICED scoring rubric with descriptions for each level.
    """
    return {
        "scale": {
            "1": "Not addressed at all",
            "2": "Mentioned superficially, not validated",
            "3": "Adequately covered with moderate depth",
            "4": "Well-developed with good detail",
            "5": "Exceptional - deep, quantified, actionable insights",
        },
        "elements": {
            "situation": {
                "description": "Understanding of prospect's current state, processes, tools, team structure",
                "key_questions": [
                    "Walk me through how you currently handle [process]?",
                    "What tools/systems are you using today?",
                    "How many people are involved in this process?",
                ],
            },
            "pain": {
                "description": "Problems, challenges, and frustrations uncovered",
                "key_questions": [
                    "What's not working well with your current approach?",
                    "What are the biggest challenges you're facing?",
                    "What keeps you up at night about [area]?",
                ],
            },
            "impact": {
                "description": "Business consequences quantified - cost of inaction, value of solution",
                "key_questions": [
                    "How is this impacting your business/team?",
                    "What does this cost you in terms of time/money/resources?",
                    "If this problem continues, what happens?",
                ],
            },
            "critical_event": {
                "description": "Timeline driver, urgency, specific deadline or trigger",
                "key_questions": [
                    "Is there a specific date or event driving this?",
                    "What happens if you don't solve this by [date]?",
                    "What's prompting you to look at this now?",
                ],
            },
            "expected_decision": {
                "description": "Decision process, stakeholders, authority, next steps",
                "key_questions": [
                    "Who else is involved in this decision?",
                    "Walk me through your typical evaluation process...",
                    "Who has final sign-off authority?",
                ],
            },
            "decision_criteria": {
                "description": "Requirements, evaluation metrics, success criteria",
                "key_questions": [
                    "What are the must-have requirements?",
                    "How will you evaluate potential solutions?",
                    "What does success look like for this project?",
                ],
            },
        },
    }
