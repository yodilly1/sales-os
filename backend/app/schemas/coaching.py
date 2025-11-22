"""Coaching Report and Score Pydantic schemas."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import Field, field_validator

from app.models.coaching import CoachingLevel
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


# ==================== CoachingScore Schemas ====================


class CoachingScoreBase(BaseSchema):
    """Base coaching score schema."""

    component: str = Field(..., pattern="^[SPICED]$")
    score: int = Field(..., ge=1, le=5)


class CoachingScoreCreate(CoachingScoreBase):
    """Schema for creating a coaching score."""

    coaching_report_id: str
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    evidence_quotes: Optional[List[str]] = None
    missed_opportunities: Optional[List[str]] = None
    recommended_questions: Optional[List[str]] = None
    best_practices: Optional[List[str]] = None


class CoachingScoreResponse(CoachingScoreBase, IDSchema, TimestampSchema):
    """Schema for coaching score response."""

    coaching_report_id: str
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    evidence_quotes: Optional[List[str]] = None
    missed_opportunities: Optional[List[str]] = None
    recommended_questions: Optional[List[str]] = None
    best_practices: Optional[List[str]] = None

    @field_validator(
        "strengths",
        "areas_for_improvement",
        "evidence_quotes",
        "missed_opportunities",
        "recommended_questions",
        "best_practices",
        mode="before",
    )
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


# ==================== CoachingReport Schemas ====================


class CoachingReportBase(BaseSchema):
    """Base coaching report schema."""

    overall_score: float = Field(..., ge=1, le=5)
    level: CoachingLevel


class CoachingReportCreate(CoachingReportBase):
    """Schema for creating a coaching report."""

    call_id: str
    user_id: str
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    executive_summary: Optional[str] = None
    key_strengths: Optional[List[str]] = None
    key_improvements: Optional[List[str]] = None
    wbd_methodology_alignment: Optional[float] = Field(None, ge=0, le=1)
    wbd_feedback: Optional[str] = None
    action_items: Optional[List[str]] = None
    learning_resources: Optional[List[str]] = None
    practice_scenarios: Optional[List[str]] = None


class CoachingReportUpdate(BaseSchema):
    """Schema for updating a coaching report."""

    overall_score: Optional[float] = Field(None, ge=1, le=5)
    level: Optional[CoachingLevel] = None
    executive_summary: Optional[str] = None
    key_strengths: Optional[List[str]] = None
    key_improvements: Optional[List[str]] = None
    action_items: Optional[List[str]] = None


class CoachingReportResponse(CoachingReportBase, IDSchema, TimestampSchema):
    """Schema for coaching report response."""

    call_id: str
    user_id: str
    confidence_score: Optional[float] = None

    # Summary
    executive_summary: Optional[str] = None
    key_strengths: Optional[List[str]] = None
    key_improvements: Optional[List[str]] = None

    # WbD alignment
    wbd_methodology_alignment: Optional[float] = None
    wbd_feedback: Optional[str] = None

    # Action items
    action_items: Optional[List[str]] = None
    learning_resources: Optional[List[str]] = None
    practice_scenarios: Optional[List[str]] = None

    # Trend analysis
    improvement_areas: Optional[List[str]] = None
    regression_areas: Optional[List[str]] = None
    trend_summary: Optional[str] = None

    # Metadata
    model_version: Optional[str] = None
    analyzed_at: Optional[datetime] = None

    # Scores
    scores: Optional[List[CoachingScoreResponse]] = None

    @field_validator(
        "key_strengths",
        "key_improvements",
        "action_items",
        "learning_resources",
        "practice_scenarios",
        "improvement_areas",
        "regression_areas",
        mode="before",
    )
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class CoachingAnalysisRequest(BaseSchema):
    """Request to analyze a call for coaching."""

    call_id: str
    include_trend_analysis: bool = True
    compare_with_team: bool = False


class CoachingAnalysisResponse(BaseSchema):
    """Response from coaching analysis."""

    report: CoachingReportResponse
    processing_time_ms: int
    model_used: str


class CoachingTrendRequest(BaseSchema):
    """Request coaching trends for a user."""

    user_id: str
    period_days: int = Field(30, ge=7, le=365)
    include_team_comparison: bool = False


class SPICEDTrendPoint(BaseSchema):
    """Single point in SPICED trend data."""

    date: datetime
    situation: Optional[float] = None
    pain: Optional[float] = None
    impact: Optional[float] = None
    critical_event: Optional[float] = None
    expected_decision: Optional[float] = None
    decision_criteria: Optional[float] = None
    overall: float


class CoachingTrendResponse(BaseSchema):
    """Response with coaching trends."""

    user_id: str
    period_days: int
    trend_data: List[SPICEDTrendPoint]
    average_scores: dict
    improvement_velocity: float
    strongest_components: List[str]
    weakest_components: List[str]
    team_comparison: Optional[dict] = None
