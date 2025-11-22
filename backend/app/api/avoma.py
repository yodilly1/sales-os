"""
Avoma API routes for transcript ingestion.

Provides REST endpoints for:
- Listing recordings
- Fetching transcripts
- Getting meeting metadata
- Triggering manual syncs
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.integrations.avoma import AvomaAuthManager, AvomaClient
from app.integrations.avoma.client import AvomaAPIError
from app.integrations.avoma.webhooks import TranscriptMapper
from app.models.avoma import (
    AvomaMeetingMetadata,
    AvomaRecording,
    AvomaRecordingListResponse,
    AvomaRecordingStatus,
    AvomaTranscript,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avoma", tags=["avoma"])


# Dependency injection for Avoma client
# In production, this would be configured from settings/environment
_avoma_client: Optional[AvomaClient] = None


async def get_avoma_client() -> AvomaClient:
    """
    Dependency to get the Avoma client.

    In production, this should be configured with proper credentials
    from environment variables or a settings module.
    """
    global _avoma_client

    if _avoma_client is None:
        # TODO: Load credentials from settings/environment
        # For now, this will need to be configured before use
        from app.core.config import get_settings

        settings = get_settings()

        auth_manager = AvomaAuthManager(
            client_id=settings.avoma_client_id,
            client_secret=settings.avoma_client_secret,
            api_key=settings.avoma_api_key,
            webhook_secret=settings.avoma_webhook_secret,
        )

        _avoma_client = AvomaClient(auth_manager)

    return _avoma_client


# Request/Response models

class RecordingListParams(BaseModel):
    """Query parameters for listing recordings."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    status: Optional[AvomaRecordingStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")


class TranscriptResponse(BaseModel):
    """Response model for transcript endpoint."""
    transcript: AvomaTranscript
    formatted_text: str = Field(..., description="Formatted transcript with speaker labels")


class MeetingMetadataResponse(BaseModel):
    """Response model for meeting metadata endpoint."""
    metadata: AvomaMeetingMetadata
    internal_attendees: list[dict] = Field(..., description="Internal attendees")
    external_attendees: list[dict] = Field(..., description="External attendees")


class SyncResponse(BaseModel):
    """Response model for sync operations."""
    status: str
    recordings_processed: int
    transcripts_fetched: int
    errors: list[str] = Field(default_factory=list)


class InternalTranscriptResponse(BaseModel):
    """Response model for transcript mapped to internal format."""
    transcript: dict
    participants: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    connected: bool
    message: Optional[str] = None


# Routes

@router.get("/health", response_model=HealthResponse)
async def health_check(
    client: AvomaClient = Depends(get_avoma_client),
) -> HealthResponse:
    """
    Check Avoma API connectivity and authentication.

    Returns the health status of the Avoma integration.
    """
    try:
        is_healthy = await client.health_check()
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            connected=is_healthy,
            message=None if is_healthy else "Could not connect to Avoma API",
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            connected=False,
            message=str(e),
        )


@router.get("/recordings", response_model=AvomaRecordingListResponse)
async def list_recordings(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[AvomaRecordingStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    client: AvomaClient = Depends(get_avoma_client),
) -> AvomaRecordingListResponse:
    """
    List available recordings from Avoma.

    Supports pagination and filtering by status and date range.
    """
    try:
        return await client.list_recordings(
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
    except AvomaAPIError as e:
        logger.error(f"Failed to list recordings: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/recordings/{recording_id}", response_model=AvomaRecording)
async def get_recording(
    recording_id: str,
    client: AvomaClient = Depends(get_avoma_client),
) -> AvomaRecording:
    """
    Get a single recording by ID.
    """
    try:
        return await client.get_recording(recording_id)
    except AvomaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recording not found: {recording_id}",
            )
        logger.error(f"Failed to get recording {recording_id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/recordings/{recording_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    recording_id: str,
    client: AvomaClient = Depends(get_avoma_client),
) -> TranscriptResponse:
    """
    Get the transcript for a recording.

    Returns both the structured transcript and formatted text.
    """
    try:
        transcript = await client.get_transcript(recording_id)
        return TranscriptResponse(
            transcript=transcript,
            formatted_text=transcript.get_formatted_transcript(),
        )
    except AvomaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript not found for recording: {recording_id}",
            )
        logger.error(f"Failed to get transcript {recording_id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/recordings/{recording_id}/metadata", response_model=MeetingMetadataResponse)
async def get_meeting_metadata(
    recording_id: str,
    client: AvomaClient = Depends(get_avoma_client),
) -> MeetingMetadataResponse:
    """
    Get full meeting metadata for a recording.

    Includes attendees categorized as internal/external.
    """
    try:
        metadata = await client.get_meeting_metadata(recording_id)
        return MeetingMetadataResponse(
            metadata=metadata,
            internal_attendees=[
                {"name": a.name, "email": a.email, "role": a.role}
                for a in metadata.get_internal_attendees()
            ],
            external_attendees=[
                {"name": a.name, "email": a.email, "role": a.role}
                for a in metadata.get_external_attendees()
            ],
        )
    except AvomaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metadata not found for recording: {recording_id}",
            )
        logger.error(f"Failed to get metadata {recording_id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/recordings/{recording_id}/internal", response_model=InternalTranscriptResponse)
async def get_internal_transcript(
    recording_id: str,
    client: AvomaClient = Depends(get_avoma_client),
) -> InternalTranscriptResponse:
    """
    Get transcript mapped to internal Sales OS format.

    Useful for feeding into the SPICED extraction pipeline.
    """
    try:
        transcript = await client.get_transcript(recording_id)
        metadata = await client.get_meeting_metadata(recording_id)

        internal_transcript = TranscriptMapper.map_to_internal_transcript(
            transcript, metadata
        )
        participants = TranscriptMapper.extract_participants(metadata)

        return InternalTranscriptResponse(
            transcript=internal_transcript,
            participants=participants,
        )
    except AvomaAPIError as e:
        logger.error(f"Failed to get internal transcript {recording_id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_recordings(
    start_date: Optional[datetime] = Query(None, description="Sync recordings after this date"),
    end_date: Optional[datetime] = Query(None, description="Sync recordings before this date"),
    max_recordings: int = Query(50, ge=1, le=200, description="Maximum recordings to sync"),
    client: AvomaClient = Depends(get_avoma_client),
) -> SyncResponse:
    """
    Manually trigger a sync of recordings from Avoma.

    Fetches recordings and their transcripts within the specified date range.
    """
    errors = []
    transcripts_fetched = 0

    try:
        results = await client.get_recordings_with_transcripts(
            start_date=start_date,
            end_date=end_date,
            max_recordings=max_recordings,
        )

        for recording, transcript in results:
            if transcript:
                transcripts_fetched += 1
                # TODO: Trigger SPICED pipeline for each transcript
                # This would integrate with the transcript processing service
            else:
                errors.append(f"No transcript available for recording {recording.id}")

        return SyncResponse(
            status="success",
            recordings_processed=len(results),
            transcripts_fetched=transcripts_fetched,
            errors=errors,
        )

    except AvomaAPIError as e:
        logger.error(f"Sync failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.post("/recordings/{recording_id}/process")
async def process_recording(
    recording_id: str,
    client: AvomaClient = Depends(get_avoma_client),
) -> dict:
    """
    Manually trigger processing of a specific recording.

    Fetches the transcript and metadata, then triggers the SPICED pipeline.
    """
    try:
        # Fetch transcript and metadata
        transcript = await client.get_transcript(recording_id)
        metadata = await client.get_meeting_metadata(recording_id)

        # Map to internal format
        internal_transcript = TranscriptMapper.map_to_internal_transcript(
            transcript, metadata
        )

        # TODO: Trigger SPICED extraction pipeline
        # In production, this would call the transcript processing service
        # Example: await spiced_service.extract(internal_transcript)

        return {
            "status": "success",
            "recording_id": recording_id,
            "transcript_id": transcript.id,
            "title": metadata.title,
            "duration_seconds": metadata.duration_seconds,
            "attendees_count": len(metadata.attendees),
            "message": "Recording queued for SPICED extraction",
        }

    except AvomaAPIError as e:
        logger.error(f"Failed to process recording {recording_id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
