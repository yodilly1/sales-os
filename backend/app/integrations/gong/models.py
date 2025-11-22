"""
Gong Integration Models

Pydantic models for Gong API requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GongAuthConfig(BaseModel):
    """Configuration for Gong API authentication."""

    access_key: str = Field(..., description="Gong API access key")
    access_key_secret: str = Field(..., description="Gong API access key secret")
    workspace_id: Optional[str] = Field(None, description="Optional workspace filter")


class GongParticipant(BaseModel):
    """Represents a participant in a Gong call."""

    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    speaker_id: Optional[str] = None
    user_id: Optional[str] = None
    affiliation: Optional[str] = None  # "internal" or "external"
    context: list[str] = Field(default_factory=list)


class GongTranscriptSegment(BaseModel):
    """A segment of a call transcript."""

    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    text: str = ""


class GongTranscript(BaseModel):
    """Full transcript for a Gong call."""

    call_id: str
    segments: list[dict] = Field(default_factory=list)

    def to_text(self) -> str:
        """Convert transcript segments to plain text."""
        lines = []
        for segment in self.segments:
            speaker = segment.get("speaker_name", "Unknown")
            text = segment.get("text", "")
            lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    def to_formatted_text(self) -> str:
        """Convert transcript to formatted text with timestamps."""
        lines = []
        for segment in self.segments:
            speaker = segment.get("speaker_name", "Unknown")
            text = segment.get("text", "")
            start = segment.get("start_time", 0)

            # Format timestamp as MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            lines.append(f"{timestamp} {speaker}: {text}")
        return "\n".join(lines)


class GongCall(BaseModel):
    """Represents a call from Gong."""

    id: str
    title: Optional[str] = None
    scheduled: Optional[datetime] = None
    started: Optional[datetime] = None
    duration: Optional[int] = None  # Duration in seconds
    direction: Optional[str] = None  # "Inbound", "Outbound", "Conference"
    system: Optional[str] = None  # Recording system (e.g., "Zoom", "Teams")
    scope: Optional[str] = None  # "Internal", "External", "Unknown"
    media: Optional[str] = None  # "Video", "Audio"
    language: Optional[str] = None
    workspace_id: Optional[str] = None
    sdr_disposition: Optional[str] = None
    client_unique_id: Optional[str] = None
    custom_data: Optional[str] = None
    url: Optional[str] = None

    # These are populated separately
    transcript: Optional[GongTranscript] = None
    participants: list[GongParticipant] = Field(default_factory=list)


class GongCallListResponse(BaseModel):
    """Response from Gong calls list endpoint."""

    calls: list[GongCall]
    cursor: Optional[str] = None
    total_records: Optional[int] = None


class GongCallInsights(BaseModel):
    """Gong's AI-generated insights for a call."""

    call_id: str
    topics: list[dict] = Field(default_factory=list)
    trackers: list[dict] = Field(default_factory=list)
    action_items: list[dict] = Field(default_factory=list)
    questions_asked: Optional[dict] = None
    talk_ratio: Optional[dict] = None
    interactivity: Optional[float] = None
    patience: Optional[float] = None


class GongSyncRequest(BaseModel):
    """Request to sync Gong calls."""

    from_datetime: Optional[datetime] = Field(
        None, description="Sync calls from this datetime"
    )
    to_datetime: Optional[datetime] = Field(
        None, description="Sync calls until this datetime"
    )
    include_transcripts: bool = Field(
        True, description="Include call transcripts"
    )
    include_insights: bool = Field(
        False, description="Include Gong AI insights"
    )
    workspace_id: Optional[str] = Field(
        None, description="Filter by workspace"
    )


class GongSyncResponse(BaseModel):
    """Response from a sync operation."""

    status: str  # "success", "partial", "error"
    calls_synced: int = 0
    calls_skipped: int = 0  # Already synced (deduplication)
    calls_failed: int = 0
    errors: list[str] = Field(default_factory=list)
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None
    next_cursor: Optional[str] = None


class GongWebhookPayload(BaseModel):
    """Payload from Gong webhooks."""

    event_type: str
    call_id: Optional[str] = None
    workspace_id: Optional[str] = None
    timestamp: datetime
    data: dict = Field(default_factory=dict)
