"""
Search API endpoints.

Provides REST API endpoints for:
- Full-text search across all entities
- Autocomplete suggestions
- Search history management
- Saved search queries
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.search import (
    SearchService,
    SearchRequest,
    SearchResponse,
    SearchFilters,
    AutocompleteRequest,
    AutocompleteResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
)
from app.services.search.schemas import (
    SearchHistoryItem,
    SavedSearchResponse,
    SortOrder,
    EntityTypeFilter,
    DateRangePreset,
)

router = APIRouter(prefix="/search", tags=["search"])


# Placeholder for auth dependency - would be replaced with actual auth
def get_current_user_id() -> int:
    """Get the current user ID from authentication context."""
    # This would be replaced with actual auth logic
    return 1


def get_current_organization_id() -> Optional[int]:
    """Get the current organization ID from authentication context."""
    # This would be replaced with actual auth logic
    return 1


# =============================================================================
# Search Endpoints
# =============================================================================


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    organization_id: Optional[int] = Depends(get_current_organization_id),
) -> SearchResponse:
    """
    Execute a full-text search across all entities.

    Supports:
    - Full-text search with relevance ranking
    - Faceted filtering by type, status, date, tags
    - Pagination and sorting
    - Highlighted result snippets

    **Performance Target:** <500ms response time
    """
    service = SearchService(db)
    return service.search(request, user_id, organization_id)


@router.get("", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    entity_types: Optional[List[EntityTypeFilter]] = Query(
        None, description="Filter by entity types"
    ),
    status: Optional[List[str]] = Query(None, description="Filter by status"),
    date_preset: Optional[DateRangePreset] = Query(None, description="Date range preset"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (AND)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: SortOrder = Query(SortOrder.RELEVANCE, description="Sort order"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    organization_id: Optional[int] = Depends(get_current_organization_id),
) -> SearchResponse:
    """
    Execute a search using GET parameters.

    Convenience endpoint for simple searches without a request body.
    """
    filters = SearchFilters(
        entity_types=entity_types,
        status=status,
        date_preset=date_preset,
        tags=tags,
    )

    request = SearchRequest(
        query=q,
        filters=filters if any([entity_types, status, date_preset, tags]) else None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )

    service = SearchService(db)
    return service.search(request, user_id, organization_id)


@router.get("/quick", response_model=SearchResponse)
async def quick_search(
    q: str = Query(..., min_length=1, max_length=100, description="Quick search query"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    organization_id: Optional[int] = Depends(get_current_organization_id),
) -> SearchResponse:
    """
    Execute a quick search for instant results.

    Returns a small number of results quickly for use in
    search-as-you-type interfaces.
    """
    request = SearchRequest(
        query=q,
        page=1,
        page_size=limit,
        include_facets=False,
        highlight=True,
    )

    service = SearchService(db)
    return service.search(request, user_id, organization_id)


# =============================================================================
# Autocomplete Endpoints
# =============================================================================


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    prefix: str = Query(..., min_length=1, max_length=100, description="Search prefix"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
    entity_types: Optional[List[EntityTypeFilter]] = Query(
        None, description="Filter by entity types"
    ),
    include_recent: bool = Query(True, description="Include recent searches"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    organization_id: Optional[int] = Depends(get_current_organization_id),
) -> AutocompleteResponse:
    """
    Get autocomplete suggestions for a search prefix.

    Returns suggestions from:
    - User's recent searches
    - Popular search terms
    - Entity title matches
    """
    request = AutocompleteRequest(
        prefix=prefix,
        limit=limit,
        entity_types=entity_types,
        include_recent=include_recent,
    )

    service = SearchService(db)
    return service.autocomplete(request, user_id, organization_id)


# =============================================================================
# Search History Endpoints
# =============================================================================


@router.get("/history", response_model=dict)
async def get_search_history(
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """
    Get the user's search history.

    Returns recent searches with filters applied and result counts.
    """
    service = SearchService(db)
    items, total = service.get_search_history(user_id, limit, offset)

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/history", status_code=status.HTTP_200_OK)
async def clear_search_history(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """
    Clear all search history for the current user.
    """
    service = SearchService(db)
    deleted = service.clear_search_history(user_id)

    return {"deleted": deleted, "message": "Search history cleared"}


@router.delete("/history/{history_id}", status_code=status.HTTP_200_OK)
async def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """
    Delete a specific search history item.
    """
    service = SearchService(db)
    deleted = service.delete_search_history_item(user_id, history_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found"
        )

    return {"deleted": True, "message": "History item deleted"}


# =============================================================================
# Saved Search Endpoints
# =============================================================================


@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    data: SavedSearchCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SavedSearchResponse:
    """
    Create a new saved search.

    Saves the query and filters for quick access later.
    """
    service = SearchService(db)
    return service.create_saved_search(user_id, data)


@router.get("/saved", response_model=dict)
async def get_saved_searches(
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """
    Get all saved searches for the current user.

    Returns saved searches ordered by usage frequency.
    """
    service = SearchService(db)
    items, total = service.get_saved_searches(user_id, limit, offset)

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/saved/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SavedSearchResponse:
    """
    Get a specific saved search by ID.
    """
    service = SearchService(db)
    result = service.get_saved_search(user_id, search_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return result


@router.put("/saved/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: int,
    data: SavedSearchUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SavedSearchResponse:
    """
    Update a saved search.
    """
    service = SearchService(db)
    result = service.update_saved_search(user_id, search_id, data)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return result


@router.delete("/saved/{search_id}", status_code=status.HTTP_200_OK)
async def delete_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """
    Delete a saved search.
    """
    service = SearchService(db)
    deleted = service.delete_saved_search(user_id, search_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return {"deleted": True, "message": "Saved search deleted"}


@router.post("/saved/{search_id}/execute", response_model=SearchResponse)
async def execute_saved_search(
    search_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    organization_id: Optional[int] = Depends(get_current_organization_id),
) -> SearchResponse:
    """
    Execute a saved search.

    Runs the saved query with its filters and returns results.
    Also increments the usage count for the saved search.
    """
    service = SearchService(db)
    result = service.execute_saved_search(
        user_id,
        search_id,
        organization_id,
        page,
        page_size
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return result
