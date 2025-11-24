"""Transcript and SPICED analysis models.

Contains both SQLAlchemy ORM models for database persistence
and Pydantic models for API request/response handling.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin, SoftDeleteMixin


# ==================== Enums ====================

class TranscriptFormat(str, Enum):
    """Supported transcript source formats."""
    ZOOM = "zoom"
    TEAMS = "teams"
    AVOMA = "avoma"
    GONG = "gong"
    CHORUS = "chorus"
    GENERIC = "generic"


class TaskPriority(str, Enum):
    """Priority levels for follow-up tasks."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CallSource(str, Enum):
    """Source of the call recording."""
    ZOOM = "zoom"
    TEAMS = "teams"
    AVOMA = "avoma"
    GONG = "gong"
    MANUAL_UPLOAD = "manual_upload"


class CallStatus(str, Enum):
    """Status of call processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CallType(str, Enum):
    """Type of sales call."""
    DISCOVERY = "discovery"
    DEMO = "demo"
    FOLLOW_UP = "follow_up"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    OTHER = "other"


# ==================== Pydantic Models (for API/Service layer) ====================

class TranscriptSpeaker(BaseModel):
    """A speaker in the transcript (Pydantic model)."""
    id: Optional[str] = Field(default=None, description="Unique speaker identifier")
    name: str = Field(..., description="Speaker name")
    role: Optional[str] = Field(default=None, description="Speaker role (sales_rep, prospect, unknown)")
    email: Optional[str] = Field(default=None, description="Speaker email")
    company: Optional[str] = Field(default=None, description="Speaker company")


class TranscriptTurn(BaseModel):
    """A single turn/utterance in the transcript (Pydantic model)."""
    speaker: str = Field(..., description="Name of the speaker")
    text: str = Field(..., description="What was said")
    timestamp: Optional[str] = Field(default=None, description="Timestamp string")
    start_time: Optional[float] = Field(default=None, description="Start time in seconds")
    end_time: Optional[float] = Field(default=None, description="End time in seconds")


class TranscriptData(BaseModel):
    """Parsed transcript (Pydantic model for service layer)."""
    id: str = Field(..., description="Unique transcript identifier")
    title: Optional[str] = Field(default=None, description="Call title")
    format: TranscriptFormat = Field(default=TranscriptFormat.GENERIC, description="Transcript format")
    raw_text: str = Field(..., description="Original raw transcript text")
    turns: List[TranscriptTurn] = Field(default_factory=list, description="Parsed conversation turns")
    speakers: List[TranscriptSpeaker] = Field(default_factory=list, description="Identified speakers")
    duration_minutes: Optional[int] = Field(default=None, description="Call duration in minutes")
    call_date: Optional[datetime] = Field(default=None, description="Date of the call")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When parsed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FollowUpTask(BaseModel):
    """A recommended follow-up task (Pydantic model)."""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    due_date_suggestion: Optional[str] = Field(default=None, description="Suggested due date")
    assignee_suggestion: Optional[str] = Field(default=None, description="Suggested assignee")
    related_spiced_component: Optional[str] = Field(default=None, description="Related SPICED component")
    crm_task_type: Optional[str] = Field(default=None, description="Suggested CRM task type")


class CallNote(BaseModel):
    """Formatted call notes (Pydantic model)."""
    summary: str = Field(..., description="Executive summary")
    attendees: List[str] = Field(default_factory=list, description="List of attendees")
    key_discussion_points: List[str] = Field(default_factory=list, description="Main topics")
    customer_sentiment: Optional[str] = Field(default=None, description="Sentiment assessment")
    next_steps_discussed: List[str] = Field(default_factory=list, description="Next steps")
    objections_raised: List[str] = Field(default_factory=list, description="Objections raised")
    questions_asked: List[str] = Field(default_factory=list, description="Questions asked")
    commitments_made: List[str] = Field(default_factory=list, description="Commitments made")
    formatted_note: str = Field(..., description="Full formatted call note")


class TranscriptParseRequest(BaseModel):
    """Request to parse a transcript."""
    transcript_text: str = Field(..., min_length=50, description="Raw transcript text")
    format: TranscriptFormat = Field(default=TranscriptFormat.GENERIC, description="Transcript format hint")
    call_title: Optional[str] = Field(default=None, description="Title for the call")
    call_date: Optional[datetime] = Field(default=None, description="Date of the call")
    company_name: Optional[str] = Field(default=None, description="Company name for context")
    sales_rep_name: Optional[str] = Field(default=None, description="Sales rep name for speaker identification")
    generate_tasks: bool = Field(default=True, description="Generate follow-up tasks")
    generate_call_note: bool = Field(default=True, description="Generate call notes")


class TranscriptParseResponse(BaseModel):
    """Response from transcript parsing."""
    transcript: TranscriptData
    spiced_analysis: Any = Field(..., description="SPICED Analysis")
    call_note: Optional[CallNote] = Field(default=None, description="Generated call notes")
    follow_up_tasks: List[FollowUpTask] = Field(default_factory=list, description="Recommended tasks")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during processing")


# ==================== SQLAlchemy ORM Models (for database) ====================

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
