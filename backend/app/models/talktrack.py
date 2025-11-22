"""
Talk Track and Script Models

Models for the talk track generator supporting WbD methodology-aligned
scripts for discovery calls, demos, objection handling, closing, and follow-ups.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ScriptType(str, Enum):
    """Types of sales scripts that can be generated."""
    DISCOVERY_CALL = "discovery_call"
    DEMO_SCRIPT = "demo_script"
    OBJECTION_RESPONSE = "objection_response"
    CLOSING_CONVERSATION = "closing_conversation"
    FOLLOW_UP_GUIDE = "follow_up_guide"


class PersonaType(str, Enum):
    """Buyer persona types for script customization."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    END_USER = "end_user"
    CHAMPION = "champion"
    ECONOMIC_BUYER = "economic_buyer"


class Industry(str, Enum):
    """Industry verticals for language customization."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    EDUCATION = "education"
    GOVERNMENT = "government"
    MEDIA_ENTERTAINMENT = "media_entertainment"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class DealStage(str, Enum):
    """Sales deal stages aligned with typical CRM stages."""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    DISCOVERY = "discovery"
    DEMO = "demo"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class SPICEDElement(str, Enum):
    """WbD SPICED framework elements."""
    SITUATION = "situation"
    PAIN = "pain"
    IMPACT = "impact"
    CRITICAL_EVENT = "critical_event"
    EXPECTED_DECISION = "expected_decision"
    DECISION_CRITERIA = "decision_criteria"


# ============================================================================
# Request/Input Models
# ============================================================================

class ProspectContext(BaseModel):
    """Context about the prospect for personalization."""
    name: Optional[str] = Field(None, description="Prospect's name")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    company_size: Optional[str] = Field(None, description="Company size range")
    industry: Industry = Field(Industry.OTHER, description="Industry vertical")
    known_pain_points: List[str] = Field(default_factory=list, description="Known pain points")
    previous_interactions: Optional[str] = Field(None, description="Summary of previous interactions")


class ProductContext(BaseModel):
    """Context about the product/solution being sold."""
    name: str = Field(..., description="Product or solution name")
    key_features: List[str] = Field(default_factory=list, description="Key features to highlight")
    value_propositions: List[str] = Field(default_factory=list, description="Core value propositions")
    differentiators: List[str] = Field(default_factory=list, description="Competitive differentiators")
    pricing_info: Optional[str] = Field(None, description="High-level pricing context")


class ObjectionContext(BaseModel):
    """Context for objection handling scripts."""
    objection: str = Field(..., description="The specific objection to address")
    objection_category: Optional[str] = Field(None, description="Category: price, timing, competition, etc.")
    competitor_mentioned: Optional[str] = Field(None, description="Competitor if mentioned")


class TalkTrackRequest(BaseModel):
    """Request to generate a talk track or script."""
    script_type: ScriptType = Field(..., description="Type of script to generate")
    persona: PersonaType = Field(PersonaType.CHAMPION, description="Target buyer persona")
    industry: Industry = Field(Industry.OTHER, description="Industry for language customization")
    deal_stage: DealStage = Field(DealStage.DISCOVERY, description="Current deal stage")

    # Context
    prospect: Optional[ProspectContext] = Field(None, description="Prospect context")
    product: Optional[ProductContext] = Field(None, description="Product context")
    objection: Optional[ObjectionContext] = Field(None, description="Objection context (for objection scripts)")

    # SPICED context
    spiced_context: Optional[Dict[str, str]] = Field(
        None,
        description="Known SPICED elements from previous discovery"
    )

    # Customization options
    tone: str = Field("professional", description="Tone: professional, casual, consultative, urgent")
    call_duration_minutes: Optional[int] = Field(None, description="Expected call duration")
    generate_variants: bool = Field(False, description="Generate A/B variants")
    include_coaching_notes: bool = Field(True, description="Include coaching tips")

    class Config:
        json_schema_extra = {
            "example": {
                "script_type": "discovery_call",
                "persona": "executive",
                "industry": "technology",
                "deal_stage": "discovery",
                "prospect": {
                    "name": "Sarah Johnson",
                    "title": "VP of Sales",
                    "company": "TechCorp",
                    "company_size": "500-1000",
                    "industry": "technology"
                },
                "product": {
                    "name": "Sales OS",
                    "key_features": ["AI transcript analysis", "Automated coaching"],
                    "value_propositions": ["Save 5+ hours per week", "Improve win rates 20%"]
                },
                "tone": "consultative",
                "generate_variants": True
            }
        }


# ============================================================================
# Script Section Models
# ============================================================================

class ScriptSection(BaseModel):
    """A section of a talk track script."""
    name: str = Field(..., description="Section name")
    duration_seconds: Optional[int] = Field(None, description="Suggested duration")
    content: str = Field(..., description="Script content")
    coaching_notes: Optional[str] = Field(None, description="Tips for delivery")
    spiced_elements: List[SPICEDElement] = Field(
        default_factory=list,
        description="SPICED elements this section addresses"
    )
    transition_phrase: Optional[str] = Field(None, description="Phrase to transition to next section")


class DiscoveryQuestion(BaseModel):
    """A discovery question aligned with SPICED framework."""
    question: str = Field(..., description="The question to ask")
    spiced_element: SPICEDElement = Field(..., description="Which SPICED element this uncovers")
    follow_up_questions: List[str] = Field(default_factory=list, description="Follow-up questions")
    what_to_listen_for: str = Field(..., description="Key signals to listen for")
    coaching_tip: Optional[str] = Field(None, description="Coaching tip for asking this question")


class ObjectionResponse(BaseModel):
    """A response to a specific objection."""
    objection: str = Field(..., description="The objection being addressed")
    category: str = Field(..., description="Objection category")
    response: str = Field(..., description="Recommended response")
    acknowledge_phrase: str = Field(..., description="Phrase to acknowledge the objection")
    reframe_strategy: str = Field(..., description="Strategy for reframing")
    transition_to_value: str = Field(..., description="How to redirect to value")
    proof_points: List[str] = Field(default_factory=list, description="Evidence to support response")


# ============================================================================
# Output/Response Models
# ============================================================================

class TalkTrack(BaseModel):
    """A complete talk track or script."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    script_type: ScriptType = Field(..., description="Type of script")
    version: str = Field("1.0", description="Script version")
    variant: Optional[str] = Field(None, description="A/B variant identifier")

    # Metadata
    title: str = Field(..., description="Script title")
    description: Optional[str] = Field(None, description="Script description")
    persona: PersonaType = Field(..., description="Target persona")
    industry: Industry = Field(..., description="Target industry")
    deal_stage: DealStage = Field(..., description="Target deal stage")

    # Script content
    opening: ScriptSection = Field(..., description="Opening section")
    sections: List[ScriptSection] = Field(default_factory=list, description="Main script sections")
    closing: ScriptSection = Field(..., description="Closing section")

    # Type-specific content
    discovery_questions: Optional[List[DiscoveryQuestion]] = Field(
        None,
        description="Discovery questions (for discovery scripts)"
    )
    objection_responses: Optional[List[ObjectionResponse]] = Field(
        None,
        description="Objection responses (for objection scripts)"
    )

    # Coaching
    key_tips: List[str] = Field(default_factory=list, description="Key coaching tips")
    common_mistakes: List[str] = Field(default_factory=list, description="Common mistakes to avoid")
    success_metrics: List[str] = Field(default_factory=list, description="What good looks like")

    # Timing
    total_duration_minutes: Optional[int] = Field(None, description="Total suggested duration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TalkTrackResponse(BaseModel):
    """Response containing generated talk track(s)."""
    primary: TalkTrack = Field(..., description="Primary talk track")
    variants: List[TalkTrack] = Field(default_factory=list, description="A/B variants if requested")
    generation_metadata: Dict = Field(default_factory=dict, description="Generation metadata")


# ============================================================================
# Performance Tracking Models
# ============================================================================

class ScriptUsageEvent(BaseModel):
    """Record of a script being used."""
    id: UUID = Field(default_factory=uuid4)
    talktrack_id: UUID = Field(..., description="ID of the talk track used")
    user_id: UUID = Field(..., description="User who used the script")
    deal_id: Optional[UUID] = Field(None, description="Associated deal ID")

    # Usage context
    used_at: datetime = Field(default_factory=datetime.utcnow)
    call_duration_minutes: Optional[int] = Field(None)
    variant_used: Optional[str] = Field(None, description="A/B variant if applicable")

    # Outcome tracking
    outcome: Optional[str] = Field(None, description="Call outcome")
    next_step_scheduled: bool = Field(False)
    deal_advanced: bool = Field(False)

    # Qualitative feedback
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating 1-5")
    user_notes: Optional[str] = Field(None, description="User feedback")


class ScriptPerformanceMetrics(BaseModel):
    """Performance metrics for a talk track."""
    talktrack_id: UUID = Field(..., description="Talk track ID")

    # Usage stats
    total_uses: int = Field(0, description="Total times used")
    unique_users: int = Field(0, description="Unique users")

    # Outcome metrics
    meetings_scheduled_rate: float = Field(0.0, description="% resulting in scheduled meeting")
    deal_advancement_rate: float = Field(0.0, description="% that advanced the deal")
    average_call_duration: Optional[float] = Field(None, description="Average call duration in minutes")

    # A/B test results
    variant_performance: Optional[Dict[str, Dict]] = Field(
        None,
        description="Performance by variant"
    )

    # User feedback
    average_rating: Optional[float] = Field(None, description="Average user rating")

    # Time range
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)


class TalkTrackLibraryItem(BaseModel):
    """Talk track summary for library listing."""
    id: UUID = Field(...)
    title: str = Field(...)
    script_type: ScriptType = Field(...)
    persona: PersonaType = Field(...)
    industry: Industry = Field(...)
    version: str = Field(...)
    total_uses: int = Field(0)
    average_rating: Optional[float] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)


class TalkTrackLibrary(BaseModel):
    """Collection of talk tracks in the library."""
    items: List[TalkTrackLibraryItem] = Field(default_factory=list)
    total: int = Field(0)
    page: int = Field(1)
    page_size: int = Field(20)
