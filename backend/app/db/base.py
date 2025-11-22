<<<<<<< HEAD
<<<<<<< HEAD
"""SQLAlchemy Base model with common fields."""
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
=======
"""SQLAlchemy Base model."""

from sqlalchemy.orm import DeclarativeBase
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef


class Base(DeclarativeBase):
    """Base class for all database models."""

<<<<<<< HEAD
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
=======
"""SQLAlchemy base model and common mixins."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

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


class SoftDeleteMixin:
<<<<<<< HEAD
    """Mixin for soft delete functionality."""
=======
    """Mixin that adds soft delete capability."""
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
<<<<<<< HEAD
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
=======
    pass
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
=======
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
