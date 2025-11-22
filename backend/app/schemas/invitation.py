"""Pydantic schemas for Invitation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class InvitationCreate(BaseModel):
    """Schema for creating an invitation."""

    email: EmailStr
    role: UserRole = UserRole.REP
    team_id: str | None = None
    message: str | None = Field(None, max_length=500)


class InvitationResponse(BaseModel):
    """Schema for invitation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    organization_id: str
    team_id: str | None
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by_email: str | None = None
    invited_by_name: str | None = None


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    token: str
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class InvitationListResponse(BaseModel):
    """Schema for listing invitations."""

    items: list[InvitationResponse]
    total: int
    page: int
    per_page: int


class InvitationResend(BaseModel):
    """Schema for resending an invitation."""

    invitation_id: str
