"""OAuth Token database model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.constants import OAuthProvider


class OAuthToken(Base):
    """OAuth Token model for storing integration tokens."""

    __tablename__ = "oauth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    token_type: Mapped[str] = mapped_column(
        String(50),
        default="Bearer",
        nullable=False,
    )
    scope: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="oauth_tokens",
    )

    def __repr__(self) -> str:
        return f"<OAuthToken(id={self.id}, provider={self.provider}, user_id={self.user_id})>"

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def needs_refresh(self, buffer_minutes: int = 5) -> bool:
        """Check if token needs refresh (expired or expiring soon)."""
        if self.expires_at is None:
            return False
        from datetime import timedelta
        buffer_time = datetime.now(self.expires_at.tzinfo) + timedelta(minutes=buffer_minutes)
        return buffer_time > self.expires_at
