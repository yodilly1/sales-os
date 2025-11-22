"""
Pydantic models for Avoma API integration.

These models define the data structures for:
- Recording metadata and lists
- Transcripts and utterances
- Meeting metadata and attendees
- Webhook events
- Authentication tokens
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AvomaRecordingStatus(str, Enum):
    """Status of an Avoma recording."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AvomaAttendee(BaseModel):
    """Represents an attendee in an Avoma meeting."""
    id: str = Field(..., description="Unique identifier for the attendee")
    name: str = Field(..., description="Full name of the attendee")
    email: Optional[str] = Field(None, description="Email address of the attendee")
    role: Optional[str] = Field(None, description="Role in the meeting (host, participant, etc.)")
    is_internal: bool = Field(False, description="Whether the attendee is internal to the organization")
    speaker_id: Optional[str] = Field(None, description="Speaker ID for transcript attribution")


class AvomaUtterance(BaseModel):
    """Represents a single utterance in a transcript."""
    id: str = Field(..., description="Unique identifier for the utterance")
    speaker_id: str = Field(..., description="ID of the speaker")
    speaker_name: Optional[str] = Field(None, description="Name of the speaker")
    text: str = Field(..., description="The transcribed text")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    confidence: Optional[float] = Field(None, description="Transcription confidence score")


class AvomaTranscript(BaseModel):
    """Represents a full transcript from Avoma."""
    id: str = Field(..., description="Unique identifier for the transcript")
    recording_id: str = Field(..., description="Associated recording ID")
    utterances: list[AvomaUtterance] = Field(default_factory=list, description="List of utterances")
    full_text: Optional[str] = Field(None, description="Full transcript as plain text")
    language: str = Field("en", description="Language code of the transcript")
    created_at: datetime = Field(..., description="Timestamp when transcript was created")

    def get_formatted_transcript(self) -> str:
        """Get the transcript formatted with speaker labels."""
        if self.full_text:
            return self.full_text

        lines = []
        for utterance in self.utterances:
            speaker = utterance.speaker_name or f"Speaker {utterance.speaker_id}"
            lines.append(f"{speaker}: {utterance.text}")
        return "\n".join(lines)


class AvomaRecording(BaseModel):
    """Represents an Avoma recording with basic metadata."""
    id: str = Field(..., description="Unique identifier for the recording")
    title: Optional[str] = Field(None, description="Title of the meeting")
    duration_seconds: int = Field(..., description="Duration of the recording in seconds")
    status: AvomaRecordingStatus = Field(..., description="Processing status of the recording")
    recording_url: Optional[str] = Field(None, description="URL to access the recording")
    created_at: datetime = Field(..., description="Timestamp when recording was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when recording was last updated")
    has_transcript: bool = Field(False, description="Whether transcript is available")
    attendee_count: int = Field(0, description="Number of attendees")


class AvomaMeetingMetadata(BaseModel):
    """Full metadata for an Avoma meeting/recording."""
    id: str = Field(..., description="Unique identifier for the meeting")
    recording_id: str = Field(..., description="Associated recording ID")
    title: str = Field(..., description="Title of the meeting")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_type: Optional[str] = Field(None, description="Type of meeting (sales call, demo, etc.)")
    duration_seconds: int = Field(..., description="Duration in seconds")
    scheduled_start: Optional[datetime] = Field(None, description="Scheduled start time")
    actual_start: datetime = Field(..., description="Actual start time")
    actual_end: datetime = Field(..., description="Actual end time")
    attendees: list[AvomaAttendee] = Field(default_factory=list, description="List of meeting attendees")
    host: Optional[AvomaAttendee] = Field(None, description="Meeting host")
    calendar_event_id: Optional[str] = Field(None, description="Associated calendar event ID")
    crm_opportunity_id: Optional[str] = Field(None, description="Associated CRM opportunity ID")
    crm_contact_ids: list[str] = Field(default_factory=list, description="Associated CRM contact IDs")
    tags: list[str] = Field(default_factory=list, description="Meeting tags")
    notes: Optional[str] = Field(None, description="Meeting notes")
    action_items: list[str] = Field(default_factory=list, description="Extracted action items")
    topics_discussed: list[str] = Field(default_factory=list, description="Main topics discussed")
    sentiment_score: Optional[float] = Field(None, description="Overall sentiment score")
    created_at: datetime = Field(..., description="Timestamp when meeting record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when meeting record was last updated")

    def get_external_attendees(self) -> list[AvomaAttendee]:
        """Get list of external attendees only."""
        return [a for a in self.attendees if not a.is_internal]

    def get_internal_attendees(self) -> list[AvomaAttendee]:
        """Get list of internal attendees only."""
        return [a for a in self.attendees if a.is_internal]


class AvomaWebhookEventType(str, Enum):
    """Types of webhook events from Avoma."""
    RECORDING_COMPLETED = "recording.completed"
    RECORDING_FAILED = "recording.failed"
    TRANSCRIPT_READY = "transcript.ready"
    MEETING_ENDED = "meeting.ended"
    NOTES_UPDATED = "notes.updated"


class AvomaWebhookEvent(BaseModel):
    """Represents a webhook event from Avoma."""
    event_id: str = Field(..., description="Unique identifier for the webhook event")
    event_type: AvomaWebhookEventType = Field(..., description="Type of the webhook event")
    recording_id: str = Field(..., description="Associated recording ID")
    meeting_id: Optional[str] = Field(None, description="Associated meeting ID")
    timestamp: datetime = Field(..., description="Timestamp of the event")
    organization_id: str = Field(..., description="Avoma organization ID")
    payload: dict = Field(default_factory=dict, description="Additional event payload data")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class AvomaRecordingListResponse(BaseModel):
    """Response model for listing recordings."""
    recordings: list[AvomaRecording] = Field(default_factory=list, description="List of recordings")
    total_count: int = Field(0, description="Total number of recordings")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")
    has_more: bool = Field(False, description="Whether there are more pages")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")


class AvomaTokenResponse(BaseModel):
    """Response model for OAuth token refresh."""
    access_token: str = Field(..., description="New access token")
    token_type: str = Field("Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="New refresh token if rotated")
    scope: Optional[str] = Field(None, description="Token scopes")


class AvomaErrorResponse(BaseModel):
    """Error response from Avoma API."""
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")


# Request models for API calls

class AvomaRecordingListRequest(BaseModel):
    """Request model for listing recordings."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    status: Optional[AvomaRecordingStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    cursor: Optional[str] = Field(None, description="Pagination cursor")


# Internal models for database storage

class AvomaRecordingDB(BaseModel):
    """Database model for storing Avoma recording references."""
    id: str = Field(..., description="Internal database ID")
    avoma_recording_id: str = Field(..., description="Avoma recording ID")
    organization_id: str = Field(..., description="Internal organization ID")
    transcript_id: Optional[str] = Field(None, description="Internal transcript ID after processing")
    status: AvomaRecordingStatus = Field(..., description="Sync status")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    metadata: Optional[dict] = Field(None, description="Cached metadata")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")


class AvomaSyncLog(BaseModel):
    """Log entry for Avoma sync operations."""
    id: str = Field(..., description="Log entry ID")
    recording_id: str = Field(..., description="Avoma recording ID")
    operation: str = Field(..., description="Operation type (fetch_transcript, sync_metadata, etc.)")
    status: str = Field(..., description="Operation status (success, failed, pending)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Operation duration in milliseconds")
    created_at: datetime = Field(..., description="Log entry timestamp")
