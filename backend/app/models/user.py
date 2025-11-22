"""User model with role-based access control."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.team import TeamMember


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"  # Full access to org, can manage everything
    MANAGER = "manager"  # Can manage team, view team data, create content
    REP = "rep"  # Can view own data, create content for self


class User(Base, UUIDMixin, TimestampMixin):
    """User model representing a person in the system."""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Organization membership
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.REP.value,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="users",
    )
    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN.value

    @property
    def is_manager(self) -> bool:
        """Check if user is a manager or higher."""
        return self.role in [UserRole.ADMIN.value, UserRole.MANAGER.value]

    def can_manage_team(self, team_id: str) -> bool:
        """Check if user can manage a specific team."""
        if self.is_admin:
            return True
        for membership in self.team_memberships:
            if membership.team_id == team_id and membership.is_team_lead:
                return True
        return False

    def can_view_user_data(self, user_id: str) -> bool:
        """Check if user can view another user's data."""
        if self.id == user_id:
            return True
        if self.is_admin:
            return True
        # Managers can view their team members' data
        if self.is_manager:
            for membership in self.team_memberships:
                if membership.is_team_lead:
                    for team_member in membership.team.members:
                        if team_member.user_id == user_id:
                            return True
        return False
