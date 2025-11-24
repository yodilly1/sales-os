"""User, Team, and Organization Pydantic schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


# ==================== Organization Schemas ====================


class OrganizationBase(BaseSchema):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)


class OrganizationResponse(OrganizationBase, IDSchema, TimestampSchema):
    """Schema for organization response."""

    pass


# ==================== Team Schemas ====================


class TeamBase(BaseSchema):
    """Base team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    organization_id: str
    manager_id: Optional[str] = None


class TeamUpdate(BaseSchema):
    """Schema for updating a team."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[str] = None


class TeamResponse(TeamBase, IDSchema, TimestampSchema):
    """Schema for team response."""

    organization_id: str
    manager_id: Optional[str] = None


# ==================== User Schemas ====================


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.SALES_REP
    phone: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field("UTC", max_length=50)


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, max_length=100)
    organization_id: str
    team_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    team_id: Optional[str] = None


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(IDSchema, TimestampSchema):
    """Schema for user response."""

    email: EmailStr
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool
    phone: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_id: str
    team_id: Optional[str] = None
    last_login_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class UserWithOrganization(UserResponse):
    """User response with organization details."""

    organization: OrganizationResponse
    team: Optional[TeamResponse] = None
