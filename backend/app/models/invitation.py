"""Invitation model for user invitations."""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.user import UserRole

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.team import Team
    from app.models.user import User


class InvitationStatus(str, Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Invitation(Base, UUIDMixin, TimestampMixin):
    """Invitation model for inviting users to organizations/teams."""

    __tablename__ = "invitations"

    # Invitation details
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Role assignment
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.REP.value,
        nullable=False,
    )

    # Organization
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional team assignment
    team_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Who sent the invitation
    invited_by_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=InvitationStatus.PENDING.value,
        nullable=False,
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # When accepted
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    team: Mapped["Team | None"] = relationship("Team")
    invited_by: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email={self.email}, status={self.status})>"

    @classmethod
    def create_with_expiry(
        cls,
        email: str,
        token: str,
        organization_id: str,
        invited_by_id: str,
        role: str = UserRole.REP.value,
        team_id: str | None = None,
        message: str | None = None,
        expiry_hours: int = 72,
    ) -> "Invitation":
        """Create an invitation with a default expiry."""
        return cls(
            email=email,
            token=token,
            organization_id=organization_id,
            invited_by_id=invited_by_id,
            role=role,
            team_id=team_id,
            message=message,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the invitation is still valid."""
        return (
            self.status == InvitationStatus.PENDING.value
            and not self.is_expired
        )

    def accept(self) -> None:
        """Mark the invitation as accepted."""
        self.status = InvitationStatus.ACCEPTED.value
        self.accepted_at = datetime.now(timezone.utc)

    def revoke(self) -> None:
        """Revoke the invitation."""
        self.status = InvitationStatus.REVOKED.value

    def mark_expired(self) -> None:
        """Mark the invitation as expired."""
        self.status = InvitationStatus.EXPIRED.value
