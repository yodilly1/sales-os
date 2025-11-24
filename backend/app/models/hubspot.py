"""HubSpot Integration model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class HubSpotIntegration(Base, TimestampMixin):
    """HubSpot OAuth2 integration and sync tracking."""

    __tablename__ = "hubspot_integrations"

    # OAuth2 tokens
    access_token: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Scope and permissions
    scopes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # HubSpot account info
    hub_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hub_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hub_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Integration status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Sync tracking
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sync statistics
    contacts_synced: Mapped[int] = mapped_column(default=0, nullable=False)
    companies_synced: Mapped[int] = mapped_column(default=0, nullable=False)
    deals_synced: Mapped[int] = mapped_column(default=0, nullable=False)

    # Field mapping configuration (JSON)
    contact_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deal_field_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, unique=True
    )

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        return datetime.utcnow() >= self.token_expires_at.replace(tzinfo=None)

    def __repr__(self) -> str:
        return f"<HubSpotIntegration hub_id={self.hub_id}>"
