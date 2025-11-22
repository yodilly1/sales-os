"""
Coaching Models for SPICED Framework Analysis

This module defines Pydantic models for the coaching service, including:
- SPICED element scores and evidence
- Per-call coaching feedback
- Trend analysis over time
- Team benchmarking
- Gap analysis and improvement recommendations
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SPICEDElement(str, Enum):
    """The six elements of the SPICED framework."""

    SITUATION = "situation"
    PAIN = "pain"
    IMPACT = "impact"
    CRITICAL_EVENT = "critical_event"
    EXPECTED_DECISION = "expected_decision"
    DECISION_CRITERIA = "decision_criteria"


class CallType(str, Enum):
    """Types of sales calls."""

    DISCOVERY = "discovery"
    DEMO = "demo"
    QUALIFICATION = "qualification"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"
    CHECK_IN = "check_in"
    OTHER = "other"


class TrendDirection(str, Enum):
    """Direction of score trends over time."""

    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


class PerformanceTier(str, Enum):
    """Performance tier classifications."""

    HIGH_PERFORMER = "high_performer"  # >= 4.0 avg
    SOLID_PERFORMER = "solid_performer"  # 3.0 - 3.9 avg
    DEVELOPING = "developing"  # < 3.0 avg


# ============================================================================
# SPICED Element Scoring Models
# ============================================================================

class ElementScore(BaseModel):
    """Score for a single SPICED element with justification."""

    element: SPICEDElement
    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    justification: str = Field(..., min_length=10, description="Brief explanation for the score")
    evidence: list[str] = Field(default_factory=list, description="Quotes from transcript supporting the score")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Score must be between 1 and 5")
        return v


class SPICEDScores(BaseModel):
    """Complete SPICED scoring for a call."""

    situation: ElementScore
    pain: ElementScore
    impact: ElementScore
    critical_event: ElementScore
    expected_decision: ElementScore
    decision_criteria: ElementScore

    @property
    def overall_score(self) -> float:
        """Calculate average of all element scores."""
        scores = [
            self.situation.score,
            self.pain.score,
            self.impact.score,
            self.critical_event.score,
            self.expected_decision.score,
            self.decision_criteria.score,
        ]
        return round(sum(scores) / len(scores), 2)

    @property
    def scores_dict(self) -> dict[str, int]:
        """Return scores as a simple dictionary."""
        return {
            "situation": self.situation.score,
            "pain": self.pain.score,
            "impact": self.impact.score,
            "critical_event": self.critical_event.score,
            "expected_decision": self.expected_decision.score,
            "decision_criteria": self.decision_criteria.score,
        }


# ============================================================================
# Coaching Feedback Models
# ============================================================================

class Strength(BaseModel):
    """A strength identified in the call."""

    title: str = Field(..., min_length=3, description="Name of the strength")
    description: str = Field(..., description="What the rep did well")
    example: str = Field(..., description="Specific quote or moment demonstrating this")


class ImprovementArea(BaseModel):
    """An area for improvement with actionable guidance."""

    title: str = Field(..., min_length=3, description="Name of the improvement area")
    gap: str = Field(..., description="What was missed or could be better")
    suggested_question: str = Field(..., description="Specific question to ask next time")
    impact: str = Field(..., description="Why this improvement matters")


class CoachingTip(BaseModel):
    """A WbD-aligned coaching tip."""

    tip: str = Field(..., description="The coaching tip")
    rationale: str = Field(..., description="Why this helps")
    practice_exercise: str = Field(..., description="How to practice this skill")


class TalkTrack(BaseModel):
    """A suggested talk track for future calls."""

    situation: str = Field(..., description="When to use this talk track")
    script: str = Field(..., description="Exact words to say")
    purpose: str = Field(..., description="What this achieves")


class CoachingSummary(BaseModel):
    """Overall summary of coaching feedback."""

    overall_assessment: str = Field(..., description="2-3 sentence summary of call quality")
    priority_focus: str = Field(..., description="Single most important improvement area")
    next_call_goal: str = Field(..., description="Specific goal for the next call")


class CoachingFeedback(BaseModel):
    """Complete coaching feedback for a single call."""

    scores: SPICEDScores
    overall_score: float = Field(..., ge=1.0, le=5.0)
    strengths: list[Strength] = Field(..., min_length=1, max_length=5)
    improvements: list[ImprovementArea] = Field(..., min_length=1, max_length=5)
    coaching_tips: list[CoachingTip] = Field(..., min_length=1, max_length=5)
    talk_tracks: list[TalkTrack] = Field(default_factory=list, max_length=3)
    summary: CoachingSummary


# ============================================================================
# Per-Call Report Models
# ============================================================================

class CallMetadata(BaseModel):
    """Metadata about the analyzed call."""

    call_id: UUID = Field(default_factory=uuid4)
    rep_id: UUID
    rep_name: str
    call_type: CallType = CallType.DISCOVERY
    prospect_company: Optional[str] = None
    prospect_name: Optional[str] = None
    call_duration_minutes: Optional[int] = None
    call_date: datetime = Field(default_factory=datetime.utcnow)
    transcript_source: Optional[str] = None  # e.g., "avoma", "zoom", "teams"


class CoachingReport(BaseModel):
    """Complete coaching report for a single call."""

    id: UUID = Field(default_factory=uuid4)
    metadata: CallMetadata
    feedback: CoachingFeedback
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional: Previous scores for context
    previous_scores: Optional[list[float]] = Field(
        default=None,
        description="Last 3-5 overall scores for trend context"
    )


# ============================================================================
# Trend Analysis Models
# ============================================================================

class ElementTrend(BaseModel):
    """Trend data for a single SPICED element."""

    element: SPICEDElement
    direction: TrendDirection
    start_avg: float = Field(..., ge=1.0, le=5.0)
    end_avg: float = Field(..., ge=1.0, le=5.0)
    change: float = Field(..., description="Positive or negative change amount")
    consistency: str = Field(..., description="steady or volatile")
    scores_history: list[float] = Field(default_factory=list, description="Historical scores")


class StrongestArea(BaseModel):
    """A rep's strongest SPICED element."""

    element: SPICEDElement
    avg_score: float = Field(..., ge=1.0, le=5.0)
    insight: str = Field(..., description="Why they excel in this area")


class ImprovementFocus(BaseModel):
    """A prioritized area for improvement."""

    element: SPICEDElement
    avg_score: float = Field(..., ge=1.0, le=5.0)
    gap_analysis: str = Field(..., description="What's missing")
    recommended_action: str = Field(..., description="Specific action to improve")


class TrendPattern(BaseModel):
    """An observed pattern in the rep's performance."""

    pattern: str = Field(..., description="The observed pattern")
    insight: str = Field(..., description="What this means")
    recommendation: str = Field(..., description="How to leverage or address")


class ImprovementGoal(BaseModel):
    """A specific improvement goal with timeline."""

    element: SPICEDElement
    current_avg: float = Field(..., ge=1.0, le=5.0)
    target_score: float = Field(..., ge=1.0, le=5.0)
    timeframe: str = Field(..., description="e.g., '4 weeks', '1 month'")
    action_plan: str = Field(..., description="Specific steps to achieve goal")


class TrendAnalysisReport(BaseModel):
    """Complete trend analysis for a rep over time."""

    id: UUID = Field(default_factory=uuid4)
    rep_id: UUID
    rep_name: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_calls_analyzed: int = Field(..., ge=1)

    element_trends: dict[SPICEDElement, ElementTrend]
    overall_trend: TrendDirection
    overall_avg_start: float = Field(..., ge=1.0, le=5.0)
    overall_avg_end: float = Field(..., ge=1.0, le=5.0)

    strongest_areas: list[StrongestArea] = Field(..., max_length=3)
    improvement_areas: list[ImprovementFocus] = Field(..., max_length=3)
    patterns: list[TrendPattern] = Field(default_factory=list, max_length=5)
    goals: list[ImprovementGoal] = Field(default_factory=list, max_length=3)

    next_review_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Team Benchmarking Models
# ============================================================================

class TeamElementAverages(BaseModel):
    """Average scores for each SPICED element across the team."""

    situation: float = Field(..., ge=1.0, le=5.0)
    pain: float = Field(..., ge=1.0, le=5.0)
    impact: float = Field(..., ge=1.0, le=5.0)
    critical_event: float = Field(..., ge=1.0, le=5.0)
    expected_decision: float = Field(..., ge=1.0, le=5.0)
    decision_criteria: float = Field(..., ge=1.0, le=5.0)


class PerformanceDistribution(BaseModel):
    """Distribution of reps across performance tiers."""

    high_performers: list[str] = Field(default_factory=list, description="Rep names with avg >= 4.0")
    solid_performers: list[str] = Field(default_factory=list, description="Rep names with avg 3.0-3.9")
    developing: list[str] = Field(default_factory=list, description="Rep names with avg < 3.0")


class IndividualBenchmark(BaseModel):
    """Individual rep benchmarked against team."""

    rep_id: UUID
    rep_name: str
    overall_avg: float = Field(..., ge=1.0, le=5.0)
    percentile: int = Field(..., ge=0, le=100)
    tier: PerformanceTier
    strengths: list[SPICEDElement] = Field(..., description="Elements above team avg")
    gaps: list[SPICEDElement] = Field(..., description="Elements below team avg")
    priority_focus: str = Field(..., description="Most important improvement area")
    calls_analyzed: int = Field(..., ge=1)


class MentoringOpportunity(BaseModel):
    """A suggested mentoring pairing."""

    mentor_name: str
    mentor_id: UUID
    skill: SPICEDElement
    mentees: list[str] = Field(..., description="Names of reps who could benefit")


class BestPractice(BaseModel):
    """A best practice from top performers."""

    technique: str = Field(..., description="What works")
    example_rep: str = Field(..., description="Who does this well")
    talk_track: str = Field(..., description="Specific example")
    applicable_to: SPICEDElement


class TeamBenchmarkReport(BaseModel):
    """Complete team benchmarking report."""

    id: UUID = Field(default_factory=uuid4)
    team_id: UUID
    team_name: str

    total_reps: int = Field(..., ge=1)
    total_calls_analyzed: int = Field(..., ge=1)
    analysis_period_start: datetime
    analysis_period_end: datetime

    avg_overall_score: float = Field(..., ge=1.0, le=5.0)
    element_averages: TeamElementAverages
    performance_distribution: PerformanceDistribution

    individual_benchmarks: list[IndividualBenchmark]

    strongest_element: SPICEDElement
    strongest_element_score: float = Field(..., ge=1.0, le=5.0)
    weakest_element: SPICEDElement
    weakest_element_score: float = Field(..., ge=1.0, le=5.0)
    recommended_training: str = Field(..., description="Team-wide training recommendation")

    mentoring_opportunities: list[MentoringOpportunity] = Field(default_factory=list)
    best_practices: list[BestPractice] = Field(default_factory=list, max_length=5)

    immediate_actions: list[str] = Field(default_factory=list, description="Actions for this week")
    short_term_actions: list[str] = Field(default_factory=list, description="Actions for this month")
    long_term_actions: list[str] = Field(default_factory=list, description="Actions for this quarter")

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Gap Analysis Models
# ============================================================================

class ElementGap(BaseModel):
    """Gap analysis for a single SPICED element."""

    element: SPICEDElement
    known: list[str] = Field(default_factory=list, description="What we learned")
    unknown: list[str] = Field(default_factory=list, description="What we still need")
    critical_gap: str = Field(..., description="Most important missing information")
    recovery_question: str = Field(..., description="Question for next call")


class MissedOpportunity(BaseModel):
    """A specific moment where the rep missed an opportunity."""

    timestamp_or_quote: str = Field(..., description="Moment in call")
    what_was_said: str = Field(..., description="Prospect statement")
    follow_up_missed: str = Field(..., description="Question that should have been asked")
    impact_of_missing: str = Field(..., description="Why this matters")


class QuestionTransition(BaseModel):
    """How to transition to an important question."""

    from_topic: str = Field(..., description="How to bring it up")
    to_question: str = Field(..., description="The question to ask")


class NextCallPlan(BaseModel):
    """Plan for the next call based on gap analysis."""

    priority_questions: list[str] = Field(..., min_length=1, description="Ordered list of questions")
    transitions: list[QuestionTransition] = Field(default_factory=list)


class GapAnalysisReport(BaseModel):
    """Complete gap analysis for a call."""

    id: UUID = Field(default_factory=uuid4)
    call_id: UUID
    rep_id: UUID

    gaps_by_element: dict[SPICEDElement, ElementGap]
    missed_opportunities: list[MissedOpportunity] = Field(default_factory=list, max_length=10)
    next_call_plan: NextCallPlan

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Request/Response Models for API
# ============================================================================

class CoachingRequest(BaseModel):
    """Request to analyze a call for coaching feedback."""

    transcript: str = Field(..., min_length=100, description="Full call transcript")
    rep_id: UUID
    rep_name: str
    call_type: CallType = CallType.DISCOVERY
    prospect_company: Optional[str] = None
    prospect_name: Optional[str] = None
    call_duration_minutes: Optional[int] = None
    call_date: Optional[datetime] = None
    include_gap_analysis: bool = Field(default=True, description="Include detailed gap analysis")


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis over time."""

    rep_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_calls: int = Field(default=3, ge=3, description="Minimum calls required for analysis")


class TeamBenchmarkRequest(BaseModel):
    """Request for team benchmarking analysis."""

    team_id: UUID
    team_name: str
    rep_ids: list[UUID] = Field(..., min_length=2, description="List of rep IDs to include")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BulkCoachingRequest(BaseModel):
    """Request to analyze multiple calls."""

    calls: list[CoachingRequest] = Field(..., min_length=1, max_length=10)


# ============================================================================
# Score History Model (for storage/retrieval)
# ============================================================================

class ScoreHistoryEntry(BaseModel):
    """A single entry in score history."""

    call_id: UUID
    call_date: datetime
    scores: dict[str, int] = Field(..., description="Element name to score mapping")
    overall_score: float = Field(..., ge=1.0, le=5.0)
    call_type: CallType


class RepScoreHistory(BaseModel):
    """Complete score history for a rep."""

    rep_id: UUID
    rep_name: str
    entries: list[ScoreHistoryEntry] = Field(default_factory=list)

    @property
    def total_calls(self) -> int:
        return len(self.entries)

    @property
    def average_overall_score(self) -> Optional[float]:
        if not self.entries:
            return None
        return round(sum(e.overall_score for e in self.entries) / len(self.entries), 2)


# ============================================================================
# Benchmark Targets Configuration
# ============================================================================

class BenchmarkTargets(BaseModel):
    """Target scores by role for benchmarking."""

    sdr_bdr_target: float = Field(default=3.0, ge=1.0, le=5.0)
    ae_smb_target: float = Field(default=3.5, ge=1.0, le=5.0)
    ae_enterprise_target: float = Field(default=4.0, ge=1.0, le=5.0)
    sales_leader_target: float = Field(default=4.5, ge=1.0, le=5.0)


# Default benchmark targets
DEFAULT_BENCHMARK_TARGETS = BenchmarkTargets()
