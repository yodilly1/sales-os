"""
Search indexer for maintaining the search index.

Provides methods to index, update, and remove entities from the search index.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.search import (
    EntityType,
    SearchStatus,
    SearchIndex,
)


class SearchIndexer:
    """
    Service for managing the search index.

    Provides methods to:
    - Index new entities
    - Update existing entities
    - Remove entities from index
    - Bulk index operations
    - Reindex all entities
    """

    def __init__(self, db: Session):
        self.db = db

    def index_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        content_subtype: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        prospect_id: Optional[int] = None,
        company_id: Optional[int] = None,
        call_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
        relevance_score: float = 1.0,
    ) -> SearchIndex:
        """
        Index or update a single entity in the search index.

        Args:
            entity_type: Type of entity being indexed
            entity_id: ID of the entity
            title: Title/name of the entity
            content: Full-text searchable content
            summary: Short summary for preview
            status: Entity status
            content_subtype: Content type (for content entities)
            tags: List of tags
            user_id: Owner user ID
            organization_id: Organization ID
            prospect_id: Related prospect ID
            company_id: Related company ID
            call_id: Related call ID
            entity_date: Date of the entity
            relevance_score: Base relevance score

        Returns:
            The created or updated SearchIndex entry
        """
        # Check if already indexed
        existing = self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).first()

        if existing:
            # Update existing entry
            existing.title = title
            existing.content = content
            existing.summary = summary
            existing.status = status
            existing.content_subtype = content_subtype
            existing.tags = tags
            existing.user_id = user_id
            existing.organization_id = organization_id
            existing.prospect_id = prospect_id
            existing.company_id = company_id
            existing.call_id = call_id
            existing.entity_date = entity_date
            existing.relevance_score = relevance_score
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new entry
            index_entry = SearchIndex(
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                content=content,
                summary=summary,
                status=status,
                content_subtype=content_subtype,
                tags=tags,
                user_id=user_id,
                organization_id=organization_id,
                prospect_id=prospect_id,
                company_id=company_id,
                call_id=call_id,
                entity_date=entity_date or datetime.utcnow(),
                relevance_score=relevance_score,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(index_entry)
            self.db.commit()
            self.db.refresh(index_entry)
            return index_entry

    def remove_entity(self, entity_type: EntityType, entity_id: int) -> bool:
        """
        Remove an entity from the search index.

        Args:
            entity_type: Type of entity to remove
            entity_id: ID of the entity

        Returns:
            True if entity was removed, False if not found
        """
        result = self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).delete()
        self.db.commit()
        return result > 0

    def bulk_index(self, entities: List[Dict[str, Any]]) -> int:
        """
        Bulk index multiple entities.

        Args:
            entities: List of entity dictionaries with required fields

        Returns:
            Number of entities indexed
        """
        count = 0
        for entity_data in entities:
            try:
                self.index_entity(
                    entity_type=EntityType(entity_data["entity_type"]),
                    entity_id=entity_data["entity_id"],
                    title=entity_data["title"],
                    content=entity_data.get("content"),
                    summary=entity_data.get("summary"),
                    status=SearchStatus(entity_data["status"]) if entity_data.get("status") else None,
                    content_subtype=entity_data.get("content_subtype"),
                    tags=entity_data.get("tags"),
                    user_id=entity_data.get("user_id"),
                    organization_id=entity_data.get("organization_id"),
                    prospect_id=entity_data.get("prospect_id"),
                    company_id=entity_data.get("company_id"),
                    call_id=entity_data.get("call_id"),
                    entity_date=entity_data.get("entity_date"),
                    relevance_score=entity_data.get("relevance_score", 1.0),
                )
                count += 1
            except Exception:
                # Log error but continue with other entities
                continue

        return count

    def bulk_remove(self, entity_type: EntityType, entity_ids: List[int]) -> int:
        """
        Bulk remove entities from the index.

        Args:
            entity_type: Type of entities to remove
            entity_ids: List of entity IDs to remove

        Returns:
            Number of entities removed
        """
        result = self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id.in_(entity_ids)
        ).delete(synchronize_session=False)
        self.db.commit()
        return result

    def update_view_count(self, entity_type: EntityType, entity_id: int) -> None:
        """
        Increment the view count for an entity.

        This can be used to boost relevance of frequently viewed items.
        """
        self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).update(
            {"view_count": SearchIndex.view_count + 1},
            synchronize_session=False
        )
        self.db.commit()

    def update_relevance_score(
        self,
        entity_type: EntityType,
        entity_id: int,
        score: float,
    ) -> None:
        """
        Update the relevance score for an entity.

        This can be used to manually boost or lower entity rankings.
        """
        self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).update(
            {"relevance_score": score},
            synchronize_session=False
        )
        self.db.commit()

    def clear_index(self, entity_type: Optional[EntityType] = None) -> int:
        """
        Clear the search index.

        Args:
            entity_type: Optional type to clear (clears all if not specified)

        Returns:
            Number of entries cleared
        """
        query = self.db.query(SearchIndex)
        if entity_type:
            query = query.filter(SearchIndex.entity_type == entity_type)

        result = query.delete(synchronize_session=False)
        self.db.commit()
        return result

    # =========================================================================
    # Entity-specific indexing helpers
    # =========================================================================

    def index_transcript(
        self,
        transcript_id: int,
        title: str,
        content: str,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        call_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index a transcript."""
        return self.index_entity(
            entity_type=EntityType.TRANSCRIPT,
            entity_id=transcript_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            call_id=call_id,
            entity_date=entity_date,
        )

    def index_call(
        self,
        call_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        prospect_id: Optional[int] = None,
        company_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index a call."""
        return self.index_entity(
            entity_type=EntityType.CALL,
            entity_id=call_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            prospect_id=prospect_id,
            company_id=company_id,
            call_id=call_id,
            entity_date=entity_date,
        )

    def index_content(
        self,
        content_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        content_subtype: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        prospect_id: Optional[int] = None,
        company_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index generated content."""
        return self.index_entity(
            entity_type=EntityType.CONTENT,
            entity_id=content_id,
            title=title,
            content=content,
            summary=summary,
            content_subtype=content_subtype,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            prospect_id=prospect_id,
            company_id=company_id,
            entity_date=entity_date,
        )

    def index_prospect(
        self,
        prospect_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        company_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index a prospect."""
        return self.index_entity(
            entity_type=EntityType.PROSPECT,
            entity_id=prospect_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            prospect_id=prospect_id,
            company_id=company_id,
            entity_date=entity_date,
        )

    def index_company(
        self,
        company_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index a company."""
        return self.index_entity(
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            company_id=company_id,
            entity_date=entity_date,
        )

    def index_coaching_report(
        self,
        report_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[SearchStatus] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        call_id: Optional[int] = None,
        entity_date: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index a coaching report."""
        return self.index_entity(
            entity_type=EntityType.COACHING_REPORT,
            entity_id=report_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            tags=tags,
            user_id=user_id,
            organization_id=organization_id,
            call_id=call_id,
            entity_date=entity_date,
        )
