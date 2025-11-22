"""Pydantic schemas for Team and TeamMember."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    """Base schema for Team."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    settings: dict = Field(default_factory=dict)


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    settings: dict | None = None
    is_active: bool | None = None


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    team_id: str
    is_team_lead: bool
    is_active: bool
    created_at: datetime
    # User details (populated from relationship)
    user_email: str | None = None
    user_name: str | None = None


class TeamResponse(TeamBase):
    """Schema for team response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    organization_id: str
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: int = 0


class TeamWithMembersResponse(TeamResponse):
    """Schema for team response with members."""

    members: list[TeamMemberResponse] = []


class TeamListResponse(BaseModel):
    """Schema for listing teams."""

    items: list[TeamResponse]
    total: int
    page: int
    per_page: int


class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team."""

    user_id: str
    is_team_lead: bool = False


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""

    is_team_lead: bool | None = None
    is_active: bool | None = None


class TeamPerformanceResponse(BaseModel):
    """Schema for team performance aggregation."""

    team_id: str
    team_name: str
    total_members: int
    active_members: int
    total_calls: int = 0
    avg_spiced_score: float | None = None
    total_content_generated: int = 0
    period_start: datetime | None = None
    period_end: datetime | None = None
