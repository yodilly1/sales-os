"""Team model for organizing users within an organization."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Team(Base, UUIDMixin, TimestampMixin):
    """Team model representing a sales team within an organization."""

    __tablename__ = "teams"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Organization
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Team settings (inherits from org but can override)
    settings: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="teams",
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, org_id={self.organization_id})>"

    def get_setting(self, key: str, default=None):
        """Get a setting, falling back to organization settings."""
        if key in self.settings:
            return self.settings[key]
        return self.organization.get_setting(key, default)

    def get_effective_settings(self) -> dict:
        """Get merged settings (org defaults + team overrides)."""
        org_settings = self.organization.settings.copy() if self.organization else {}
        return {**org_settings, **self.settings}

    @property
    def member_count(self) -> int:
        """Get the number of active team members."""
        return len([m for m in self.members if m.is_active])


class TeamMember(Base, UUIDMixin, TimestampMixin):
    """Association table for users in teams with additional metadata."""

    __tablename__ = "team_members"

    # Foreign keys
    team_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role within team
    is_team_lead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships",
    )

    def __repr__(self) -> str:
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, lead={self.is_team_lead})>"
