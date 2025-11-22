"""SPICED methodology data models.

SPICED is a sales methodology framework that structures discovery conversations:
- Situation: Current state, context, background
- Pain: Problems, challenges, frustrations
- Impact: Business impact, consequences of the pain
- Critical Event: Timeline drivers, urgency, deadlines
- Expected Decision: Decision process, stakeholders, criteria
- Decision Criteria: How they'll evaluate solutions
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for extracted information."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_FOUND = "not_found"


class Situation(BaseModel):
    """Current state and context of the prospect.

    Captures the background, current tools/processes, team structure,
    and any relevant context about their current situation.
    """

    summary: str = Field(
        ...,
        description="Brief summary of the prospect's current situation",
    )
    current_tools: list[str] = Field(
        default_factory=list,
        description="Current tools or solutions they're using",
    )
    team_size: Optional[str] = Field(
        default=None,
        description="Team size or structure if mentioned",
    )
    industry_context: Optional[str] = Field(
        default=None,
        description="Industry-specific context or challenges",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class Pain(BaseModel):
    """Problems, challenges, and frustrations experienced by the prospect.

    Captures the specific pain points that are driving them to seek a solution.
    """

    primary_pain: str = Field(
        ...,
        description="The main pain point or challenge",
    )
    secondary_pains: list[str] = Field(
        default_factory=list,
        description="Additional pain points mentioned",
    )
    symptoms: list[str] = Field(
        default_factory=list,
        description="Observable symptoms of the pain",
    )
    root_causes: list[str] = Field(
        default_factory=list,
        description="Underlying root causes if identified",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class Impact(BaseModel):
    """Business impact and consequences of the pain.

    Captures the quantifiable and qualitative effects of the problem.
    """

    business_impact: str = Field(
        ...,
        description="Summary of the business impact",
    )
    quantified_impact: Optional[str] = Field(
        default=None,
        description="Quantified impact (revenue, time, costs) if mentioned",
    )
    affected_areas: list[str] = Field(
        default_factory=list,
        description="Business areas affected (revenue, productivity, morale, etc.)",
    )
    stakeholders_affected: list[str] = Field(
        default_factory=list,
        description="People or teams affected by the problem",
    )
    opportunity_cost: Optional[str] = Field(
        default=None,
        description="Opportunity cost of not solving the problem",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class CriticalEvent(BaseModel):
    """Timeline drivers and urgency factors.

    Captures deadlines, events, or triggers creating urgency.
    """

    summary: str = Field(
        ...,
        description="Summary of the critical event or timeline",
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Specific deadline if mentioned",
    )
    trigger_events: list[str] = Field(
        default_factory=list,
        description="Events triggering the need for change",
    )
    consequences_of_delay: Optional[str] = Field(
        default=None,
        description="What happens if they don't act in time",
    )
    urgency_level: Optional[str] = Field(
        default=None,
        description="Assessed urgency level (high/medium/low)",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class ExpectedDecision(BaseModel):
    """Decision process and criteria information.

    Captures how the buying decision will be made and who's involved.
    """

    summary: str = Field(
        ...,
        description="Summary of the expected decision process",
    )
    decision_maker: Optional[str] = Field(
        default=None,
        description="Primary decision maker if identified",
    )
    stakeholders: list[str] = Field(
        default_factory=list,
        description="Other stakeholders involved in the decision",
    )
    decision_timeline: Optional[str] = Field(
        default=None,
        description="Expected timeline for making a decision",
    )
    approval_process: Optional[str] = Field(
        default=None,
        description="How decisions get approved in their organization",
    )
    budget_authority: Optional[str] = Field(
        default=None,
        description="Information about budget and authority",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class DecisionCriteria(BaseModel):
    """How the prospect will evaluate solutions.

    Captures the criteria, requirements, and priorities for choosing a solution.
    """

    summary: str = Field(
        ...,
        description="Summary of how they'll evaluate solutions",
    )
    must_haves: list[str] = Field(
        default_factory=list,
        description="Required features or capabilities",
    )
    nice_to_haves: list[str] = Field(
        default_factory=list,
        description="Desired but not required features",
    )
    deal_breakers: list[str] = Field(
        default_factory=list,
        description="Things that would disqualify a solution",
    )
    evaluation_criteria: list[str] = Field(
        default_factory=list,
        description="How they'll compare options",
    )
    competitors_considered: list[str] = Field(
        default_factory=list,
        description="Other solutions they're evaluating",
    )
    key_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes that support this analysis",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level in this extraction",
    )


class SPICEDConfidence(BaseModel):
    """Overall confidence scores for SPICED extraction."""

    overall: ConfidenceLevel = Field(
        ...,
        description="Overall confidence in the SPICED analysis",
    )
    situation: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    pain: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    impact: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    critical_event: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    expected_decision: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    decision_criteria: ConfidenceLevel = Field(default=ConfidenceLevel.NOT_FOUND)
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How complete the SPICED analysis is (0-1)",
    )


class SPICEDAnalysis(BaseModel):
    """Complete SPICED analysis extracted from a sales conversation.

    This is the primary output of the transcript analysis, containing
    structured information about each SPICED component.
    """

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this analysis",
    )
    transcript_id: Optional[str] = Field(
        default=None,
        description="ID of the source transcript",
    )
    situation: Situation = Field(
        ...,
        description="Current state and context",
    )
    pain: Pain = Field(
        ...,
        description="Problems, challenges, and frustrations",
    )
    impact: Impact = Field(
        ...,
        description="Business impact and consequences",
    )
    critical_event: CriticalEvent = Field(
        ...,
        description="Timeline drivers and urgency",
    )
    expected_decision: ExpectedDecision = Field(
        ...,
        description="Decision process information",
    )
    decision_criteria: DecisionCriteria = Field(
        ...,
        description="Solution evaluation criteria",
    )
    confidence: SPICEDConfidence = Field(
        ...,
        description="Confidence scores for the analysis",
    )
    gaps_identified: list[str] = Field(
        default_factory=list,
        description="Information gaps that need follow-up",
    )
    coaching_notes: list[str] = Field(
        default_factory=list,
        description="Notes for sales coaching",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this analysis was created",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "situation": {
                    "summary": "Mid-size SaaS company with 50-person sales team",
                    "current_tools": ["Salesforce", "Outreach", "Gong"],
                    "team_size": "50 sales reps",
                    "confidence": "high",
                },
                "pain": {
                    "primary_pain": "Reps spending too much time on admin tasks",
                    "secondary_pains": ["Poor CRM data quality", "Inconsistent follow-up"],
                    "confidence": "high",
                },
                "impact": {
                    "business_impact": "20% of selling time lost to admin work",
                    "quantified_impact": "$2M in lost revenue opportunity",
                    "confidence": "medium",
                },
                "critical_event": {
                    "summary": "Q4 planning deadline requires decision by end of month",
                    "deadline": "October 31",
                    "urgency_level": "high",
                    "confidence": "high",
                },
                "expected_decision": {
                    "summary": "VP Sales makes final call with CFO budget approval",
                    "decision_maker": "VP of Sales",
                    "stakeholders": ["CFO", "Sales Ops Manager"],
                    "confidence": "medium",
                },
                "decision_criteria": {
                    "summary": "Looking for ROI within 6 months, easy integration",
                    "must_haves": ["Salesforce integration", "Mobile app"],
                    "nice_to_haves": ["AI recommendations"],
                    "confidence": "medium",
                },
            }
        }
