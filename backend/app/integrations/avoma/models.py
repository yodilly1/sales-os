"""
Avoma integration-specific models.

Re-exports models from the main models module for convenience,
and adds any integration-specific models.
"""

# Re-export all Avoma models from the main models module
from app.models.avoma import (
    AvomaAttendee,
    AvomaErrorResponse,
    AvomaMeetingMetadata,
    AvomaRecording,
    AvomaRecordingDB,
    AvomaRecordingListRequest,
    AvomaRecordingListResponse,
    AvomaRecordingStatus,
    AvomaSyncLog,
    AvomaTokenResponse,
    AvomaTranscript,
    AvomaUtterance,
    AvomaWebhookEvent,
    AvomaWebhookEventType,
)

__all__ = [
    "AvomaAttendee",
    "AvomaErrorResponse",
    "AvomaMeetingMetadata",
    "AvomaRecording",
    "AvomaRecordingDB",
    "AvomaRecordingListRequest",
    "AvomaRecordingListResponse",
    "AvomaRecordingStatus",
    "AvomaSyncLog",
    "AvomaTokenResponse",
    "AvomaTranscript",
    "AvomaUtterance",
    "AvomaWebhookEvent",
    "AvomaWebhookEventType",
]
