"""Zoom-related Pydantic models and schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, HttpUrl


class RecordingType(str, Enum):
    """Zoom recording file types."""

    SHARED_SCREEN_WITH_SPEAKER = "shared_screen_with_speaker_view"
    SHARED_SCREEN_WITH_GALLERY = "shared_screen_with_gallery_view"
    SHARED_SCREEN = "shared_screen"
    SPEAKER_VIEW = "speaker_view"
    GALLERY_VIEW = "gallery_view"
    AUDIO_ONLY = "audio_only"
    AUDIO_TRANSCRIPT = "audio_transcript"
    CHAT_FILE = "chat_file"
    TIMELINE = "timeline"
    CLOSED_CAPTION = "closed_caption"


class RecordingStatus(str, Enum):
    """Recording processing status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MeetingType(str, Enum):
    """Zoom meeting types."""

    INSTANT = "1"
    SCHEDULED = "2"
    RECURRING_NO_FIXED_TIME = "3"
    PMI = "4"
    RECURRING_FIXED_TIME = "8"


class ZoomOAuthTokens(BaseModel):
    """OAuth2 tokens from Zoom."""

    access_token: str
    token_type: str = "Bearer"
    refresh_token: str
    expires_in: int
    scope: str
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() >= self.expires_at


class ZoomAccount(BaseModel):
    """Zoom user account information."""

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    account_id: str
    timezone: Optional[str] = None
    created_at: Optional[datetime] = None
    tokens: Optional[ZoomOAuthTokens] = None


class ZoomRecordingFile(BaseModel):
    """Individual recording file from Zoom."""

    id: str
    meeting_id: str
    recording_start: datetime
    recording_end: datetime
    file_type: str
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    play_url: Optional[str] = None
    download_url: Optional[str] = None
    status: RecordingStatus = RecordingStatus.COMPLETED
    recording_type: Optional[RecordingType] = None


class ZoomRecording(BaseModel):
    """Zoom cloud recording with all associated files."""

    uuid: str
    id: int
    account_id: str
    host_id: str
    host_email: Optional[str] = None
    topic: str
    type: int = 2
    start_time: datetime
    duration: int  # in minutes
    timezone: Optional[str] = None
    total_size: Optional[int] = None
    recording_count: int = 0
    share_url: Optional[str] = None
    recording_files: List[ZoomRecordingFile] = Field(default_factory=list)
    password: Optional[str] = None


class ZoomRecordingListResponse(BaseModel):
    """Response from Zoom recordings list API."""

    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    page_size: int
    next_page_token: Optional[str] = None
    meetings: List[ZoomRecording] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ZoomMeeting(BaseModel):
    """Zoom meeting details."""

    uuid: str
    id: int
    host_id: str
    host_email: Optional[str] = None
    topic: str
    type: int
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None  # in minutes
    timezone: Optional[str] = None
    agenda: Optional[str] = None
    created_at: Optional[datetime] = None
    join_url: Optional[str] = None
    start_url: Optional[str] = None


class ZoomMeetingMetadata(BaseModel):
    """Extracted metadata from a Zoom meeting."""

    meeting_id: str
    meeting_uuid: str
    topic: str
    host_email: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int
    participants: List[str] = Field(default_factory=list)
    has_recording: bool = False
    has_transcript: bool = False
    recording_url: Optional[str] = None
    transcript_url: Optional[str] = None


class TranscriptLine(BaseModel):
    """A single line/segment from a transcript."""

    speaker: Optional[str] = None
    start_time: float  # seconds
    end_time: float  # seconds
    text: str
    confidence: Optional[float] = None


class ParsedTranscript(BaseModel):
    """Parsed transcript with structured data."""

    meeting_id: str
    meeting_topic: Optional[str] = None
    total_duration: float  # seconds
    lines: List[TranscriptLine] = Field(default_factory=list)
    speakers: List[str] = Field(default_factory=list)
    raw_text: str = ""
    format: str = "vtt"  # vtt, srt, or txt

    def get_full_text(self) -> str:
        """Get the full transcript as plain text."""
        if self.raw_text:
            return self.raw_text
        return "\n".join(
            f"{line.speaker or 'Unknown'}: {line.text}" for line in self.lines
        )


class ZoomTranscript(BaseModel):
    """Zoom transcript file content."""

    recording_id: str
    meeting_id: str
    download_url: str
    file_type: str = "VTT"
    content: Optional[str] = None
    parsed: Optional[ParsedTranscript] = None


# Webhook-related models


class WebhookEventType(str, Enum):
    """Zoom webhook event types."""

    RECORDING_COMPLETED = "recording.completed"
    RECORDING_TRANSCRIPT_COMPLETED = "recording.transcript_completed"
    RECORDING_STARTED = "recording.started"
    RECORDING_STOPPED = "recording.stopped"
    MEETING_STARTED = "meeting.started"
    MEETING_ENDED = "meeting.ended"


class ZoomWebhookPayload(BaseModel):
    """Base payload structure for Zoom webhooks."""

    account_id: str
    object: Dict[str, Any]


class ZoomWebhookEvent(BaseModel):
    """Zoom webhook event structure."""

    event: WebhookEventType
    event_ts: int  # Unix timestamp in milliseconds
    payload: ZoomWebhookPayload
    download_token: Optional[str] = None


class RecordingCompletedPayload(BaseModel):
    """Payload for recording.completed webhook event."""

    uuid: str
    id: int
    account_id: str
    host_id: str
    host_email: str
    topic: str
    type: int
    start_time: datetime
    duration: int
    timezone: Optional[str] = None
    share_url: Optional[str] = None
    total_size: Optional[int] = None
    recording_count: int = 0
    recording_files: List[ZoomRecordingFile] = Field(default_factory=list)
    password: Optional[str] = None
    recording_play_passcode: Optional[str] = None
    download_access_token: Optional[str] = None


# Request/Response models for API endpoints


class ZoomOAuthCallbackRequest(BaseModel):
    """OAuth callback request parameters."""

    code: str
    state: Optional[str] = None


class ZoomConnectResponse(BaseModel):
    """Response after connecting Zoom account."""

    success: bool
    account: Optional[ZoomAccount] = None
    message: Optional[str] = None


class ZoomRecordingsRequest(BaseModel):
    """Request parameters for listing recordings."""

    from_date: Optional[str] = None  # YYYY-MM-DD
    to_date: Optional[str] = None  # YYYY-MM-DD
    page_size: int = Field(default=30, ge=1, le=300)
    next_page_token: Optional[str] = None


class ZoomTranscriptRequest(BaseModel):
    """Request to download a specific transcript."""

    meeting_id: str
    recording_id: Optional[str] = None


class ProcessingStatus(str, Enum):
    """Status of transcript processing."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptProcessingResult(BaseModel):
    """Result of processing a transcript."""

    meeting_id: str
    status: ProcessingStatus
    transcript: Optional[ParsedTranscript] = None
    spiced_analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processed_at: Optional[datetime] = None
