"""
Search service for Sales OS.

Provides full-text search, faceted filtering, autocomplete,
search history, and saved search functionality.
"""

from .service import SearchService
from .schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchFilters,
    FacetResult,
    AutocompleteRequest,
    AutocompleteResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
)
from .indexer import SearchIndexer

__all__ = [
    "SearchService",
    "SearchIndexer",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "SearchFilters",
    "FacetResult",
    "AutocompleteRequest",
    "AutocompleteResponse",
    "SavedSearchCreate",
    "SavedSearchUpdate",
]
