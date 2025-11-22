<<<<<<< HEAD
"""Content generation data models and schemas."""

from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.constants import AudienceType, BrandVoice, ContentStatus, ContentType


# =============================================================================
# Input Models
# =============================================================================


class ProductInfo(BaseModel):
    """Product information for content generation."""

    name: str = Field(..., description="Product or solution name")
    description: str = Field(..., description="Brief product description")
    key_features: list[str] = Field(
        default_factory=list, description="Key product features"
    )
    value_propositions: list[str] = Field(
        default_factory=list, description="Main value propositions"
    )
    pricing_info: Optional[str] = Field(None, description="Pricing information if applicable")
    differentiators: list[str] = Field(
        default_factory=list, description="Key differentiators from competitors"
    )
    use_cases: list[str] = Field(
        default_factory=list, description="Primary use cases"
    )
    customer_segments: list[str] = Field(
        default_factory=list, description="Target customer segments"
    )


class AudienceInfo(BaseModel):
    """Target audience information."""

    audience_type: AudienceType = Field(
        default=AudienceType.VP_DIRECTOR, description="Primary audience type"
    )
    company_name: Optional[str] = Field(None, description="Target company name")
    industry: Optional[str] = Field(None, description="Target industry")
    company_size: Optional[str] = Field(None, description="Company size (e.g., 'Enterprise', 'SMB')")
    pain_points: list[str] = Field(
        default_factory=list, description="Known pain points of the audience"
    )
    priorities: list[str] = Field(
        default_factory=list, description="Known priorities or goals"
    )
    decision_criteria: list[str] = Field(
        default_factory=list, description="How they evaluate solutions"
    )
    stakeholders: list[str] = Field(
        default_factory=list, description="Key stakeholders involved"
    )


class CompetitorInfo(BaseModel):
    """Competitor information for battlecards."""

    name: str = Field(..., description="Competitor name")
    description: Optional[str] = Field(None, description="Brief competitor description")
    strengths: list[str] = Field(
        default_factory=list, description="Competitor strengths"
    )
    weaknesses: list[str] = Field(
        default_factory=list, description="Competitor weaknesses"
    )
    pricing: Optional[str] = Field(None, description="Competitor pricing info")
    common_objections: list[str] = Field(
        default_factory=list, description="Common objections when competing"
    )


class ObjectionInfo(BaseModel):
    """Objection information for objection handling battlecards."""

    objection: str = Field(..., description="The objection text")
    category: Optional[str] = Field(
        None, description="Category (e.g., 'pricing', 'features', 'timing')"
    )
    frequency: Optional[str] = Field(
        None, description="How often this objection comes up"
    )
    context: Optional[str] = Field(
        None, description="When this objection typically arises"
    )


class SPICEDContext(BaseModel):
    """SPICED framework context for WbD alignment."""

    situation: Optional[str] = Field(None, description="Current situation context")
    pain: Optional[str] = Field(None, description="Key pain points identified")
    impact: Optional[str] = Field(None, description="Business impact of the problem")
    critical_event: Optional[str] = Field(None, description="Timeline drivers")
    expected_decision: Optional[str] = Field(None, description="Decision process info")
    decision_criteria: Optional[str] = Field(None, description="Evaluation criteria")


# =============================================================================
# Content Structure Models
# =============================================================================


class DeckSlide(BaseModel):
    """Individual slide in a sales deck."""

    slide_number: int = Field(..., description="Slide number (1-indexed)")
    title: str = Field(..., description="Slide title")
    subtitle: Optional[str] = Field(None, description="Slide subtitle")
    content_type: str = Field(
        default="text", description="Content type: text, bullets, chart, image, quote"
    )
    main_content: Union[str, list[str]] = Field(
        ..., description="Main slide content (text or bullet points)"
    )
    speaker_notes: Optional[str] = Field(None, description="Speaker notes for this slide")
    visual_suggestions: Optional[str] = Field(
        None, description="Suggested visuals or graphics"
    )
    transition_note: Optional[str] = Field(
        None, description="How to transition to next slide"
    )


class DeckContent(BaseModel):
    """Complete sales deck content."""

    title: str = Field(..., description="Deck title")
    subtitle: Optional[str] = Field(None, description="Deck subtitle")
    deck_type: str = Field(..., description="Type: pitch, renewal, qbr")
    slides: list[DeckSlide] = Field(..., description="List of slides")
    total_slides: int = Field(..., description="Total number of slides")
    estimated_duration_minutes: int = Field(
        default=30, description="Estimated presentation duration"
    )
    key_messages: list[str] = Field(
        default_factory=list, description="Key messages to convey"
    )
    call_to_action: str = Field(..., description="Primary call to action")


class ProposalSection(BaseModel):
    """Individual section in a proposal."""

    section_number: int = Field(..., description="Section number")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content (markdown supported)")
    subsections: Optional[list[dict[str, str]]] = Field(
        None, description="Optional subsections"
    )


class ProposalContent(BaseModel):
    """Complete proposal content."""

    title: str = Field(..., description="Proposal title")
    proposal_type: str = Field(..., description="Type: custom, templated")
    executive_summary: str = Field(..., description="Executive summary")
    sections: list[ProposalSection] = Field(..., description="Proposal sections")
    pricing_table: Optional[dict[str, Any]] = Field(
        None, description="Pricing breakdown"
    )
    terms_and_conditions: Optional[str] = Field(
        None, description="Terms and conditions"
    )
    next_steps: list[str] = Field(
        default_factory=list, description="Recommended next steps"
    )
    validity_period: Optional[str] = Field(
        None, description="Proposal validity period"
    )
    signature_block: Optional[dict[str, str]] = Field(
        None, description="Signature block info"
    )


class OnePagerContent(BaseModel):
    """Complete one-pager content."""

    title: str = Field(..., description="One-pager title")
    one_pager_type: str = Field(..., description="Type: product, solution, case_study")
    headline: str = Field(..., description="Main headline")
    subheadline: Optional[str] = Field(None, description="Supporting subheadline")
    overview: str = Field(..., description="Brief overview paragraph")
    key_points: list[dict[str, str]] = Field(
        ..., description="Key points with title and description"
    )
    benefits: list[str] = Field(..., description="Key benefits")
    proof_points: Optional[list[dict[str, str]]] = Field(
        None, description="Stats, quotes, or case study snippets"
    )
    call_to_action: str = Field(..., description="Call to action")
    contact_info: Optional[dict[str, str]] = Field(
        None, description="Contact information"
    )
    # Case study specific fields
    customer_name: Optional[str] = Field(None, description="Customer name for case study")
    challenge: Optional[str] = Field(None, description="Challenge faced")
    solution: Optional[str] = Field(None, description="Solution provided")
    results: Optional[list[dict[str, str]]] = Field(
        None, description="Results achieved (metrics)"
    )
    customer_quote: Optional[str] = Field(None, description="Customer testimonial")


class BattlecardContent(BaseModel):
    """Complete battlecard content."""

    title: str = Field(..., description="Battlecard title")
    battlecard_type: str = Field(..., description="Type: competitive, objection")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # Competitive battlecard fields
    competitor_name: Optional[str] = Field(None, description="Competitor name")
    competitor_overview: Optional[str] = Field(None, description="Competitor overview")
    their_strengths: Optional[list[str]] = Field(
        None, description="Competitor strengths"
    )
    their_weaknesses: Optional[list[str]] = Field(
        None, description="Competitor weaknesses"
    )
    our_advantages: Optional[list[str]] = Field(
        None, description="Our advantages vs competitor"
    )
    head_to_head: Optional[list[dict[str, str]]] = Field(
        None, description="Feature comparison table"
    )
    competitive_positioning: Optional[str] = Field(
        None, description="How to position against them"
    )
    trap_questions: Optional[list[dict[str, str]]] = Field(
        None, description="Questions to ask that favor us"
    )
    landmines: Optional[list[dict[str, str]]] = Field(
        None, description="Topics to avoid or handle carefully"
    )
    win_themes: Optional[list[str]] = Field(
        None, description="Key themes when competing"
    )

    # Objection handling fields
    objections: Optional[list[dict[str, str]]] = Field(
        None, description="Objections with responses"
    )
    category: Optional[str] = Field(
        None, description="Objection category for objection battlecard"
    )
    quick_responses: Optional[list[dict[str, str]]] = Field(
        None, description="Quick one-liner responses"
    )
    detailed_responses: Optional[list[dict[str, str]]] = Field(
        None, description="Detailed responses with context"
    )
    prevention_tips: Optional[list[str]] = Field(
        None, description="How to prevent objections"
    )
    related_proof_points: Optional[list[str]] = Field(
        None, description="Evidence to support responses"
    )


# =============================================================================
# Request/Response Models
# =============================================================================


class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""

    content_type: ContentType = Field(..., description="Type of content to generate")
    goal: str = Field(..., description="Goal or purpose of the content")
    product_info: ProductInfo = Field(..., description="Product information")
    audience: AudienceInfo = Field(
        default_factory=AudienceInfo, description="Target audience info"
    )

    # Optional customization
    brand_voice: BrandVoice = Field(
        default=BrandVoice.PROFESSIONAL, description="Brand voice to use"
    )
    spiced_context: Optional[SPICEDContext] = Field(
        None, description="SPICED context for WbD alignment"
    )
    custom_instructions: Optional[str] = Field(
        None, description="Additional custom instructions"
    )

    # Type-specific inputs
    competitors: Optional[list[CompetitorInfo]] = Field(
        None, description="Competitor info for battlecards"
    )
    objections: Optional[list[ObjectionInfo]] = Field(
        None, description="Objections for objection battlecards"
    )
    case_study_data: Optional[dict[str, Any]] = Field(
        None, description="Case study data for case study one-pagers"
    )

    # Output preferences
    include_speaker_notes: bool = Field(
        default=True, description="Include speaker notes for decks"
    )
    include_visual_suggestions: bool = Field(
        default=True, description="Include visual suggestions"
    )
    max_slides: Optional[int] = Field(
        None, description="Max slides for decks (overrides default)"
    )


class ContentMetadata(BaseModel):
    """Metadata about generated content."""

    content_id: UUID = Field(default_factory=uuid4, description="Unique content ID")
    content_type: ContentType = Field(..., description="Type of content generated")
    status: ContentStatus = Field(
        default=ContentStatus.COMPLETED, description="Generation status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    generation_time_ms: Optional[int] = Field(
        None, description="Generation time in milliseconds"
    )
    model_used: Optional[str] = Field(None, description="Claude model used")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    version: str = Field(default="1.0", description="Content version")


class ContentGenerationResponse(BaseModel):
    """Response model for content generation."""

    metadata: ContentMetadata = Field(..., description="Content metadata")
    content: Union[DeckContent, ProposalContent, OnePagerContent, BattlecardContent] = Field(
        ..., description="Generated content"
    )
    raw_content: Optional[dict[str, Any]] = Field(
        None, description="Raw content JSON for debugging"
    )
    suggestions: Optional[list[str]] = Field(
        None, description="Suggestions for improvement"
    )
    wbd_alignment_score: Optional[float] = Field(
        None, description="WbD methodology alignment score (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "content_id": "123e4567-e89b-12d3-a456-426614174000",
                    "content_type": "deck_pitch",
                    "status": "completed",
                    "created_at": "2024-01-15T10:30:00Z",
                    "generation_time_ms": 3500,
                    "model_used": "claude-sonnet-4-20250514",
                    "tokens_used": 2500,
                    "version": "1.0",
                },
                "content": {
                    "title": "Transform Your Sales with AI",
                    "deck_type": "pitch",
                    "total_slides": 10,
                    "estimated_duration_minutes": 30,
                    "slides": [],
                    "key_messages": ["AI-powered efficiency", "Proven ROI"],
                    "call_to_action": "Schedule a demo today",
                },
            }
        }
=======
"""Content and Content Template models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum as SQLEnum

from .base import BaseDBModel, BaseModel, TimestampedSchema


class ContentType(str, Enum):
    """Type of generated content."""

    SALES_DECK = "sales_deck"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"
    CASE_STUDY = "case_study"
    EMAIL_SEQUENCE = "email_sequence"
    FOLLOW_UP = "follow_up"


class ContentStatus(str, Enum):
    """Status of content generation."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ContentTemplate(BaseDBModel):
    """Reusable content template."""

    __tablename__ = "content_templates"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    template_body = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # List of required variables
    styling = Column(JSON, default=dict)  # Brand styling options
    is_active = Column(Boolean, default=True)

    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


# Add Boolean import
from sqlalchemy import Boolean


class Content(BaseDBModel):
    """Generated content asset."""

    __tablename__ = "contents"

    title = Column(String(500), nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT)
    body = Column(Text)  # HTML/Markdown content
    rendered_html = Column(Text)  # Rendered HTML
    metadata = Column(JSON, default=dict)

    # File references
    pdf_path = Column(String(500))
    pptx_path = Column(String(500))

    # Source references
    transcript_id = Column(String(36), ForeignKey("transcripts.id"))
    template_id = Column(String(36), ForeignKey("content_templates.id"))
    prospect_id = Column(String(36), ForeignKey("prospects.id"))

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


# Pydantic Schemas
class ContentTemplateSchema(TimestampedSchema):
    """Content template response schema."""

    name: str
    description: Optional[str] = None
    content_type: ContentType
    template_body: str
    variables: List[str] = []
    styling: Dict[str, Any] = {}
    is_active: bool = True
    organization_id: str


class ContentSchema(TimestampedSchema):
    """Content response schema."""

    title: str
    content_type: ContentType
    status: ContentStatus
    body: Optional[str] = None
    rendered_html: Optional[str] = None
    metadata: Dict[str, Any] = {}
    pdf_path: Optional[str] = None
    pptx_path: Optional[str] = None
    transcript_id: Optional[str] = None
    template_id: Optional[str] = None
    prospect_id: Optional[str] = None
    user_id: str
    organization_id: str


class ContentCreate(BaseModel):
    """Content creation schema."""

    title: str
    content_type: ContentType
    body: Optional[str] = None
    template_id: Optional[str] = None
    transcript_id: Optional[str] = None
    prospect_id: Optional[str] = None
    variables: Dict[str, Any] = {}


class ContentExport(BaseModel):
    """Content export data format."""

    id: str
    title: str
    content_type: str
    status: str
    body: Optional[str] = None
    created_at: str
    files: List[str] = []  # List of file paths to include
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3
