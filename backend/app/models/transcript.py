"""Transcript and SPICED analysis models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseDBModel, BaseModel, TimestampedSchema


class TranscriptSource(str, Enum):
    """Source of the transcript."""

    AVOMA = "avoma"
    ZOOM = "zoom"
    TEAMS = "teams"
    GONG = "gong"
    MANUAL = "manual"


class CallSource(str, Enum):
    """Source of the call."""
    MANUAL_UPLOAD = "manual_upload"
    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    DIALER = "dialer"


class CallType(str, Enum):
    """Type of call."""
    DISCOVERY = "discovery"
    DEMO = "demo"
    NEGOTIATION = "negotiation"
    CHECK_IN = "check_in"
    SUPPORT = "support"
    OTHER = "other"


class CallStatus(str, Enum):
    """Status of the call."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class Call(BaseDBModel):
    """Call model."""

    __tablename__ = "calls"

    title = Column(String(500), nullable=False)
    source = Column(SQLEnum(CallSource), default=CallSource.MANUAL_UPLOAD)
    call_type = Column(SQLEnum(CallType), nullable=True)
    status = Column(SQLEnum(CallStatus), default=CallStatus.COMPLETED)
    
    scheduled_at = Column(String(50))
    started_at = Column(String(50))
    ended_at = Column(String(50))
    duration_seconds = Column(Integer)
    
    recording_url = Column(String(500))
    external_id = Column(String(255))
    
    participants = Column(JSON, default=list)
    
    # Relationships
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    prospect_id = Column(String(36), ForeignKey("prospects.id"))
    company_id = Column(String(36), ForeignKey("companies.id"))
    
    transcript = relationship("Transcript", backref="call", uselist=False)
    coaching_reports = relationship("CoachingReport", back_populates="call")
    prospect = relationship("Prospect", back_populates="calls")
    company = relationship("Company", back_populates="calls")


class Transcript(BaseDBModel):
    """Call transcript model."""

    __tablename__ = "transcripts"

    title = Column(String(500), nullable=False)
    source = Column(SQLEnum(TranscriptSource), default=TranscriptSource.MANUAL)
    source_id = Column(String(255))  # External ID from source system
    raw_text = Column(Text, nullable=False)
    duration_seconds = Column(Integer)
    call_date = Column(String(50))  # ISO date string
    participants = Column(JSON, default=list)  # List of participant names/emails
    meta_data = Column(JSON, default=dict)

    # Relationships
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    prospect_id = Column(String(36), ForeignKey("prospects.id"))


class SPICEDAnalysis(BaseDBModel):
    """SPICED analysis extracted from transcript."""

    __tablename__ = "spiced_analyses"

    transcript_id = Column(
        String(36), ForeignKey("transcripts.id"), nullable=False, unique=True
    )

    # SPICED Fields
    situation = Column(Text)  # Current state/context
    situation_confidence = Column(Integer, default=0)  # 0-100

    pain = Column(Text)  # Problems/challenges identified
    pain_confidence = Column(Integer, default=0)

    impact = Column(Text)  # Business consequences
    impact_confidence = Column(Integer, default=0)

    critical_event = Column(Text)  # Timeline/urgency drivers
    critical_event_confidence = Column(Integer, default=0)

    expected_decision = Column(Text)  # Decision process
    expected_decision_confidence = Column(Integer, default=0)

    decision_criteria = Column(Text)  # Evaluation criteria
    decision_criteria_confidence = Column(Integer, default=0)

    # Summary and suggestions
    summary = Column(Text)
    key_quotes = Column(JSON, default=list)  # List of notable quotes
    follow_up_tasks = Column(JSON, default=list)  # Suggested next steps
    objections = Column(JSON, default=list)  # Objections raised

    # Analysis metadata
    model_version = Column(String(50))
    analysis_date = Column(String(50))
