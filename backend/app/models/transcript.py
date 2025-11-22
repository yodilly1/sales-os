"""Call and Transcript models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.coaching import CoachingReport
    from app.models.prospect import Company, Prospect
    from app.models.spiced import SPICEDAnalysis
    from app.models.user import User


class CallSource(str, Enum):
    """Source of the call recording."""

    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    AVOMA = "avoma"
    GONG = "gong"
    CHORUS = "chorus"
    MANUAL_UPLOAD = "manual_upload"
    OTHER = "other"


class CallType(str, Enum):
    """Type of sales call."""

    DISCOVERY = "discovery"
    DEMO = "demo"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"
    CHECK_IN = "check_in"
    KICKOFF = "kickoff"
    OTHER = "other"


class CallStatus(str, Enum):
    """Status of the call processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Call(Base, TimestampMixin, SoftDeleteMixin):
    """Call model representing a sales call."""

    __tablename__ = "calls"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default=CallSource.MANUAL_UPLOAD.value, nullable=False)
    call_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=CallStatus.PENDING.value, nullable=False)

    # Call timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Participants (stored as JSON string)
    participants: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    prospect_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("prospects.id"), nullable=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="calls")
    prospect: Mapped[Optional["Prospect"]] = relationship("Prospect", back_populates="calls")
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="calls")
    transcript: Mapped[Optional["Transcript"]] = relationship(
        "Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    spiced_analysis: Mapped[Optional["SPICEDAnalysis"]] = relationship(
        "SPICEDAnalysis", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    coaching_reports: Mapped[List["CoachingReport"]] = relationship(
        "CoachingReport", back_populates="call", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Call {self.title}>"


class Transcript(Base, TimestampMixin):
    """Transcript model for storing call transcriptions."""

    __tablename__ = "transcripts"

    # Raw transcript text
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured transcript with speaker labels (JSON string)
    structured_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Processing info
    transcription_service: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    call_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("calls.id"), nullable=False, unique=True
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="transcript")

    def __repr__(self) -> str:
        return f"<Transcript for Call {self.call_id}>"
