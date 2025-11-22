"""Pydantic models for rendering service."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# Enums
class ContentType(str, Enum):
    """Types of content that can be rendered."""
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    PITCH_DECK = "pitch_deck"
    QBR_DECK = "qbr_deck"
    EXECUTIVE_SUMMARY = "executive_summary"
    CASE_STUDY = "case_study"


class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    PPTX = "pptx"
    HTML = "html"


class SlideLayout(str, Enum):
    """Predefined slide layouts."""
    TITLE = "title"
    TITLE_CONTENT = "title_content"
    TWO_COLUMN = "two_column"
    IMAGE_LEFT = "image_left"
    IMAGE_RIGHT = "image_right"
    FULL_IMAGE = "full_image"
    QUOTE = "quote"
    METRICS = "metrics"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    TEAM = "team"
    PRICING = "pricing"
    CTA = "cta"


class TextAlign(str, Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


# Brand Configuration
class BrandConfig(BaseModel):
    """Brand styling configuration."""
    primary_color: str = Field(default="#1E40AF", description="Primary brand color (hex)")
    secondary_color: str = Field(default="#3B82F6", description="Secondary brand color (hex)")
    accent_color: str = Field(default="#10B981", description="Accent color (hex)")
    text_color: str = Field(default="#1F2937", description="Main text color (hex)")
    light_color: str = Field(default="#F9FAFB", description="Light background color (hex)")
    heading_font: str = Field(default="Inter", description="Font for headings")
    body_font: str = Field(default="Inter", description="Font for body text")
    logo_url: Optional[str] = Field(default=None, description="URL or path to logo")
    logo_position: str = Field(default="top-left", description="Logo position on slides")


# Content Elements
class TextBlock(BaseModel):
    """A block of text content."""
    content: str = Field(..., description="The text content (supports markdown)")
    style: str = Field(default="body", description="Style: heading1, heading2, heading3, body, caption")
    align: TextAlign = Field(default=TextAlign.LEFT)
    color: Optional[str] = Field(default=None, description="Override text color")


class ImageBlock(BaseModel):
    """An image element."""
    url: str = Field(..., description="Image URL or base64 data")
    alt_text: str = Field(default="", description="Alt text for accessibility")
    width: Optional[int] = Field(default=None, description="Width in pixels")
    height: Optional[int] = Field(default=None, description="Height in pixels")
    fit: str = Field(default="contain", description="Fit mode: contain, cover, fill")


class MetricItem(BaseModel):
    """A single metric for display."""
    value: str = Field(..., description="The metric value (e.g., '150%', '$2M')")
    label: str = Field(..., description="Label for the metric")
    description: Optional[str] = Field(default=None, description="Additional context")
    trend: Optional[str] = Field(default=None, description="Trend indicator: up, down, neutral")


class TimelineItem(BaseModel):
    """An item in a timeline."""
    date: str = Field(..., description="Date or period label")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(default=None)


class TeamMember(BaseModel):
    """Team member information."""
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="Job title/role")
    image_url: Optional[str] = Field(default=None, description="Profile photo URL")
    bio: Optional[str] = Field(default=None, description="Short bio")
    linkedin_url: Optional[str] = Field(default=None)


class PricingTier(BaseModel):
    """A pricing tier option."""
    name: str = Field(..., description="Tier name")
    price: str = Field(..., description="Price display (e.g., '$99/mo')")
    description: Optional[str] = Field(default=None)
    features: list[str] = Field(default_factory=list, description="List of features")
    highlighted: bool = Field(default=False, description="Highlight this tier")
    cta_text: str = Field(default="Get Started")


class ComparisonColumn(BaseModel):
    """A column in a comparison table."""
    header: str = Field(..., description="Column header")
    values: list[str] = Field(..., description="Values for each row")
    highlighted: bool = Field(default=False)


class BulletList(BaseModel):
    """A list of bullet points."""
    items: list[str] = Field(..., description="List items")
    style: str = Field(default="bullet", description="Style: bullet, numbered, check")


# Slide Content
class SlideContent(BaseModel):
    """Content for a single slide."""
    layout: SlideLayout = Field(default=SlideLayout.TITLE_CONTENT)
    title: Optional[str] = Field(default=None, description="Slide title")
    subtitle: Optional[str] = Field(default=None, description="Slide subtitle")
    body: Optional[list[TextBlock]] = Field(default=None, description="Body text blocks")
    bullets: Optional[BulletList] = Field(default=None, description="Bullet points")
    image: Optional[ImageBlock] = Field(default=None, description="Main image")
    images: Optional[list[ImageBlock]] = Field(default=None, description="Multiple images")
    metrics: Optional[list[MetricItem]] = Field(default=None, description="Metrics display")
    timeline: Optional[list[TimelineItem]] = Field(default=None, description="Timeline items")
    team: Optional[list[TeamMember]] = Field(default=None, description="Team members")
    pricing: Optional[list[PricingTier]] = Field(default=None, description="Pricing tiers")
    comparison: Optional[list[ComparisonColumn]] = Field(default=None)
    comparison_rows: Optional[list[str]] = Field(default=None, description="Row labels for comparison")
    quote: Optional[str] = Field(default=None, description="Quote text")
    quote_author: Optional[str] = Field(default=None, description="Quote attribution")
    cta_text: Optional[str] = Field(default=None, description="Call to action text")
    cta_url: Optional[str] = Field(default=None, description="Call to action URL")
    speaker_notes: Optional[str] = Field(default=None, description="Speaker notes (not displayed)")
    background_color: Optional[str] = Field(default=None, description="Override slide background")
    background_image: Optional[str] = Field(default=None, description="Background image URL")


class Slide(BaseModel):
    """A complete slide definition."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: SlideContent
    transition: str = Field(default="fade", description="Transition effect")
    duration: Optional[int] = Field(default=None, description="Auto-advance duration in seconds")


# Document Sections (for PDFs)
class DocumentSection(BaseModel):
    """A section in a PDF document."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str = Field(..., description="Section title")
    content: list[TextBlock | ImageBlock | BulletList | MetricItem] = Field(
        default_factory=list, description="Section content"
    )
    page_break_before: bool = Field(default=False, description="Start on new page")
    page_break_after: bool = Field(default=False, description="Page break after section")


# SPICED Content Integration
class SPICEDData(BaseModel):
    """SPICED methodology data extracted from transcripts."""
    situation: Optional[str] = Field(default=None, description="Current situation")
    pain: Optional[str] = Field(default=None, description="Pain points identified")
    impact: Optional[str] = Field(default=None, description="Business impact")
    critical_event: Optional[str] = Field(default=None, description="Critical event/timeline")
    decision: Optional[str] = Field(default=None, description="Decision criteria")
    extras: Optional[dict[str, Any]] = Field(default=None, description="Additional context")


class ProspectInfo(BaseModel):
    """Information about the prospect/company."""
    company_name: str = Field(..., description="Company name")
    contact_name: Optional[str] = Field(default=None)
    contact_title: Optional[str] = Field(default=None)
    industry: Optional[str] = Field(default=None)
    company_size: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)


# Render Requests
class RenderRequest(BaseModel):
    """Base render request model."""
    id: UUID = Field(default_factory=uuid4)
    content_type: ContentType
    format: ExportFormat = Field(default=ExportFormat.PDF)
    brand: BrandConfig = Field(default_factory=BrandConfig)
    title: str = Field(..., description="Document/deck title")
    subtitle: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    prospect: Optional[ProspectInfo] = Field(default=None)
    spiced: Optional[SPICEDData] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PDFRenderRequest(RenderRequest):
    """Request to render a PDF document."""
    sections: list[DocumentSection] = Field(..., description="Document sections")
    header_text: Optional[str] = Field(default=None, description="Header text on each page")
    footer_text: Optional[str] = Field(default=None, description="Footer text on each page")
    show_page_numbers: bool = Field(default=True)
    show_toc: bool = Field(default=False, description="Include table of contents")


class DeckRenderRequest(RenderRequest):
    """Request to render a slide deck."""
    slides: list[Slide] = Field(..., description="Slides in the deck")
    show_slide_numbers: bool = Field(default=True)
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 16:9, 4:3")


class WebDeckConfig(BaseModel):
    """Configuration for web-based deck viewer."""
    enable_navigation: bool = Field(default=True)
    enable_fullscreen: bool = Field(default=True)
    enable_presenter_mode: bool = Field(default=True)
    enable_download: bool = Field(default=True)
    auto_advance: bool = Field(default=False)
    auto_advance_interval: int = Field(default=10, description="Seconds between slides")
    theme: str = Field(default="light", description="Theme: light, dark")
    share_expires_at: Optional[datetime] = Field(default=None)


class WebDeckRenderRequest(DeckRenderRequest):
    """Request to render a web-based deck viewer."""
    config: WebDeckConfig = Field(default_factory=WebDeckConfig)
    share_id: Optional[str] = Field(default=None, description="Unique share identifier")


# Render Responses
class RenderStatus(str, Enum):
    """Status of a render job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderResult(BaseModel):
    """Result of a render operation."""
    id: UUID
    status: RenderStatus
    content_type: ContentType
    format: ExportFormat
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    file_path: Optional[str] = Field(default=None, description="Path to rendered file")
    file_url: Optional[str] = Field(default=None, description="Download URL")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    page_count: Optional[int] = Field(default=None, description="Number of pages/slides")
    error_message: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebDeckResult(RenderResult):
    """Result of web deck rendering."""
    share_url: Optional[str] = Field(default=None, description="Shareable URL")
    embed_code: Optional[str] = Field(default=None, description="HTML embed code")
    expires_at: Optional[datetime] = Field(default=None)


# Template Models
class TemplateInfo(BaseModel):
    """Information about a content template."""
    id: str
    name: str
    description: str
    content_type: ContentType
    preview_url: Optional[str] = Field(default=None)
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""
    templates: list[TemplateInfo]
    total: int
