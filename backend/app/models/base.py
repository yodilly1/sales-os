<<<<<<< HEAD
"""
Base model configuration for SQLAlchemy ORM.

This module provides the declarative base class used by all database models
in the Sales OS application.
"""

from sqlalchemy.orm import declarative_base

# Create the declarative base class
Base = declarative_base()
=======
"""Base models for SQLAlchemy and Pydantic."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
import uuid

# SQLAlchemy Base
Base = declarative_base()


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )


class BaseModel(PydanticBaseModel):
    """Base Pydantic model with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class BaseDBModel(Base, UUIDMixin, TimestampMixin):
    """Base database model with UUID and timestamps."""

    __abstract__ = True


class TimestampedSchema(BaseModel):
    """Base schema with timestamps."""

    id: str
    created_at: datetime
    updated_at: datetime
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3
