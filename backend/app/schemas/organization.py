"""Pydantic schemas for Organization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Base schema for Organization."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    settings: dict = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    settings: dict | None = None
    is_active: bool | None = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    settings: dict
    is_active: bool
    plan: str
    max_users: int
    max_teams: int
    created_at: datetime
    updated_at: datetime


class OrganizationListResponse(BaseModel):
    """Schema for listing organizations."""

    items: list[OrganizationResponse]
    total: int
    page: int
    per_page: int
