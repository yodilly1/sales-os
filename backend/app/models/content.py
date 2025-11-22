"""Content and ContentTemplate models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.prospect import Company, Prospect
    from app.models.user import User


class ContentType(str, Enum):
    """Type of generated content."""

    SALES_DECK = "sales_deck"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"
    CASE_STUDY = "case_study"
    EMAIL_SEQUENCE = "email_sequence"
    FOLLOW_UP_EMAIL = "follow_up_email"
    EXECUTIVE_SUMMARY = "executive_summary"
    ROI_CALCULATOR = "roi_calculator"
    OTHER = "other"


class ContentStatus(str, Enum):
    """Status of content generation."""

    DRAFT = "draft"
    GENERATING = "generating"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"


class ContentTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """Template for content generation."""

    __tablename__ = "content_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Template structure (JSON)
    template_structure: Mapped[str] = mapped_column(Text, nullable=False)

    # Styling and branding
    brand_guidelines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    color_scheme: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    font_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Template settings
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Foreign Keys
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )

    # Relationships
    content: Mapped[List["Content"]] = relationship("Content", back_populates="template")

    def __repr__(self) -> str:
        return f"<ContentTemplate {self.name}>"


class Content(Base, TimestampMixin, SoftDeleteMixin):
    """Generated content model."""

    __tablename__ = "content"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ContentStatus.DRAFT.value, nullable=False)

    # Input data for generation
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    audience_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    additional_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated content (JSON structure)
    content_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rendered output
    rendered_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rendered_pdf_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    rendered_pptx_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("content.id"), nullable=True
    )

    # Metadata
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Foreign Keys
    created_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("content_templates.id"), nullable=True
    )
    prospect_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("prospects.id"), nullable=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True
    )

    # Relationships
    created_by: Mapped["User"] = relationship("User", back_populates="content")
    template: Mapped[Optional["ContentTemplate"]] = relationship(
        "ContentTemplate", back_populates="content"
    )
    prospect: Mapped[Optional["Prospect"]] = relationship("Prospect", back_populates="content")
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="content")
    revisions: Mapped[List["Content"]] = relationship(
        "Content", back_populates="parent", remote_side="Content.id"
    )
    parent: Mapped[Optional["Content"]] = relationship(
        "Content", back_populates="revisions", remote_side=[parent_id]
    )

    def __repr__(self) -> str:
        return f"<Content {self.title}>"
