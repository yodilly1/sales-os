"""SPICED Analysis Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class SPICEDScores(BaseSchema):
    """Individual SPICED scores."""

    situation: Optional[int] = Field(None, ge=1, le=5)
    pain: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    critical_event: Optional[int] = Field(None, ge=1, le=5)
    expected_decision: Optional[int] = Field(None, ge=1, le=5)
    decision_criteria: Optional[int] = Field(None, ge=1, le=5)

    @property
    def average(self) -> Optional[float]:
        """Calculate average score."""
        scores = [
            self.situation,
            self.pain,
            self.impact,
            self.critical_event,
            self.expected_decision,
            self.decision_criteria,
        ]
        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return None
        return sum(valid_scores) / len(valid_scores)


class SPICEDAnalysisBase(BaseSchema):
    """Base SPICED analysis schema."""

    # SPICED Components
    situation: Optional[str] = None
    pain: Optional[str] = None
    impact: Optional[str] = None
    critical_event: Optional[str] = None
    expected_decision: Optional[str] = None
    decision_criteria: Optional[str] = None


class SPICEDAnalysisCreate(SPICEDAnalysisBase):
    """Schema for creating a SPICED analysis."""

    call_id: str


class SPICEDAnalysisUpdate(BaseSchema):
    """Schema for updating a SPICED analysis."""

    situation: Optional[str] = None
    pain: Optional[str] = None
    impact: Optional[str] = None
    critical_event: Optional[str] = None
    expected_decision: Optional[str] = None
    decision_criteria: Optional[str] = None

    # Scores
    situation_score: Optional[int] = Field(None, ge=1, le=5)
    pain_score: Optional[int] = Field(None, ge=1, le=5)
    impact_score: Optional[int] = Field(None, ge=1, le=5)
    critical_event_score: Optional[int] = Field(None, ge=1, le=5)
    expected_decision_score: Optional[int] = Field(None, ge=1, le=5)
    decision_criteria_score: Optional[int] = Field(None, ge=1, le=5)


class SPICEDAnalysisResponse(SPICEDAnalysisBase, IDSchema, TimestampSchema):
    """Schema for SPICED analysis response."""

    call_id: str

    # Scores
    situation_score: Optional[int] = None
    pain_score: Optional[int] = None
    impact_score: Optional[int] = None
    critical_event_score: Optional[int] = None
    expected_decision_score: Optional[int] = None
    decision_criteria_score: Optional[int] = None

    # Overall metrics
    overall_score: Optional[float] = None
    confidence_score: Optional[float] = None

    # Generated content
    call_summary: Optional[str] = None
    call_notes: Optional[str] = None
    follow_up_tasks: Optional[List[str]] = None
    key_quotes: Optional[List[str]] = None
    action_items: Optional[List[str]] = None

    # Gaps and recommendations
    gaps_identified: Optional[List[str]] = None
    recommended_questions: Optional[List[str]] = None

    # Metadata
    model_version: Optional[str] = None
    analyzed_at: Optional[datetime] = None

    @field_validator(
        "follow_up_tasks",
        "key_quotes",
        "action_items",
        "gaps_identified",
        "recommended_questions",
        mode="before",
    )
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields to lists."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @property
    def scores(self) -> SPICEDScores:
        """Get all SPICED scores as a structured object."""
        return SPICEDScores(
            situation=self.situation_score,
            pain=self.pain_score,
            impact=self.impact_score,
            critical_event=self.critical_event_score,
            expected_decision=self.expected_decision_score,
            decision_criteria=self.decision_criteria_score,
        )


class SPICEDExtractionRequest(BaseSchema):
    """Request to extract SPICED analysis from a call."""

    call_id: str
    include_coaching: bool = False
    include_action_items: bool = True
    include_follow_up_tasks: bool = True


class SPICEDExtractionResponse(BaseSchema):
    """Response from SPICED extraction."""

    analysis: SPICEDAnalysisResponse
    processing_time_ms: int
    model_used: str
