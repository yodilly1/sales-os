"""Webhook handlers for external service events."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Header

from app.core.config import settings
from app.integrations.zoom import ZoomClient
from app.integrations.zoom.exceptions import ZoomWebhookValidationError
from app.models.zoom import (
    WebhookEventType,
    ZoomWebhookEvent,
    RecordingCompletedPayload,
    ZoomRecordingFile,
    TranscriptProcessingResult,
    ProcessingStatus,
)
from app.services.transcript.pipeline import TranscriptProcessingPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# Store processing results (replace with database in production)
_processing_results: Dict[str, TranscriptProcessingResult] = {}


# ==================== Zoom Webhooks ====================


@router.post("/zoom")
async def handle_zoom_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_zm_signature: Optional[str] = Header(default=None, alias="x-zm-signature"),
    x_zm_request_timestamp: Optional[str] = Header(
        default=None, alias="x-zm-request-timestamp"
    ),
):
    """Handle incoming Zoom webhook events.

    Supports:
    - URL validation (for Zoom webhook setup)
    - recording.completed events
    - recording.transcript_completed events

    Events trigger async processing pipeline for SPICED analysis.
    """
    body = await request.body()
    payload = await request.json()

    # Handle URL validation challenge (used when setting up webhooks in Zoom)
    if payload.get("event") == "endpoint.url_validation":
        plain_token = payload.get("payload", {}).get("plainToken")
        if not plain_token:
            raise HTTPException(status_code=400, detail="Missing plainToken")

        response = ZoomClient.generate_webhook_response(plain_token)
        return response

    # Validate webhook signature for actual events
    if settings.zoom_webhook_secret and x_zm_signature and x_zm_request_timestamp:
        is_valid = ZoomClient.validate_webhook_signature(
            payload=body,
            signature=x_zm_signature,
            timestamp=x_zm_request_timestamp,
        )
        if not is_valid:
            logger.warning("Invalid Zoom webhook signature")
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    event_type = payload.get("event")
    logger.info(f"Received Zoom webhook event: {event_type}")

    # Handle recording completed events
    if event_type == WebhookEventType.RECORDING_COMPLETED.value:
        await handle_recording_completed(payload, background_tasks)
        return {"status": "accepted", "event": event_type}

    # Handle transcript completed events
    if event_type == WebhookEventType.RECORDING_TRANSCRIPT_COMPLETED.value:
        await handle_transcript_completed(payload, background_tasks)
        return {"status": "accepted", "event": event_type}

    # Handle meeting ended events (optional - for tracking)
    if event_type == WebhookEventType.MEETING_ENDED.value:
        await handle_meeting_ended(payload)
        return {"status": "accepted", "event": event_type}

    # Accept but don't process other events
    return {"status": "ignored", "event": event_type}


async def handle_recording_completed(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """Handle recording.completed webhook event.

    When a recording completes, check if it has a transcript and trigger processing.
    """
    try:
        event_data = payload.get("payload", {}).get("object", {})
        meeting_id = str(event_data.get("id", ""))
        meeting_uuid = event_data.get("uuid", "")
        topic = event_data.get("topic", "Unknown Meeting")
        host_email = event_data.get("host_email", "")
        download_token = payload.get("download_token")

        logger.info(
            f"Recording completed for meeting: {topic} (ID: {meeting_id})"
        )

        # Check for transcript file in recording files
        recording_files = event_data.get("recording_files", [])
        transcript_file = None
        transcript_url = None

        for rf in recording_files:
            file_type = rf.get("file_type", "")
            if file_type in ("TRANSCRIPT", "VTT", "CC"):
                transcript_file = rf
                transcript_url = rf.get("download_url")
                break

        if transcript_file and transcript_url:
            logger.info(f"Transcript available for meeting {meeting_id}, queuing processing")

            # Initialize processing result
            _processing_results[meeting_id] = TranscriptProcessingResult(
                meeting_id=meeting_id,
                status=ProcessingStatus.PENDING,
            )

            # Queue background processing
            background_tasks.add_task(
                process_recording_transcript,
                meeting_id=meeting_id,
                meeting_uuid=meeting_uuid,
                topic=topic,
                host_email=host_email,
                transcript_url=transcript_url,
                file_type=transcript_file.get("file_type", "VTT"),
                download_token=download_token,
            )
        else:
            logger.info(
                f"No transcript file in recording for meeting {meeting_id}, "
                "waiting for transcript_completed event"
            )

    except Exception as e:
        logger.error(f"Error handling recording_completed: {e}")


async def handle_transcript_completed(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """Handle recording.transcript_completed webhook event.

    This event fires when a transcript becomes available for a recording.
    """
    try:
        event_data = payload.get("payload", {}).get("object", {})
        meeting_id = str(event_data.get("id", ""))
        meeting_uuid = event_data.get("uuid", "")
        topic = event_data.get("topic", "Unknown Meeting")
        host_email = event_data.get("host_email", "")
        download_token = payload.get("download_token")

        logger.info(f"Transcript completed for meeting: {topic} (ID: {meeting_id})")

        # Get transcript URL from recording files
        recording_files = event_data.get("recording_files", [])
        transcript_url = None
        file_type = "VTT"

        for rf in recording_files:
            rf_type = rf.get("file_type", "")
            if rf_type in ("TRANSCRIPT", "VTT", "CC"):
                transcript_url = rf.get("download_url")
                file_type = rf_type
                break

        if transcript_url:
            # Initialize processing result
            _processing_results[meeting_id] = TranscriptProcessingResult(
                meeting_id=meeting_id,
                status=ProcessingStatus.PENDING,
            )

            # Queue background processing
            background_tasks.add_task(
                process_recording_transcript,
                meeting_id=meeting_id,
                meeting_uuid=meeting_uuid,
                topic=topic,
                host_email=host_email,
                transcript_url=transcript_url,
                file_type=file_type,
                download_token=download_token,
            )
        else:
            logger.warning(f"No transcript URL in transcript_completed event for {meeting_id}")

    except Exception as e:
        logger.error(f"Error handling transcript_completed: {e}")


async def handle_meeting_ended(payload: Dict[str, Any]):
    """Handle meeting.ended webhook event.

    Used for tracking meeting completions and triggering follow-up actions.
    """
    try:
        event_data = payload.get("payload", {}).get("object", {})
        meeting_id = str(event_data.get("id", ""))
        topic = event_data.get("topic", "Unknown Meeting")
        duration = event_data.get("duration", 0)

        logger.info(
            f"Meeting ended: {topic} (ID: {meeting_id}, Duration: {duration} min)"
        )

        # Could trigger additional processing here, such as:
        # - Notifying users
        # - Scheduling follow-up tasks
        # - Updating CRM records

    except Exception as e:
        logger.error(f"Error handling meeting_ended: {e}")


async def process_recording_transcript(
    meeting_id: str,
    meeting_uuid: str,
    topic: str,
    host_email: str,
    transcript_url: str,
    file_type: str,
    download_token: Optional[str] = None,
):
    """Process a recording transcript through the SPICED analysis pipeline.

    This runs as a background task and:
    1. Downloads the transcript
    2. Parses it (VTT/SRT)
    3. Runs SPICED analysis via Claude
    4. Stores results for retrieval
    """
    result = _processing_results.get(meeting_id)
    if not result:
        result = TranscriptProcessingResult(
            meeting_id=meeting_id,
            status=ProcessingStatus.DOWNLOADING,
        )
        _processing_results[meeting_id] = result

    try:
        result.status = ProcessingStatus.DOWNLOADING
        logger.info(f"Downloading transcript for meeting {meeting_id}")

        # Download transcript
        async with ZoomClient() as client:
            transcript = await client.download_transcript_from_url(
                download_url=transcript_url,
                meeting_id=meeting_id,
                file_type=file_type,
                download_token=download_token,
            )

        if not transcript.parsed:
            raise ValueError("Failed to parse transcript")

        result.status = ProcessingStatus.PARSING
        result.transcript = transcript.parsed
        result.transcript.meeting_topic = topic

        logger.info(
            f"Transcript parsed for meeting {meeting_id}: "
            f"{len(transcript.parsed.lines)} lines, "
            f"{len(transcript.parsed.speakers)} speakers"
        )

        # Run SPICED analysis
        result.status = ProcessingStatus.ANALYZING
        logger.info(f"Running SPICED analysis for meeting {meeting_id}")

        pipeline = TranscriptProcessingPipeline()
        spiced_result = await pipeline.process_transcript(transcript.parsed)

        result.spiced_analysis = spiced_result
        result.status = ProcessingStatus.COMPLETED
        result.processed_at = datetime.utcnow()

        logger.info(f"SPICED analysis completed for meeting {meeting_id}")

        # Here you could also:
        # - Push results to HubSpot CRM
        # - Generate coaching recommendations
        # - Send notifications

    except Exception as e:
        logger.error(f"Error processing transcript for meeting {meeting_id}: {e}")
        result.status = ProcessingStatus.FAILED
        result.error = str(e)


# ==================== Processing Status Routes ====================


@router.get("/zoom/processing/{meeting_id}")
async def get_processing_status(meeting_id: str) -> TranscriptProcessingResult:
    """Get the processing status for a meeting transcript.

    Returns the current status and results of SPICED analysis.
    """
    result = _processing_results.get(meeting_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No processing found for meeting {meeting_id}",
        )
    return result


@router.get("/zoom/processing")
async def list_processing_results() -> Dict[str, Any]:
    """List all processing results.

    Returns summary of all processed and pending transcripts.
    """
    results = []
    for meeting_id, result in _processing_results.items():
        results.append({
            "meeting_id": meeting_id,
            "status": result.status.value,
            "has_transcript": result.transcript is not None,
            "has_spiced_analysis": result.spiced_analysis is not None,
            "processed_at": result.processed_at.isoformat() if result.processed_at else None,
            "error": result.error,
        })

    return {
        "total": len(results),
        "results": results,
    }
