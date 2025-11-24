"""Call and Transcript Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.models.transcript import (
    CallSource,
    CallStatus,
    CallType,
    TranscriptFormat,
    TaskPriority,
)
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


# ==================== Transcript Components ====================

class TranscriptSpeaker(BaseSchema):
    """A speaker in the transcript."""
    id: Optional[str] = Field(default=None, description="Unique speaker identifier")
    name: str = Field(..., description="Speaker name")
    role: Optional[str] = Field(default=None, description="Speaker role")
    email: Optional[str] = Field(default=None, description="Speaker email")
    company: Optional[str] = Field(default=None, description="Speaker company")


class TranscriptTurn(BaseSchema):
    """A single turn/utterance in the transcript."""
    speaker: str = Field(..., description="Name of the speaker")
    text: str = Field(..., description="What was said")
    timestamp: Optional[str] = Field(default=None, description="Timestamp string")
    start_time: Optional[float] = Field(default=None, description="Start time in seconds")
    end_time: Optional[float] = Field(default=None, description="End time in seconds")


class FollowUpTask(BaseSchema):
    """A recommended follow-up task."""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    due_date_suggestion: Optional[str] = Field(default=None, description="Suggested due date")
    assignee_suggestion: Optional[str] = Field(default=None, description="Suggested assignee")
    related_spiced_component: Optional[str] = Field(default=None, description="Related SPICED component")
    crm_task_type: Optional[str] = Field(default=None, description="Suggested CRM task type")


class CallNote(BaseSchema):
    """Formatted call notes."""
    summary: str = Field(..., description="Executive summary")
    attendees: List[str] = Field(default_factory=list, description="List of attendees")
    key_discussion_points: List[str] = Field(default_factory=list, description="Main topics")
    customer_sentiment: Optional[str] = Field(default=None, description="Sentiment assessment")
    next_steps_discussed: List[str] = Field(default_factory=list, description="Next steps")
    objections_raised: List[str] = Field(default_factory=list, description="Objections raised")
    questions_asked: List[str] = Field(default_factory=list, description="Questions asked")
    commitments_made: List[str] = Field(default_factory=list, description="Commitments made")
    formatted_note: str = Field(..., description="Full formatted call note")


# ==================== Transcript Schemas ====================


class TranscriptBase(BaseSchema):
    """Base transcript schema."""

    raw_text: str = Field(..., min_length=1)
    language: str = Field("en", max_length=10)


class TranscriptCreate(TranscriptBase):
    """Schema for creating a transcript."""

    call_id: str
    structured_text: Optional[Dict[str, Any]] = None
    transcription_service: Optional[str] = None


class TranscriptResponse(TranscriptBase, IDSchema, TimestampSchema):
    """Schema for transcript response."""

    call_id: str
    structured_text: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = None
    confidence_score: Optional[float] = None
    transcription_service: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    # Expanded fields from HEAD model
    format: TranscriptFormat = Field(default=TranscriptFormat.GENERIC)
    turns: List[TranscriptTurn] = Field(default_factory=list)
    speakers: List[TranscriptSpeaker] = Field(default_factory=list)
    duration_minutes: Optional[int] = None
    call_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptParseRequest(BaseSchema):
    """Request to parse a transcript."""
    transcript_text: str = Field(..., min_length=50)
    format: TranscriptFormat = Field(default=TranscriptFormat.GENERIC)
    call_title: Optional[str] = None
    call_date: Optional[datetime] = None
    company_name: Optional[str] = None
    sales_rep_name: Optional[str] = None
    generate_tasks: bool = True
    generate_call_note: bool = True


class TranscriptParseResponse(BaseSchema):
    """Response from transcript parsing."""
    transcript: TranscriptResponse
    spiced_analysis: Any = Field(..., description="SPICED Analysis") # Typed as Any to avoid circular import
    call_note: Optional[CallNote] = None
    follow_up_tasks: List[FollowUpTask] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)


# ==================== Call Schemas ====================


class CallParticipant(BaseSchema):
    """Schema for call participant."""

    name: str
    email: Optional[str] = None
    role: Optional[str] = None  # host, participant, etc.
    is_internal: bool = False


class CallBase(BaseSchema):
    """Base call schema."""

    title: str = Field(..., min_length=1, max_length=500)
    source: CallSource = CallSource.MANUAL_UPLOAD
    call_type: Optional[CallType] = None


class CallCreate(CallBase):
    """Schema for creating a call."""

    user_id: str
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    external_id: Optional[str] = None
    participants: Optional[List[CallParticipant]] = None

    @field_validator("participants", mode="before")
    @classmethod
    def validate_participants(cls, v: Any) -> Any:
        """Validate and convert participants."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


class CallUpdate(BaseSchema):
    """Schema for updating a call."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    call_type: Optional[CallType] = None
    status: Optional[CallStatus] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    participants: Optional[List[CallParticipant]] = None


class CallResponse(CallBase, IDSchema, TimestampSchema):
    """Schema for call response."""

    status: CallStatus
    user_id: str
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    external_id: Optional[str] = None
    participants: Optional[List[CallParticipant]] = None


class CallWithTranscript(CallResponse):
    """Call response with transcript included."""

    transcript: Optional[TranscriptResponse] = None


class CallUploadRequest(BaseSchema):
    """Schema for uploading a call with transcript."""

    title: str = Field(..., min_length=1, max_length=500)
    source: CallSource = CallSource.MANUAL_UPLOAD
    call_type: Optional[CallType] = None
    transcript_text: str = Field(..., min_length=1)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    prospect_id: Optional[str] = None
    company_id: Optional[str] = None
    participants: Optional[List[CallParticipant]] = None
