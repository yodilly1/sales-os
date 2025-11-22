"""Pydantic schemas for Authentication."""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Schema for registration (first user in org)."""

    # Organization info
    organization_name: str = Field(..., min_length=1, max_length=255)
    organization_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")

    # User info
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""

    sub: str  # User ID
    org_id: str  # Organization ID
    role: str  # User role
    exp: int  # Expiration timestamp
    type: str  # Token type (access/refresh)


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing tokens."""

    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=8)
