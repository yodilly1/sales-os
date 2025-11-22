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
