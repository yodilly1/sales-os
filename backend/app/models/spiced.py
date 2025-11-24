"""SPICED methodology Pydantic models for extraction and analysis.

These models are used by the SPICEDExtractor service to structure
the AI-extracted information from sales call transcripts.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for extracted information."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_FOUND = "not_found"


class Situation(BaseModel):
    """Current situation of the prospect."""
    summary: str = Field(..., description="Summary of the current situation")
    current_tools: List[str] = Field(default_factory=list, description="Current tools/solutions in use")
    team_size: Optional[str] = Field(None, description="Size of the team")
    industry_context: Optional[str] = Field(None, description="Industry-specific context")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class Pain(BaseModel):
    """Pain points identified from the transcript."""
    primary_pain: str = Field(..., description="Primary pain point")
    secondary_pains: List[str] = Field(default_factory=list, description="Secondary pain points")
    symptoms: List[str] = Field(default_factory=list, description="Symptoms of the pain")
    root_causes: List[str] = Field(default_factory=list, description="Root causes identified")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class Impact(BaseModel):
    """Business impact of the pain points."""
    business_impact: str = Field(..., description="Description of business impact")
    quantified_impact: Optional[str] = Field(None, description="Quantified impact (dollars, time, etc.)")
    affected_areas: List[str] = Field(default_factory=list, description="Business areas affected")
    stakeholders_affected: List[str] = Field(default_factory=list, description="Stakeholders impacted")
    opportunity_cost: Optional[str] = Field(None, description="Opportunity cost of inaction")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class CriticalEvent(BaseModel):
    """Critical event or timeline driving the decision."""
    summary: str = Field(..., description="Summary of the critical event")
    deadline: Optional[str] = Field(None, description="Key deadline")
    trigger_events: List[str] = Field(default_factory=list, description="Events that triggered the search")
    consequences_of_delay: Optional[str] = Field(None, description="What happens if delayed")
    urgency_level: Optional[str] = Field(None, description="Level of urgency (high/medium/low)")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class ExpectedDecision(BaseModel):
    """Expected decision process and stakeholders."""
    summary: str = Field(..., description="Summary of decision process")
    decision_maker: Optional[str] = Field(None, description="Primary decision maker")
    stakeholders: List[str] = Field(default_factory=list, description="Other stakeholders involved")
    decision_timeline: Optional[str] = Field(None, description="Expected timeline for decision")
    approval_process: Optional[str] = Field(None, description="Approval process description")
    budget_authority: Optional[str] = Field(None, description="Who controls the budget")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class DecisionCriteria(BaseModel):
    """Criteria the prospect will use to make their decision."""
    summary: str = Field(..., description="Summary of decision criteria")
    must_haves: List[str] = Field(default_factory=list, description="Required features/capabilities")
    nice_to_haves: List[str] = Field(default_factory=list, description="Desired but not required")
    deal_breakers: List[str] = Field(default_factory=list, description="Things that would prevent a deal")
    evaluation_criteria: List[str] = Field(default_factory=list, description="How they will evaluate")
    competitors_considered: List[str] = Field(default_factory=list, description="Competitors being evaluated")
    key_quotes: List[str] = Field(default_factory=list, description="Supporting quotes from transcript")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Confidence in extraction")


class SPICEDConfidence(BaseModel):
    """Confidence scores for the entire SPICED analysis."""
    overall: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Overall confidence")
    situation: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Situation confidence")
    pain: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Pain confidence")
    impact: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Impact confidence")
    critical_event: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Critical event confidence")
    expected_decision: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Expected decision confidence")
    decision_criteria: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Decision criteria confidence")
    completeness_score: float = Field(default=0.5, ge=0.0, le=1.0, description="How complete the analysis is")


class SPICEDAnalysis(BaseModel):
    """Complete SPICED analysis extracted from a transcript."""
    id: str = Field(..., description="Unique analysis ID")
    transcript_id: Optional[str] = Field(None, description="ID of source transcript")

    # SPICED components
    situation: Situation
    pain: Pain
    impact: Impact
    critical_event: CriticalEvent
    expected_decision: ExpectedDecision
    decision_criteria: DecisionCriteria

    # Meta information
    confidence: SPICEDConfidence
    gaps_identified: List[str] = Field(default_factory=list, description="Information gaps identified")
    coaching_notes: List[str] = Field(default_factory=list, description="Coaching suggestions")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="When analysis was created")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
