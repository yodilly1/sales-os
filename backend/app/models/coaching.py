"""Coaching report and score models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Float

from .base import BaseDBModel, BaseModel, TimestampedSchema


class CoachingScore(BaseDBModel):
    """Individual SPICED element score."""

    __tablename__ = "coaching_scores"

    report_id = Column(String(36), ForeignKey("coaching_reports.id"), nullable=False)

    # SPICED Element being scored
    element = Column(String(50), nullable=False)  # situation, pain, impact, etc.

    # Score (1-5)
    score = Column(Integer, nullable=False)

    # Feedback
    feedback = Column(Text)
    strengths = Column(JSON, default=list)
    improvements = Column(JSON, default=list)
    examples = Column(JSON, default=list)  # Specific examples from transcript


class CoachingReport(BaseDBModel):
    """Coaching feedback report for a call."""

    __tablename__ = "coaching_reports"

    transcript_id = Column(
        String(36), ForeignKey("transcripts.id"), nullable=False, unique=True
    )

    # Overall scores
    overall_score = Column(Float)
    situation_score = Column(Integer)
    pain_score = Column(Integer)
    impact_score = Column(Integer)
    critical_event_score = Column(Integer)
    expected_decision_score = Column(Integer)
    decision_criteria_score = Column(Integer)

    # Feedback sections
    executive_summary = Column(Text)
    key_strengths = Column(JSON, default=list)
    areas_for_improvement = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)
    coaching_tips = Column(JSON, default=list)

    # Comparison data
    team_average = Column(Float)
    percentile_rank = Column(Integer)

    # WbD methodology alignment
    wbd_alignment_score = Column(Integer)
    wbd_feedback = Column(Text)

    # User who received coaching
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


# Pydantic Schemas
class CoachingScoreSchema(TimestampedSchema):
    """Coaching score response schema."""

    report_id: str
    element: str
    score: int
    feedback: Optional[str] = None
    strengths: List[str] = []
    improvements: List[str] = []
    examples: List[str] = []


class CoachingReportSchema(TimestampedSchema):
    """Coaching report response schema."""

    transcript_id: str
    overall_score: Optional[float] = None
    situation_score: Optional[int] = None
    pain_score: Optional[int] = None
    impact_score: Optional[int] = None
    critical_event_score: Optional[int] = None
    expected_decision_score: Optional[int] = None
    decision_criteria_score: Optional[int] = None
    executive_summary: Optional[str] = None
    key_strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommended_actions: List[str] = []
    coaching_tips: List[str] = []
    team_average: Optional[float] = None
    percentile_rank: Optional[int] = None
    wbd_alignment_score: Optional[int] = None
    wbd_feedback: Optional[str] = None
    user_id: str
    organization_id: str
    scores: List[CoachingScoreSchema] = []


class CoachingReportExport(BaseModel):
    """Coaching report export data format."""

    id: str
    transcript_id: str
    transcript_title: str
    call_date: Optional[str] = None
    overall_score: Optional[float] = None
    situation_score: Optional[int] = None
    pain_score: Optional[int] = None
    impact_score: Optional[int] = None
    critical_event_score: Optional[int] = None
    expected_decision_score: Optional[int] = None
    decision_criteria_score: Optional[int] = None
    executive_summary: Optional[str] = None
    key_strengths: str = ""  # Comma-separated for CSV
    areas_for_improvement: str = ""
    recommended_actions: str = ""
    created_at: str
