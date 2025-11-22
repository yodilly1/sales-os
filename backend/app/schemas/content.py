"""Content and ContentTemplate Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.models.content import ContentStatus, ContentType
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


# ==================== ContentTemplate Schemas ====================


class ContentTemplateBase(BaseSchema):
    """Base content template schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: ContentType


class ContentTemplateCreate(ContentTemplateBase):
    """Schema for creating a content template."""

    template_structure: Dict[str, Any]
    brand_guidelines: Optional[Dict[str, Any]] = None
    color_scheme: Optional[Dict[str, Any]] = None
    font_family: Optional[str] = Field(None, max_length=100)
    is_default: bool = False
    is_public: bool = False
    organization_id: Optional[str] = None


class ContentTemplateUpdate(BaseSchema):
    """Schema for updating a content template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_structure: Optional[Dict[str, Any]] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    color_scheme: Optional[Dict[str, Any]] = None
    font_family: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None


class ContentTemplateResponse(ContentTemplateBase, IDSchema, TimestampSchema):
    """Schema for content template response."""

    template_structure: Dict[str, Any]
    brand_guidelines: Optional[Dict[str, Any]] = None
    color_scheme: Optional[Dict[str, Any]] = None
    font_family: Optional[str] = None
    is_default: bool
    is_public: bool
    version: int
    usage_count: int
    organization_id: Optional[str] = None

    @field_validator("template_structure", "brand_guidelines", "color_scheme", mode="before")
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


# ==================== Content Schemas ====================


class AudienceInfo(BaseSchema):
    """Audience information for content generation."""

    industry: Optional[str] = None
    company_size: Optional[str] = None
    role: Optional[str] = None
    pain_points: Optional[List[str]] = None
    goals: Optional[List[str]] = None


class ProductInfo(BaseSchema):
    """Product information for content generation."""

    name: str
    description: Optional[str] = None
    features: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    differentiators: Optional[List[str]] = None
    pricing: Optional[str] = None


class ContentBase(BaseSchema):
    """Base content schema."""

    title: str = Field(..., min_length=1, max_length=500)
    content_type: ContentType


class ContentCreate(ContentBase):
    """Schema for creating content."""

    goal: Optional[str] = None
    product_info: Optional[ProductInfo] = None
    audience_info: Optional[AudienceInfo] = None
    additional_context: Optional[str] = None
    template_id: Optional[str] = None
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None


class ContentUpdate(BaseSchema):
    """Schema for updating content."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[ContentStatus] = None
    goal: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ContentResponse(ContentBase, IDSchema, TimestampSchema):
    """Schema for content response."""

    status: ContentStatus
    goal: Optional[str] = None
    product_info: Optional[ProductInfo] = None
    audience_info: Optional[AudienceInfo] = None
    additional_context: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    rendered_html: Optional[str] = None
    rendered_pdf_url: Optional[str] = None
    rendered_pptx_url: Optional[str] = None
    version: int
    parent_id: Optional[str] = None
    tags: Optional[List[str]] = None
    generated_at: Optional[datetime] = None
    model_version: Optional[str] = None
    created_by_id: str
    template_id: Optional[str] = None
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None

    @field_validator("product_info", "audience_info", "content_data", "tags", mode="before")
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """Parse JSON string fields."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class ContentGenerateRequest(BaseSchema):
    """Request to generate content."""

    content_type: ContentType
    title: str = Field(..., min_length=1, max_length=500)
    goal: str
    product_info: ProductInfo
    audience_info: Optional[AudienceInfo] = None
    template_id: Optional[str] = None
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    additional_context: Optional[str] = None
    style_preferences: Optional[Dict[str, Any]] = None


class ContentGenerateResponse(BaseSchema):
    """Response from content generation."""

    content: ContentResponse
    processing_time_ms: int
    model_used: str


class ContentRenderRequest(BaseSchema):
    """Request to render content."""

    content_id: str
    format: str = Field(..., pattern="^(pdf|pptx|html)$")
    include_branding: bool = True


class ContentRenderResponse(BaseSchema):
    """Response from content rendering."""

    content_id: str
    format: str
    url: str
    expires_at: datetime
