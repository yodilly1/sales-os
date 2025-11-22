"""Pydantic schemas for User."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for User."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.REP
    title: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = None
    title: str | None = None
    bio: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: str | None = None
    title: str | None = None
    bio: str | None = None
    phone: str | None = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Schema for listing users."""

    items: list[UserResponse]
    total: int
    page: int
    per_page: int


class UserWithTeamsResponse(UserResponse):
    """Schema for user response with team memberships."""

    teams: list[dict] = []  # List of team info dicts
