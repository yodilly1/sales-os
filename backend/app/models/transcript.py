"""Transcript and SPICED analysis models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

class Call(Base, TimestampMixin, SoftDeleteMixin):
    """Call model."""

    __tablename__ = "calls"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual_upload", nullable=False)
    call_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    recording_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    participants: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    prospect_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("prospects.id"), nullable=True)
    company_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="calls")
    transcript = relationship("Transcript", back_populates="call", uselist=False)
    coaching_reports = relationship("CoachingReport", back_populates="call")
    prospect = relationship("Prospect", back_populates="calls")
    company = relationship("Company", back_populates="calls")
    spiced_analysis = relationship("SPICEDAnalysis", back_populates="call", uselist=False)


class Transcript(Base, TimestampMixin):
    """Call transcript model."""

    __tablename__ = "transcripts"

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transcription_service: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    call_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("calls.id"), nullable=False, unique=True)

    # Relationships
    call = relationship("Call", back_populates="transcript")


class SPICEDAnalysis(Base, TimestampMixin):
    """SPICED analysis extracted from transcript."""

    __tablename__ = "spiced_analyses"

    situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    critical_event: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    situation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pain_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impact_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    critical_event_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_decision_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decision_criteria_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    call_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    call_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_tasks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_quotes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gaps_identified: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_questions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    call_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("calls.id"), nullable=False, unique=True)

    # Relationships
    call = relationship("Call", back_populates="spiced_analysis")
