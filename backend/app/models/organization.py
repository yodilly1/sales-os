"""Organization model for multi-tenant support."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization model representing a company/tenant."""

    __tablename__ = "organizations"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color

    # Settings (JSON for flexibility)
    settings: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Billing/Plan info (for future use)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    max_users: Mapped[int] = mapped_column(default=5, nullable=False)
    max_teams: Mapped[int] = mapped_column(default=3, nullable=False)

    # Relationships
    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def default_settings(self) -> dict:
        """Get default organization settings."""
        return {
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD",
            "enable_coaching": True,
            "enable_content_generation": True,
            "enable_enrichment": True,
            "notification_preferences": {
                "email_notifications": True,
                "weekly_digest": True,
            },
        }

    def get_setting(self, key: str, default=None):
        """Get a specific setting value."""
        return self.settings.get(key, default)

    def update_settings(self, new_settings: dict) -> None:
        """Update organization settings."""
        self.settings = {**self.settings, **new_settings}
