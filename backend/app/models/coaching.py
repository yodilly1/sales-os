"""Coaching Report and Score models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.transcript import Call
    from app.models.user import User


class CoachingLevel(str, Enum):
    """Overall coaching level assessment."""

    NEEDS_IMPROVEMENT = "needs_improvement"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CoachingScore(Base, TimestampMixin):
    """Individual SPICED component scores for coaching.

    Tracks scores for each SPICED element with detailed feedback.
    """

    __tablename__ = "coaching_scores"

    # SPICED Component
    component: Mapped[str] = mapped_column(String(50), nullable=False)  # S, P, I, C, E, D

    # Score (1-5 scale)
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Detailed feedback
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    areas_for_improvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Evidence from the call
    evidence_quotes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    missed_opportunities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Recommended actions
    recommended_questions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    best_practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Foreign Keys
    coaching_report_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("coaching_reports.id"), nullable=False
    )

    # Relationships
    coaching_report: Mapped["CoachingReport"] = relationship(
        "CoachingReport", back_populates="scores"
    )

    def __repr__(self) -> str:
        return f"<CoachingScore {self.component}: {self.score}>"


class CoachingReport(Base, TimestampMixin):
    """Comprehensive coaching report for a sales call.

    Based on Winning by Design methodology for SPICED coaching.
    """

    __tablename__ = "coaching_reports"

    # Overall assessment
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Summary feedback
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    key_improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Winning by Design alignment
    wbd_methodology_alignment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wbd_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Action items and next steps
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    learning_resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    practice_scenarios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Trend analysis (comparison with previous reports)
    improvement_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    regression_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    trend_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing metadata
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    call_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("calls.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="coaching_reports")
    user: Mapped["User"] = relationship("User", back_populates="coaching_reports")
    scores: Mapped[list["CoachingScore"]] = relationship(
        "CoachingScore", back_populates="coaching_report", cascade="all, delete-orphan"
    )

    @property
    def average_spiced_score(self) -> Optional[float]:
        """Calculate average score across all SPICED components."""
        if not self.scores:
            return None
        return sum(s.score for s in self.scores) / len(self.scores)

    def get_score_by_component(self, component: str) -> Optional["CoachingScore"]:
        """Get score for a specific SPICED component."""
        for score in self.scores:
            if score.component.upper() == component.upper():
                return score
        return None

    def __repr__(self) -> str:
        return f"<CoachingReport {self.overall_score} for Call {self.call_id}>"
