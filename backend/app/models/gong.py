"""
Gong Data Models

Pydantic models for Gong integration data stored in the database.
These models represent the internal representation of Gong data
after it has been synced and processed.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class IntegrationStatus(str, Enum):
    """Status of an integration connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class SyncStatus(str, Enum):
    """Status of a sync operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class GongIntegrationConfig(BaseModel):
    """
    Stored configuration for a Gong integration.

    This is stored per-organization/user to manage their Gong connection.
    """

    id: Optional[str] = None
    organization_id: str
    status: IntegrationStatus = IntegrationStatus.PENDING
    access_key_encrypted: str  # Encrypted at rest
    access_key_secret_encrypted: str  # Encrypted at rest
    workspace_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class GongSyncedCall(BaseModel):
    """
    A Gong call that has been synced to our system.

    This represents the internal storage format after processing.
    """

    id: Optional[str] = None
    organization_id: str
    gong_call_id: str
    gong_hash: str  # For deduplication
    title: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    direction: Optional[str] = None
    platform: Optional[str] = None  # "Zoom", "Teams", etc.
    scope: Optional[str] = None  # "Internal", "External"
    media_type: Optional[str] = None  # "Video", "Audio"
    language: Optional[str] = None
    external_url: Optional[str] = None
    workspace_id: Optional[str] = None

    # Processing status
    transcript_synced: bool = False
    participants_synced: bool = False
    insights_synced: bool = False
    spiced_processed: bool = False  # Whether SPICED analysis has been run

    # Metadata
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class GongSyncedTranscript(BaseModel):
    """
    A synced transcript from Gong.
    """

    id: Optional[str] = None
    call_id: str  # Reference to GongSyncedCall
    gong_call_id: str
    raw_text: str
    formatted_text: str
    segments: list[dict] = Field(default_factory=list)
    segment_count: int = 0
    word_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class GongSyncedParticipant(BaseModel):
    """
    A participant from a Gong call.
    """

    id: Optional[str] = None
    call_id: str  # Reference to GongSyncedCall
    gong_participant_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    is_internal: bool = False
    speaker_id: Optional[str] = None
    talk_time_percentage: Optional[float] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class GongSyncLog(BaseModel):
    """
    Log entry for a Gong sync operation.
    """

    id: Optional[str] = None
    organization_id: str
    status: SyncStatus
    sync_type: str  # "scheduled", "manual", "historical"
    started_at: datetime
    completed_at: Optional[datetime] = None
    calls_found: int = 0
    calls_synced: int = 0
    calls_skipped: int = 0
    calls_failed: int = 0
    errors: list[str] = Field(default_factory=list)
    filter_from: Optional[datetime] = None
    filter_to: Optional[datetime] = None
    cursor: Optional[str] = None  # For resumable sync

    class Config:
        from_attributes = True


# API Request/Response Models

class GongConnectRequest(BaseModel):
    """Request to connect Gong integration."""

    access_key: str
    access_key_secret: str
    workspace_id: Optional[str] = None


class GongConnectResponse(BaseModel):
    """Response after connecting Gong."""

    status: IntegrationStatus
    message: str
    connected_at: Optional[datetime] = None


class GongStatusResponse(BaseModel):
    """Response for Gong integration status check."""

    status: IntegrationStatus
    workspace_id: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    total_calls_synced: int = 0
    last_error: Optional[str] = None


class GongCallListRequest(BaseModel):
    """Request to list synced Gong calls."""

    page: int = 1
    page_size: int = 20
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None
    include_transcript: bool = False


class GongCallResponse(BaseModel):
    """Response for a single Gong call."""

    id: str
    gong_call_id: str
    title: Optional[str]
    started_at: Optional[datetime]
    duration_seconds: Optional[int]
    duration_formatted: str
    platform: Optional[str]
    scope: Optional[str]
    participants: list[GongSyncedParticipant] = []
    has_transcript: bool
    has_spiced_analysis: bool
    external_url: Optional[str]


class GongCallListResponse(BaseModel):
    """Response for list of Gong calls."""

    calls: list[GongCallResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class GongSyncTriggerRequest(BaseModel):
    """Request to trigger a sync operation."""

    sync_type: str = "incremental"  # "incremental", "full", "historical"
    from_datetime: Optional[datetime] = None
    to_datetime: Optional[datetime] = None
    include_transcripts: bool = True
    include_insights: bool = False


class GongSyncStatusResponse(BaseModel):
    """Response for sync status check."""

    is_syncing: bool
    last_sync: Optional[GongSyncLog] = None
    next_scheduled_sync: Optional[datetime] = None
