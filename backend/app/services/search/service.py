"""
Main search service implementation.

Provides full-text search across all entities with faceted filtering,
autocomplete suggestions, search history, and saved searches.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, and_, func, text, cast, String
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB

from app.models.search import (
    EntityType,
    SearchStatus,
    SearchHistory,
    SavedSearch,
    SearchIndex,
    SearchSuggestion,
)
from app.core.config import settings

from .schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchFilters,
    FacetResult,
    FacetValue,
    AutocompleteRequest,
    AutocompleteResponse,
    AutocompleteSuggestion,
    SearchHistoryItem,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    SortOrder,
    DateRangePreset,
    EntityTypeFilter,
)


class SearchService:
    """
    Service for performing searches across all entities.

    Supports:
    - Full-text search with relevance ranking
    - Faceted filtering
    - Autocomplete suggestions
    - Search history tracking
    - Saved search queries
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Full-Text Search
    # =========================================================================

    def search(
        self,
        request: SearchRequest,
        user_id: int,
        organization_id: Optional[int] = None,
    ) -> SearchResponse:
        """
        Execute a full-text search across all indexed entities.

        Args:
            request: Search request with query and filters
            user_id: ID of the user performing the search
            organization_id: Optional organization scope

        Returns:
            SearchResponse with results, facets, and pagination
        """
        start_time = time.time()

        # Build the base query
        query = self.db.query(SearchIndex)

        # Apply organization scope if provided
        if organization_id:
            query = query.filter(SearchIndex.organization_id == organization_id)

        # Apply full-text search
        query = self._apply_text_search(query, request.query)

        # Apply filters
        if request.filters:
            query = self._apply_filters(query, request.filters)

        # Get total count before pagination
        total_count = query.count()

        # Get facets if requested
        facets = None
        if request.include_facets:
            facets = self._get_facets(query, request.filters)

        # Apply sorting
        query = self._apply_sorting(query, request.sort_by)

        # Apply pagination
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)

        # Execute query
        results = query.all()

        # Transform results
        search_results = [
            self._transform_result(result, request.query, request.highlight)
            for result in results
        ]

        # Record search in history
        self._record_search_history(
            user_id=user_id,
            query=request.query,
            filters=request.filters,
            result_count=total_count,
            entity_types=request.filters.entity_types if request.filters else None,
        )

        # Update suggestion frequency
        self._update_suggestions(request.query, organization_id)

        # Calculate execution time
        search_time_ms = int((time.time() - start_time) * 1000)

        # Calculate total pages
        total_pages = (total_count + request.page_size - 1) // request.page_size

        return SearchResponse(
            query=request.query,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            results=search_results,
            facets=facets,
            search_time_ms=search_time_ms,
            filters_applied=request.filters,
        )

    def _apply_text_search(self, query, search_query: str):
        """Apply full-text search to the query."""
        # Normalize the search query
        search_terms = self._tokenize_query(search_query)

        if not search_terms:
            return query

        # Build search conditions
        conditions = []
        for term in search_terms:
            pattern = f"%{term}%"
            term_condition = or_(
                SearchIndex.title.ilike(pattern),
                SearchIndex.content.ilike(pattern),
                SearchIndex.summary.ilike(pattern),
                # Search in tags (JSON array)
                cast(SearchIndex.tags, String).ilike(pattern),
            )
            conditions.append(term_condition)

        # All terms must match (AND logic)
        query = query.filter(and_(*conditions))

        return query

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize and normalize search query."""
        # Handle quoted phrases
        phrases = re.findall(r'"([^"]+)"', query)

        # Remove quoted phrases from query
        remaining = re.sub(r'"[^"]+"', '', query)

        # Split remaining into words
        words = remaining.lower().split()

        # Filter out very short words and common stop words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = [w for w in words if len(w) >= settings.SEARCH_MIN_QUERY_LENGTH and w not in stop_words]

        return phrases + words

    def _apply_filters(self, query, filters: SearchFilters):
        """Apply all filters to the query."""
        # Entity type filter
        if filters.entity_types:
            valid_types = [
                EntityType(et.value) for et in filters.entity_types
                if et != EntityTypeFilter.ALL
            ]
            if valid_types:
                query = query.filter(SearchIndex.entity_type.in_(valid_types))

        # Date filters
        query = self._apply_date_filter(query, filters)

        # Status filter
        if filters.status:
            status_values = [SearchStatus(s) for s in filters.status if s in SearchStatus.__members__]
            if status_values:
                query = query.filter(SearchIndex.status.in_(status_values))

        # Tag filters (AND logic - must have all tags)
        if filters.tags:
            for tag in filters.tags:
                query = query.filter(
                    func.json_contains(SearchIndex.tags, f'"{tag}"')
                )

        # Tag filters (OR logic - must have any tag)
        if filters.tags_any:
            tag_conditions = [
                func.json_contains(SearchIndex.tags, f'"{tag}"')
                for tag in filters.tags_any
            ]
            query = query.filter(or_(*tag_conditions))

        # Content subtype filter
        if filters.content_types:
            query = query.filter(SearchIndex.content_subtype.in_(filters.content_types))

        # Related entity filters
        if filters.prospect_id:
            query = query.filter(SearchIndex.prospect_id == filters.prospect_id)
        if filters.company_id:
            query = query.filter(SearchIndex.company_id == filters.company_id)
        if filters.user_id:
            query = query.filter(SearchIndex.user_id == filters.user_id)

        return query

    def _apply_date_filter(self, query, filters: SearchFilters):
        """Apply date range filter based on preset or custom dates."""
        now = datetime.utcnow()
        date_from = None
        date_to = None

        if filters.date_preset:
            if filters.date_preset == DateRangePreset.TODAY:
                date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = now
            elif filters.date_preset == DateRangePreset.YESTERDAY:
                yesterday = now - timedelta(days=1)
                date_from = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = yesterday.replace(hour=23, minute=59, second=59)
            elif filters.date_preset == DateRangePreset.LAST_7_DAYS:
                date_from = now - timedelta(days=7)
            elif filters.date_preset == DateRangePreset.LAST_30_DAYS:
                date_from = now - timedelta(days=30)
            elif filters.date_preset == DateRangePreset.LAST_90_DAYS:
                date_from = now - timedelta(days=90)
            elif filters.date_preset == DateRangePreset.THIS_MONTH:
                date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif filters.date_preset == DateRangePreset.LAST_MONTH:
                first_of_this_month = now.replace(day=1)
                last_month = first_of_this_month - timedelta(days=1)
                date_from = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                date_to = last_month.replace(hour=23, minute=59, second=59)
            elif filters.date_preset == DateRangePreset.THIS_QUARTER:
                quarter = (now.month - 1) // 3
                date_from = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif filters.date_preset == DateRangePreset.THIS_YEAR:
                date_from = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            elif filters.date_preset == DateRangePreset.CUSTOM:
                date_from = filters.date_from
                date_to = filters.date_to

        # Apply custom dates if preset is CUSTOM or not set
        if filters.date_from and not date_from:
            date_from = filters.date_from
        if filters.date_to and not date_to:
            date_to = filters.date_to

        # Apply to query
        if date_from:
            query = query.filter(SearchIndex.entity_date >= date_from)
        if date_to:
            query = query.filter(SearchIndex.entity_date <= date_to)

        return query

    def _apply_sorting(self, query, sort_by: SortOrder):
        """Apply sorting to the query."""
        if sort_by == SortOrder.RELEVANCE:
            # Sort by relevance score (higher is better)
            query = query.order_by(SearchIndex.relevance_score.desc())
        elif sort_by == SortOrder.DATE_DESC:
            query = query.order_by(SearchIndex.entity_date.desc().nullslast())
        elif sort_by == SortOrder.DATE_ASC:
            query = query.order_by(SearchIndex.entity_date.asc().nullsfirst())
        elif sort_by == SortOrder.TITLE_ASC:
            query = query.order_by(SearchIndex.title.asc())
        elif sort_by == SortOrder.TITLE_DESC:
            query = query.order_by(SearchIndex.title.desc())

        return query

    def _transform_result(
        self,
        index_entry: SearchIndex,
        query: str,
        highlight: bool,
    ) -> SearchResult:
        """Transform a SearchIndex entry to a SearchResult."""
        highlighted_title = None
        highlighted_summary = None

        if highlight:
            highlighted_title = self._highlight_text(index_entry.title, query)
            if index_entry.summary:
                highlighted_summary = self._highlight_text(index_entry.summary, query)

        return SearchResult(
            id=index_entry.entity_id,
            entity_type=index_entry.entity_type.value,
            title=index_entry.title,
            summary=index_entry.summary,
            highlighted_title=highlighted_title,
            highlighted_summary=highlighted_summary,
            status=index_entry.status.value if index_entry.status else None,
            tags=index_entry.tags or [],
            date=index_entry.entity_date,
            relevance_score=index_entry.relevance_score,
            metadata={
                "prospect_id": index_entry.prospect_id,
                "company_id": index_entry.company_id,
                "call_id": index_entry.call_id,
            },
        )

    def _highlight_text(self, text: str, query: str) -> str:
        """Add highlight markers around matching terms."""
        if not text:
            return text

        terms = self._tokenize_query(query)
        highlighted = text

        for term in terms:
            # Case-insensitive replacement with highlight markers
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f"<mark>{term}</mark>", highlighted)

        return highlighted

    # =========================================================================
    # Faceted Filtering
    # =========================================================================

    def _get_facets(self, base_query, filters: Optional[SearchFilters]) -> List[FacetResult]:
        """Calculate facet counts for filter options."""
        facets = []

        # Entity type facet
        entity_type_facet = self._get_entity_type_facet(base_query, filters)
        facets.append(entity_type_facet)

        # Status facet
        status_facet = self._get_status_facet(base_query, filters)
        facets.append(status_facet)

        # Date range facet
        date_facet = self._get_date_facet(base_query, filters)
        facets.append(date_facet)

        # Tags facet (top 10 most common)
        tags_facet = self._get_tags_facet(base_query, filters)
        facets.append(tags_facet)

        return facets

    def _get_entity_type_facet(self, base_query, filters: Optional[SearchFilters]) -> FacetResult:
        """Get facet counts for entity types."""
        # Query without entity type filter to get accurate counts
        query = base_query.with_entities(
            SearchIndex.entity_type,
            func.count(SearchIndex.id).label('count')
        ).group_by(SearchIndex.entity_type)

        results = query.all()

        selected_types = []
        if filters and filters.entity_types:
            selected_types = [et.value for et in filters.entity_types]

        values = [
            FacetValue(
                value=row.entity_type.value,
                count=row.count,
                selected=row.entity_type.value in selected_types
            )
            for row in results
        ]

        return FacetResult(
            name="entity_type",
            display_name="Type",
            values=sorted(values, key=lambda x: -x.count)
        )

    def _get_status_facet(self, base_query, filters: Optional[SearchFilters]) -> FacetResult:
        """Get facet counts for status values."""
        query = base_query.with_entities(
            SearchIndex.status,
            func.count(SearchIndex.id).label('count')
        ).filter(SearchIndex.status.isnot(None)).group_by(SearchIndex.status)

        results = query.all()

        selected_statuses = []
        if filters and filters.status:
            selected_statuses = filters.status

        values = [
            FacetValue(
                value=row.status.value if row.status else "unknown",
                count=row.count,
                selected=row.status.value in selected_statuses if row.status else False
            )
            for row in results
            if row.status
        ]

        return FacetResult(
            name="status",
            display_name="Status",
            values=sorted(values, key=lambda x: -x.count)
        )

    def _get_date_facet(self, base_query, filters: Optional[SearchFilters]) -> FacetResult:
        """Get facet counts for date ranges."""
        now = datetime.utcnow()

        # Calculate counts for each date preset
        date_ranges = [
            ("today", now.replace(hour=0, minute=0, second=0, microsecond=0), now),
            ("last_7_days", now - timedelta(days=7), now),
            ("last_30_days", now - timedelta(days=30), now),
            ("last_90_days", now - timedelta(days=90), now),
            ("this_year", now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), now),
        ]

        selected_preset = None
        if filters and filters.date_preset:
            selected_preset = filters.date_preset.value if hasattr(filters.date_preset, 'value') else filters.date_preset

        values = []
        for name, start, end in date_ranges:
            count = base_query.filter(
                SearchIndex.entity_date >= start,
                SearchIndex.entity_date <= end
            ).count()
            values.append(FacetValue(
                value=name,
                count=count,
                selected=name == selected_preset
            ))

        return FacetResult(
            name="date_range",
            display_name="Date",
            values=values
        )

    def _get_tags_facet(self, base_query, filters: Optional[SearchFilters]) -> FacetResult:
        """Get facet counts for tags (top 10)."""
        # This is a simplified implementation
        # In production, you'd want a more sophisticated approach for JSON arrays
        query = base_query.filter(SearchIndex.tags.isnot(None))
        results = query.limit(1000).all()

        tag_counts: Dict[str, int] = {}
        for result in results:
            if result.tags:
                for tag in result.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        selected_tags = set()
        if filters:
            if filters.tags:
                selected_tags.update(filters.tags)
            if filters.tags_any:
                selected_tags.update(filters.tags_any)

        values = [
            FacetValue(
                value=tag,
                count=count,
                selected=tag in selected_tags
            )
            for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:10]
        ]

        return FacetResult(
            name="tags",
            display_name="Tags",
            values=values
        )

    # =========================================================================
    # Autocomplete & Suggestions
    # =========================================================================

    def autocomplete(
        self,
        request: AutocompleteRequest,
        user_id: int,
        organization_id: Optional[int] = None,
    ) -> AutocompleteResponse:
        """
        Get autocomplete suggestions for a search prefix.

        Combines:
        - Recent searches from user history
        - Popular search terms
        - Entity title matches
        """
        suggestions: List[AutocompleteSuggestion] = []
        prefix = request.prefix.lower().strip()

        # Get recent searches if requested
        if request.include_recent:
            recent = self._get_recent_search_suggestions(user_id, prefix, limit=3)
            suggestions.extend(recent)

        # Get popular suggestions
        popular = self._get_popular_suggestions(prefix, organization_id, limit=3)
        suggestions.extend(popular)

        # Get entity title matches
        entity_matches = self._get_entity_title_matches(
            prefix,
            organization_id,
            request.entity_types,
            limit=request.limit - len(suggestions)
        )
        suggestions.extend(entity_matches)

        # Deduplicate and limit
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s.text.lower() not in seen:
                seen.add(s.text.lower())
                unique_suggestions.append(s)
                if len(unique_suggestions) >= request.limit:
                    break

        return AutocompleteResponse(
            prefix=request.prefix,
            suggestions=unique_suggestions
        )

    def _get_recent_search_suggestions(
        self,
        user_id: int,
        prefix: str,
        limit: int = 3,
    ) -> List[AutocompleteSuggestion]:
        """Get suggestions from user's recent searches."""
        results = self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id,
            SearchHistory.query.ilike(f"{prefix}%")
        ).order_by(
            SearchHistory.created_at.desc()
        ).limit(limit).all()

        return [
            AutocompleteSuggestion(
                text=r.query,
                type="recent",
                frequency=1
            )
            for r in results
        ]

    def _get_popular_suggestions(
        self,
        prefix: str,
        organization_id: Optional[int],
        limit: int = 3,
    ) -> List[AutocompleteSuggestion]:
        """Get popular search term suggestions."""
        query = self.db.query(SearchSuggestion).filter(
            SearchSuggestion.normalized_term.ilike(f"{prefix}%")
        )

        if organization_id:
            query = query.filter(
                or_(
                    SearchSuggestion.organization_id == organization_id,
                    SearchSuggestion.organization_id.is_(None)
                )
            )

        results = query.order_by(
            SearchSuggestion.frequency.desc()
        ).limit(limit).all()

        return [
            AutocompleteSuggestion(
                text=r.term,
                type="popular",
                frequency=r.frequency
            )
            for r in results
        ]

    def _get_entity_title_matches(
        self,
        prefix: str,
        organization_id: Optional[int],
        entity_types: Optional[List[EntityTypeFilter]],
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """Get entity title matches for autocomplete."""
        query = self.db.query(SearchIndex).filter(
            SearchIndex.title.ilike(f"{prefix}%")
        )

        if organization_id:
            query = query.filter(SearchIndex.organization_id == organization_id)

        if entity_types:
            valid_types = [
                EntityType(et.value) for et in entity_types
                if et != EntityTypeFilter.ALL
            ]
            if valid_types:
                query = query.filter(SearchIndex.entity_type.in_(valid_types))

        results = query.order_by(
            SearchIndex.view_count.desc()
        ).limit(limit).all()

        return [
            AutocompleteSuggestion(
                text=r.title,
                type="entity",
                entity_type=r.entity_type.value,
                entity_id=r.entity_id
            )
            for r in results
        ]

    def _update_suggestions(self, query: str, organization_id: Optional[int]) -> None:
        """Update suggestion frequency for a search term."""
        normalized = query.lower().strip()

        if len(normalized) < settings.SEARCH_MIN_QUERY_LENGTH:
            return

        existing = self.db.query(SearchSuggestion).filter(
            SearchSuggestion.normalized_term == normalized
        ).first()

        if existing:
            existing.frequency += 1
            existing.last_used_at = datetime.utcnow()
        else:
            suggestion = SearchSuggestion(
                term=query.strip(),
                normalized_term=normalized,
                frequency=1,
                organization_id=organization_id,
                last_used_at=datetime.utcnow()
            )
            self.db.add(suggestion)

        self.db.commit()

    # =========================================================================
    # Search History
    # =========================================================================

    def get_search_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[SearchHistoryItem], int]:
        """Get recent search history for a user."""
        query = self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(SearchHistory.created_at.desc())

        total = query.count()
        results = query.offset(offset).limit(limit).all()

        items = [
            SearchHistoryItem(
                id=r.id,
                query=r.query,
                filters=r.filters,
                result_count=r.result_count,
                entity_types=r.entity_types,
                created_at=r.created_at
            )
            for r in results
        ]

        return items, total

    def clear_search_history(self, user_id: int) -> int:
        """Clear all search history for a user."""
        deleted = self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).delete()
        self.db.commit()
        return deleted

    def delete_search_history_item(self, user_id: int, history_id: int) -> bool:
        """Delete a specific search history item."""
        result = self.db.query(SearchHistory).filter(
            SearchHistory.id == history_id,
            SearchHistory.user_id == user_id
        ).delete()
        self.db.commit()
        return result > 0

    def _record_search_history(
        self,
        user_id: int,
        query: str,
        filters: Optional[SearchFilters],
        result_count: int,
        entity_types: Optional[List[EntityTypeFilter]],
    ) -> None:
        """Record a search in the user's history."""
        # Check if we should dedupe recent identical searches
        recent = self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id,
            SearchHistory.query == query
        ).order_by(SearchHistory.created_at.desc()).first()

        # Skip if identical search within last minute
        if recent and (datetime.utcnow() - recent.created_at).total_seconds() < 60:
            return

        # Create new history entry
        history = SearchHistory(
            user_id=user_id,
            query=query,
            filters=filters.model_dump() if filters else None,
            result_count=result_count,
            entity_types=[et.value for et in entity_types] if entity_types else None,
            created_at=datetime.utcnow()
        )
        self.db.add(history)

        # Clean up old history entries (keep last N)
        self._cleanup_old_history(user_id)

        self.db.commit()

    def _cleanup_old_history(self, user_id: int) -> None:
        """Remove old history entries beyond the limit."""
        # Get IDs to keep
        keep_ids = self.db.query(SearchHistory.id).filter(
            SearchHistory.user_id == user_id
        ).order_by(
            SearchHistory.created_at.desc()
        ).limit(settings.SEARCH_HISTORY_LIMIT).all()

        keep_ids = [r[0] for r in keep_ids]

        if keep_ids:
            # Delete entries not in keep list
            self.db.query(SearchHistory).filter(
                SearchHistory.user_id == user_id,
                ~SearchHistory.id.in_(keep_ids)
            ).delete(synchronize_session=False)

    # =========================================================================
    # Saved Searches
    # =========================================================================

    def create_saved_search(
        self,
        user_id: int,
        data: SavedSearchCreate,
    ) -> SavedSearchResponse:
        """Create a new saved search."""
        # If this is set as default, unset other defaults
        if data.is_default:
            self.db.query(SavedSearch).filter(
                SavedSearch.user_id == user_id,
                SavedSearch.is_default == True
            ).update({"is_default": False})

        saved_search = SavedSearch(
            user_id=user_id,
            name=data.name,
            description=data.description,
            query=data.query,
            filters=data.filters.model_dump() if data.filters else None,
            entity_types=[et.value for et in data.entity_types] if data.entity_types else None,
            is_default=data.is_default,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(saved_search)
        self.db.commit()
        self.db.refresh(saved_search)

        return SavedSearchResponse.model_validate(saved_search)

    def get_saved_searches(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SavedSearchResponse], int]:
        """Get all saved searches for a user."""
        query = self.db.query(SavedSearch).filter(
            SavedSearch.user_id == user_id
        ).order_by(SavedSearch.use_count.desc(), SavedSearch.updated_at.desc())

        total = query.count()
        results = query.offset(offset).limit(limit).all()

        return [SavedSearchResponse.model_validate(r) for r in results], total

    def get_saved_search(self, user_id: int, search_id: int) -> Optional[SavedSearchResponse]:
        """Get a specific saved search."""
        result = self.db.query(SavedSearch).filter(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id
        ).first()

        if result:
            return SavedSearchResponse.model_validate(result)
        return None

    def update_saved_search(
        self,
        user_id: int,
        search_id: int,
        data: SavedSearchUpdate,
    ) -> Optional[SavedSearchResponse]:
        """Update a saved search."""
        saved_search = self.db.query(SavedSearch).filter(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id
        ).first()

        if not saved_search:
            return None

        # If setting as default, unset other defaults
        if data.is_default:
            self.db.query(SavedSearch).filter(
                SavedSearch.user_id == user_id,
                SavedSearch.id != search_id,
                SavedSearch.is_default == True
            ).update({"is_default": False})

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        if "filters" in update_data and update_data["filters"]:
            update_data["filters"] = update_data["filters"].model_dump()
        if "entity_types" in update_data and update_data["entity_types"]:
            update_data["entity_types"] = [et.value for et in update_data["entity_types"]]

        for field, value in update_data.items():
            setattr(saved_search, field, value)

        saved_search.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(saved_search)

        return SavedSearchResponse.model_validate(saved_search)

    def delete_saved_search(self, user_id: int, search_id: int) -> bool:
        """Delete a saved search."""
        result = self.db.query(SavedSearch).filter(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id
        ).delete()
        self.db.commit()
        return result > 0

    def execute_saved_search(
        self,
        user_id: int,
        search_id: int,
        organization_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[SearchResponse]:
        """Execute a saved search and increment use count."""
        saved_search = self.db.query(SavedSearch).filter(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id
        ).first()

        if not saved_search:
            return None

        # Increment use count
        saved_search.use_count += 1
        saved_search.last_used_at = datetime.utcnow()
        self.db.commit()

        # Build search request from saved search
        filters = None
        if saved_search.filters:
            filters = SearchFilters(**saved_search.filters)

        request = SearchRequest(
            query=saved_search.query,
            filters=filters,
            page=page,
            page_size=page_size
        )

        return self.search(request, user_id, organization_id)
