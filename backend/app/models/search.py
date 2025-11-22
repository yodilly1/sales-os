"""
Search-related database models for Sales OS.

This module defines models for:
- SearchHistory: Tracks recent user searches
- SavedSearch: Persists saved search queries
- SearchIndex: Maintains searchable entity index for fast lookups
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Index,
    Enum as SQLEnum,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EntityType(str, Enum):
    """Types of searchable entities in the system."""
    TRANSCRIPT = "transcript"
    CALL = "call"
    CONTENT = "content"
    PROSPECT = "prospect"
    COMPANY = "company"
    COACHING_REPORT = "coaching_report"


class ContentType(str, Enum):
    """Types of generated content."""
    DECK = "deck"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"


class SearchStatus(str, Enum):
    """Status values for searchable entities."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    PENDING = "pending"


class SearchHistory(Base):
    """
    Tracks recent search queries per user.

    Stores the last N searches for each user to provide
    quick access to recent searches and search suggestions.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(String(500), nullable=False)
    filters = Column(JSON, nullable=True)  # Stores applied filters as JSON
    result_count = Column(Integer, default=0)
    entity_types = Column(JSON, nullable=True)  # List of entity types searched
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_search_history_user_created", "user_id", "created_at"),
        Index("ix_search_history_query", "query"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query": self.query,
            "filters": self.filters,
            "result_count": self.result_count,
            "entity_types": self.entity_types,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SavedSearch(Base):
    """
    Persists saved search queries for users.

    Allows users to save frequently used search queries
    with filters for quick access.
    """
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    query = Column(String(500), nullable=False)
    filters = Column(JSON, nullable=True)  # Stores filter configuration
    entity_types = Column(JSON, nullable=True)  # Entity types to search
    is_default = Column(Boolean, default=False)  # Quick access default
    use_count = Column(Integer, default=0)  # Track usage frequency
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_saved_searches_user_name", "user_id", "name"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "query": self.query,
            "filters": self.filters,
            "entity_types": self.entity_types,
            "is_default": self.is_default,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class SearchIndex(Base):
    """
    Unified search index for all searchable entities.

    Maintains a denormalized index of searchable content
    for fast full-text search across all entity types.
    """
    __tablename__ = "search_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)

    # Searchable content fields
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)  # Full-text searchable content
    summary = Column(Text, nullable=True)  # Short description for previews

    # Metadata for filtering
    status = Column(SQLEnum(SearchStatus), nullable=True, index=True)
    content_subtype = Column(String(50), nullable=True)  # e.g., deck, proposal
    tags = Column(JSON, nullable=True)  # List of tags

    # Ownership and organization
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)

    # Related entities for filtering
    prospect_id = Column(Integer, nullable=True, index=True)
    company_id = Column(Integer, nullable=True, index=True)
    call_id = Column(Integer, nullable=True, index=True)

    # Scoring and ranking
    relevance_score = Column(Float, default=1.0)
    view_count = Column(Integer, default=0)

    # Timestamps for date filtering
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entity_date = Column(DateTime, nullable=True, index=True)  # Original entity date

    __table_args__ = (
        Index("ix_search_index_entity", "entity_type", "entity_id", unique=True),
        Index("ix_search_index_user_type", "user_id", "entity_type"),
        Index("ix_search_index_org_type", "organization_id", "entity_type"),
        Index("ix_search_index_date_range", "entity_date", "entity_type"),
        # Full-text search index (PostgreSQL specific - will use GIN index)
        Index("ix_search_index_title_content", "title", "content"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type.value if self.entity_type else None,
            "entity_id": self.entity_id,
            "title": self.title,
            "summary": self.summary,
            "status": self.status.value if self.status else None,
            "content_subtype": self.content_subtype,
            "tags": self.tags,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "prospect_id": self.prospect_id,
            "company_id": self.company_id,
            "call_id": self.call_id,
            "relevance_score": self.relevance_score,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "entity_date": self.entity_date.isoformat() if self.entity_date else None,
        }

    def to_search_result(self) -> Dict[str, Any]:
        """Convert to a search result format for API responses."""
        return {
            "id": self.entity_id,
            "type": self.entity_type.value if self.entity_type else None,
            "title": self.title,
            "summary": self.summary,
            "status": self.status.value if self.status else None,
            "tags": self.tags or [],
            "date": self.entity_date.isoformat() if self.entity_date else None,
            "relevance_score": self.relevance_score,
        }


class SearchSuggestion(Base):
    """
    Stores popular search terms for autocomplete suggestions.

    Aggregates search terms with their frequency and recency
    for providing intelligent autocomplete suggestions.
    """
    __tablename__ = "search_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(255), nullable=False, unique=True, index=True)
    normalized_term = Column(String(255), nullable=False, index=True)  # Lowercase, trimmed
    frequency = Column(Integer, default=1)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    organization_id = Column(Integer, nullable=True, index=True)  # Org-specific suggestions

    __table_args__ = (
        Index("ix_search_suggestions_org_freq", "organization_id", "frequency"),
        Index("ix_search_suggestions_prefix", "normalized_term"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "term": self.term,
            "frequency": self.frequency,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
