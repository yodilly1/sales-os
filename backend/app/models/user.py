"""User, Team, and Organization models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.audit_log import AuditLog
    from app.models.coaching import CoachingReport
    from app.models.content import Content
    from app.models.notification import Notification, NotificationPreference
    from app.models.oauth_token import OAuthToken
    from app.models.transcript import Call


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """Organization model representing a company using Sales OS."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON settings

    # API keys for integrations (encrypted in production)
    hubspot_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    claude_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    teams: Mapped[List["Team"]] = relationship(
        "Team", back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"


class Team(Base, TimestampMixin, SoftDeleteMixin):
    """Team model for organizing users within an organization."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False
    )
    manager_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="teams"
    )
    members: Mapped[List["User"]] = relationship(
        "User", back_populates="team", foreign_keys="User.team_id"
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[manager_id], post_update=True
    )

    def __repr__(self) -> str:
        return f"<Team {self.name}>"


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.SALES_REP.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="UTC", nullable=True)

    # Last activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("teams.id"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    team: Mapped[Optional["Team"]] = relationship(
        Team, back_populates="members", foreign_keys=[team_id]
    )
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="user")
    content: Mapped[List["Content"]] = relationship("Content", back_populates="created_by")
    coaching_reports: Mapped[List["CoachingReport"]] = relationship(
        "CoachingReport", back_populates="user"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship(
        "OAuthToken", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[List["NotificationPreference"]] = relationship(
        "NotificationPreference", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
