"""
Pydantic schemas for search service requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SortOrder(str, Enum):
    """Sort order for search results."""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"


class EntityTypeFilter(str, Enum):
    """Entity types available for filtering."""
    TRANSCRIPT = "transcript"
    CALL = "call"
    CONTENT = "content"
    PROSPECT = "prospect"
    COMPANY = "company"
    COACHING_REPORT = "coaching_report"
    ALL = "all"


class DateRangePreset(str, Enum):
    """Preset date ranges for quick filtering."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class SearchFilters(BaseModel):
    """Filters for narrowing search results."""

    # Entity type filtering
    entity_types: Optional[List[EntityTypeFilter]] = Field(
        default=None,
        description="Filter by entity types (transcript, content, etc.)"
    )

    # Date filtering
    date_preset: Optional[DateRangePreset] = Field(
        default=None,
        description="Preset date range filter"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Custom start date for filtering"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Custom end date for filtering"
    )

    # Status filtering
    status: Optional[List[str]] = Field(
        default=None,
        description="Filter by status values"
    )

    # Tag filtering
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (AND logic)"
    )
    tags_any: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (OR logic)"
    )

    # Content subtype filtering
    content_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by content subtypes (deck, proposal, etc.)"
    )

    # Related entity filtering
    prospect_id: Optional[int] = Field(
        default=None,
        description="Filter by related prospect"
    )
    company_id: Optional[int] = Field(
        default=None,
        description="Filter by related company"
    )
    user_id: Optional[int] = Field(
        default=None,
        description="Filter by owner/creator"
    )

    class Config:
        use_enum_values = True


class SearchRequest(BaseModel):
    """Request schema for search queries."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters to apply"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of results per page"
    )
    sort_by: SortOrder = Field(
        default=SortOrder.RELEVANCE,
        description="Sort order for results"
    )
    include_facets: bool = Field(
        default=True,
        description="Whether to include facet counts in response"
    )
    highlight: bool = Field(
        default=True,
        description="Whether to highlight matching terms"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Strip and validate query string."""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Query must not be empty")
        return v


class SearchResult(BaseModel):
    """Individual search result item."""

    id: int = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Type of entity")
    title: str = Field(..., description="Result title")
    summary: Optional[str] = Field(None, description="Result summary/snippet")
    highlighted_title: Optional[str] = Field(None, description="Title with highlights")
    highlighted_summary: Optional[str] = Field(None, description="Summary with highlights")
    status: Optional[str] = Field(None, description="Entity status")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    date: Optional[datetime] = Field(None, description="Entity date")
    relevance_score: float = Field(default=0.0, description="Search relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        from_attributes = True


class FacetValue(BaseModel):
    """A single facet value with its count."""

    value: str = Field(..., description="Facet value")
    count: int = Field(..., description="Number of results with this value")
    selected: bool = Field(default=False, description="Whether this facet is selected")


class FacetResult(BaseModel):
    """Faceted search result for a single facet category."""

    name: str = Field(..., description="Facet name (e.g., 'entity_type', 'status')")
    display_name: str = Field(..., description="Human-readable facet name")
    values: List[FacetValue] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response schema for search queries."""

    query: str = Field(..., description="Original query string")
    total_count: int = Field(..., description="Total number of matching results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    results: List[SearchResult] = Field(default_factory=list)
    facets: Optional[List[FacetResult]] = Field(None, description="Faceted filter counts")
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")
    filters_applied: Optional[SearchFilters] = Field(None, description="Filters that were applied")


class AutocompleteRequest(BaseModel):
    """Request for autocomplete suggestions."""

    prefix: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Prefix to match"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of suggestions"
    )
    entity_types: Optional[List[EntityTypeFilter]] = Field(
        default=None,
        description="Filter suggestions by entity type"
    )
    include_recent: bool = Field(
        default=True,
        description="Include recent searches in suggestions"
    )


class AutocompleteSuggestion(BaseModel):
    """A single autocomplete suggestion."""

    text: str = Field(..., description="Suggested text")
    type: str = Field(..., description="Suggestion type (recent, popular, entity)")
    entity_type: Optional[str] = Field(None, description="Entity type if applicable")
    entity_id: Optional[int] = Field(None, description="Entity ID if direct match")
    frequency: Optional[int] = Field(None, description="Usage frequency")


class AutocompleteResponse(BaseModel):
    """Response with autocomplete suggestions."""

    prefix: str = Field(..., description="Original prefix")
    suggestions: List[AutocompleteSuggestion] = Field(default_factory=list)


class SearchHistoryItem(BaseModel):
    """A single search history entry."""

    id: int = Field(..., description="History entry ID")
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    result_count: int = Field(default=0, description="Number of results")
    entity_types: Optional[List[str]] = Field(None, description="Entity types searched")
    created_at: datetime = Field(..., description="When the search was performed")

    class Config:
        from_attributes = True


class SavedSearchCreate(BaseModel):
    """Schema for creating a saved search."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name for the saved search"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query to save"
    )
    filters: Optional[SearchFilters] = Field(
        None,
        description="Filters to save with the search"
    )
    entity_types: Optional[List[EntityTypeFilter]] = Field(
        None,
        description="Entity types to search"
    )
    is_default: bool = Field(
        default=False,
        description="Set as default quick search"
    )


class SavedSearchUpdate(BaseModel):
    """Schema for updating a saved search."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    entity_types: Optional[List[EntityTypeFilter]] = None
    is_default: Optional[bool] = None


class SavedSearchResponse(BaseModel):
    """Response schema for saved search."""

    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    query: str
    filters: Optional[Dict[str, Any]] = None
    entity_types: Optional[List[str]] = None
    is_default: bool = False
    use_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
