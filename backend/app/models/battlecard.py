"""
Battlecard Models - Pydantic schemas for battlecard generation and management.

Supports four battlecard types:
- Competitive battlecards (vs specific competitors)
- Objection handling cards
- Feature comparison matrices
- Win/loss analysis cards
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class BattlecardType(str, Enum):
    """Types of battlecards supported by the system."""
    COMPETITIVE = "competitive"
    OBJECTION_HANDLING = "objection_handling"
    FEATURE_COMPARISON = "feature_comparison"
    WIN_LOSS_ANALYSIS = "win_loss_analysis"


class BattlecardStatus(str, Enum):
    """Status of a battlecard."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Competitor Models

class CompetitorStrength(BaseModel):
    """A competitive strength of a competitor."""
    area: str = Field(..., description="Area of strength (e.g., 'pricing', 'features')")
    description: str = Field(..., description="Description of the strength")
    impact: str = Field(..., description="Impact on sales conversations")


class CompetitorWeakness(BaseModel):
    """A competitive weakness of a competitor."""
    area: str = Field(..., description="Area of weakness")
    description: str = Field(..., description="Description of the weakness")
    talking_point: str = Field(..., description="How to position against this weakness")


class Competitor(BaseModel):
    """Competitor entity for competitive intelligence."""
    id: Optional[str] = None
    name: str = Field(..., description="Competitor company name")
    website: Optional[str] = Field(None, description="Competitor website URL")
    description: str = Field(..., description="Brief description of the competitor")
    target_market: str = Field(..., description="Primary target market")
    pricing_model: Optional[str] = Field(None, description="Pricing structure overview")
    key_products: list[str] = Field(default_factory=list, description="Key product offerings")
    strengths: list[CompetitorStrength] = Field(default_factory=list)
    weaknesses: list[CompetitorWeakness] = Field(default_factory=list)
    win_rate_against: Optional[float] = Field(None, ge=0, le=100, description="Our win rate against this competitor")
    common_objections: list[str] = Field(default_factory=list, description="Common objections when competing")
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None


class CompetitorCreate(BaseModel):
    """Request model for creating a competitor."""
    name: str
    website: Optional[str] = None
    description: str
    target_market: str
    pricing_model: Optional[str] = None
    key_products: list[str] = Field(default_factory=list)


class CompetitorUpdate(BaseModel):
    """Request model for updating a competitor."""
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    target_market: Optional[str] = None
    pricing_model: Optional[str] = None
    key_products: Optional[list[str]] = None
    strengths: Optional[list[CompetitorStrength]] = None
    weaknesses: Optional[list[CompetitorWeakness]] = None
    win_rate_against: Optional[float] = None
    common_objections: Optional[list[str]] = None


# Competitive Battlecard Models

class CompetitiveTalkingPoint(BaseModel):
    """A talking point for competitive conversations."""
    category: str = Field(..., description="Category (e.g., 'differentiation', 'value', 'proof')")
    point: str = Field(..., description="The talking point")
    supporting_evidence: Optional[str] = Field(None, description="Evidence or data to support")


class CompetitiveBattlecard(BaseModel):
    """Competitive battlecard content against a specific competitor."""
    competitor_name: str
    competitor_overview: str
    our_positioning: str = Field(..., description="How we position against this competitor")
    key_differentiators: list[str] = Field(..., description="Our key differentiators")
    competitor_strengths: list[CompetitorStrength]
    competitor_weaknesses: list[CompetitorWeakness]
    talking_points: list[CompetitiveTalkingPoint]
    landmines: list[str] = Field(..., description="Questions to plant doubt about competitor")
    proof_points: list[str] = Field(..., description="Customer stories, data points")
    when_we_win: list[str] = Field(..., description="Scenarios where we typically win")
    when_we_lose: list[str] = Field(..., description="Scenarios where we typically lose")


# Objection Handling Models

class ObjectionResponse(BaseModel):
    """A structured response to a sales objection."""
    acknowledge: str = Field(..., description="Acknowledge the concern")
    clarify: str = Field(..., description="Clarifying question to ask")
    respond: str = Field(..., description="Response to the objection")
    proof: Optional[str] = Field(None, description="Supporting proof point")
    redirect: str = Field(..., description="How to redirect the conversation")


class ObjectionCard(BaseModel):
    """An objection handling card."""
    objection: str = Field(..., description="The objection statement")
    category: str = Field(..., description="Category (e.g., 'price', 'timing', 'competition')")
    severity: str = Field(..., description="low, medium, high")
    root_cause: str = Field(..., description="Underlying concern behind objection")
    response: ObjectionResponse
    alternative_responses: list[str] = Field(default_factory=list)
    success_rate: Optional[float] = Field(None, description="Success rate when using this response")


class ObjectionHandlingBattlecard(BaseModel):
    """Collection of objection handling cards."""
    context: str = Field(..., description="Sales context (e.g., 'enterprise deals', 'SMB')")
    objections: list[ObjectionCard]
    general_tips: list[str] = Field(default_factory=list)


# Feature Comparison Models

class FeatureRating(str, Enum):
    """Rating for feature comparison."""
    SUPERIOR = "superior"
    COMPARABLE = "comparable"
    INFERIOR = "inferior"
    NOT_AVAILABLE = "not_available"


class FeatureComparison(BaseModel):
    """Comparison of a single feature across competitors."""
    feature_name: str
    feature_category: str
    our_capability: str = Field(..., description="Our capability description")
    our_rating: FeatureRating
    competitor_capabilities: dict[str, str] = Field(..., description="Competitor name -> capability")
    competitor_ratings: dict[str, FeatureRating] = Field(..., description="Competitor name -> rating")
    talking_point: Optional[str] = Field(None, description="How to discuss this feature")


class FeatureComparisonMatrix(BaseModel):
    """Feature comparison matrix battlecard."""
    title: str
    our_product: str
    competitors: list[str]
    categories: list[str] = Field(..., description="Feature categories included")
    comparisons: list[FeatureComparison]
    summary: str = Field(..., description="Overall comparison summary")
    key_advantages: list[str]
    areas_for_improvement: list[str]


# Win/Loss Analysis Models

class DealOutcome(str, Enum):
    """Outcome of a deal."""
    WON = "won"
    LOST = "lost"


class WinLossFactor(BaseModel):
    """A factor that contributed to win or loss."""
    factor: str = Field(..., description="The factor (e.g., 'pricing', 'features', 'relationship')")
    impact: str = Field(..., description="high, medium, low")
    description: str
    frequency: Optional[int] = Field(None, description="How often this factor appears")


class WinLossDeal(BaseModel):
    """Summary of a won or lost deal for analysis."""
    deal_id: Optional[str] = None
    deal_name: str
    outcome: DealOutcome
    competitor: Optional[str] = Field(None, description="Primary competitor if applicable")
    deal_size: Optional[float] = None
    sales_cycle_days: Optional[int] = None
    key_factors: list[str]
    lessons_learned: str
    date: Optional[datetime] = None


class WinLossAnalysisBattlecard(BaseModel):
    """Win/loss analysis battlecard."""
    analysis_period: str = Field(..., description="Time period analyzed")
    total_deals_analyzed: int
    win_rate: float = Field(..., ge=0, le=100)
    avg_deal_size_won: Optional[float] = None
    avg_deal_size_lost: Optional[float] = None
    avg_sales_cycle_won: Optional[int] = None
    avg_sales_cycle_lost: Optional[int] = None
    top_win_factors: list[WinLossFactor]
    top_loss_factors: list[WinLossFactor]
    competitor_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Win rate by competitor"
    )
    recommendations: list[str]
    notable_deals: list[WinLossDeal] = Field(default_factory=list)


# Main Battlecard Models

class BattlecardContent(BaseModel):
    """Union type for battlecard content."""
    competitive: Optional[CompetitiveBattlecard] = None
    objection_handling: Optional[ObjectionHandlingBattlecard] = None
    feature_comparison: Optional[FeatureComparisonMatrix] = None
    win_loss_analysis: Optional[WinLossAnalysisBattlecard] = None


class BattlecardVersion(BaseModel):
    """Version history entry for a battlecard."""
    version: int
    created_at: datetime
    created_by: str
    change_summary: str
    content_snapshot: dict  # JSON snapshot of content at this version


class Battlecard(BaseModel):
    """Main battlecard entity."""
    id: Optional[str] = None
    title: str = Field(..., description="Battlecard title")
    type: BattlecardType
    status: BattlecardStatus = BattlecardStatus.DRAFT
    description: Optional[str] = Field(None, description="Brief description")
    content: BattlecardContent
    tags: list[str] = Field(default_factory=list)

    # Ownership and sharing
    created_by: Optional[str] = None
    team_id: Optional[str] = None
    is_shared: bool = False
    shared_with_teams: list[str] = Field(default_factory=list)
    favorited_by: list[str] = Field(default_factory=list)

    # Versioning
    version: int = 1
    version_history: list[BattlecardVersion] = Field(default_factory=list)

    # Metadata
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    view_count: int = 0

    # Related entities
    competitor_ids: list[str] = Field(default_factory=list)
    product_ids: list[str] = Field(default_factory=list)


# Request/Response Models

class BattlecardGenerateRequest(BaseModel):
    """Request to generate a new battlecard."""
    type: BattlecardType
    title: str

    # For competitive battlecards
    competitor_id: Optional[str] = None
    competitor_name: Optional[str] = None

    # For objection handling
    objection_context: Optional[str] = None
    objection_categories: Optional[list[str]] = None

    # For feature comparison
    competitors_to_compare: Optional[list[str]] = None
    feature_categories: Optional[list[str]] = None

    # For win/loss analysis
    analysis_period_days: Optional[int] = Field(None, description="Days to analyze")

    # Common options
    product_context: Optional[str] = Field(None, description="Product/solution context")
    additional_context: Optional[str] = Field(None, description="Any additional context")
    auto_publish: bool = False


class BattlecardUpdateRequest(BaseModel):
    """Request to update an existing battlecard."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BattlecardStatus] = None
    content: Optional[BattlecardContent] = None
    tags: Optional[list[str]] = None
    is_shared: Optional[bool] = None
    shared_with_teams: Optional[list[str]] = None


class BattlecardResponse(BaseModel):
    """Response containing a battlecard."""
    success: bool
    battlecard: Optional[Battlecard] = None
    message: Optional[str] = None


class BattlecardListResponse(BaseModel):
    """Response containing a list of battlecards."""
    success: bool
    battlecards: list[Battlecard]
    total: int
    page: int = 1
    page_size: int = 20


class CompetitorListResponse(BaseModel):
    """Response containing a list of competitors."""
    success: bool
    competitors: list[Competitor]
    total: int


class BattlecardExportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class BattlecardExportRequest(BaseModel):
    """Request to export a battlecard."""
    battlecard_id: str
    format: BattlecardExportFormat
    include_version_history: bool = False


class BattlecardSearchRequest(BaseModel):
    """Request to search battlecards."""
    query: Optional[str] = None
    type: Optional[BattlecardType] = None
    status: Optional[BattlecardStatus] = None
    competitor_id: Optional[str] = None
    tags: Optional[list[str]] = None
    favorites_only: bool = False
    team_id: Optional[str] = None
    page: int = 1
    page_size: int = 20


class FavoriteRequest(BaseModel):
    """Request to favorite/unfavorite a battlecard."""
    battlecard_id: str
    user_id: str
    action: str = Field(..., pattern="^(add|remove)$")
