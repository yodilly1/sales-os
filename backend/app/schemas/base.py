"""Base Pydantic schemas and utilities."""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: str


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: List[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Generic error response."""

    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
