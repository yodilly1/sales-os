"""Call and Transcript Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.models.transcript import CallSource, CallStatus, CallType
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


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
