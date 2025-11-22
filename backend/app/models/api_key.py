"""API Key database model."""

import secrets
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.config import settings


class APIKey(Base):
    """API Key model for programmatic access."""

    __tablename__ = "api_keys"

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
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    scopes: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>"

    @classmethod
    def generate_key(cls) -> tuple[str, str]:
        """Generate a new API key and return (raw_key, key_prefix)."""
        raw_key = settings.api_key_prefix + secrets.token_urlsafe(settings.api_key_length)
        key_prefix = raw_key[:12] + "..."
        return raw_key, key_prefix

    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
