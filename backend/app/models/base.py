"""
Base model configuration for SQLAlchemy ORM.

This module provides the declarative base class used by all database models
in the Sales OS application.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel, Field
from app.db.base import Base, TimestampMixin

# Alias for backward compatibility
BaseDBModel = Base
TimestampMixin = TimestampMixin

# Pydantic Base Model
class BaseModel(PydanticBaseModel):
    """Base Pydantic model."""
    pass

class TimestampedSchema(BaseModel):
    """Base schema with timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
