"""SPICED Analysis model for Winning by Design methodology."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.transcript import Call


class SPICEDAnalysis(Base, TimestampMixin):
    """SPICED Analysis model following Winning by Design methodology.

    SPICED Framework:
    - S: Situation - Current state and context
    - P: Pain - Key challenges and problems
    - I: Impact - Business impact of the pain
    - C: Critical Event - Timeline drivers and urgency
    - E: Expected Decision - Decision process and criteria
    - D: Decision Criteria - What factors will influence the decision
    """

    __tablename__ = "spiced_analyses"

    # SPICED Components - Extracted content
    situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    critical_event: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SPICED Scores (1-5 scale for quality of information gathered)
    situation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pain_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impact_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    critical_event_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_decision_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decision_criteria_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Overall score and confidence
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Generated content
    call_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    call_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_tasks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    key_quotes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Gaps identified in the discovery
    gaps_identified: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    recommended_questions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Processing metadata
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    call_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("calls.id"), nullable=False, unique=True
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="spiced_analysis")

    @property
    def average_score(self) -> Optional[float]:
        """Calculate average SPICED score."""
        scores = [
            self.situation_score,
            self.pain_score,
            self.impact_score,
            self.critical_event_score,
            self.expected_decision_score,
            self.decision_criteria_score,
        ]
        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return None
        return sum(valid_scores) / len(valid_scores)

    def __repr__(self) -> str:
        return f"<SPICEDAnalysis for Call {self.call_id}>"
