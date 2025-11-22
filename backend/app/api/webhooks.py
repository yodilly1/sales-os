<<<<<<< HEAD
"""
<<<<<<< HEAD
Webhook handlers for external service integrations.

Provides endpoints for receiving webhooks from:
- Avoma (recording completed, transcript ready)
- HubSpot (contact updates, deal changes)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.integrations.avoma import AvomaAuthManager, AvomaClient
from app.integrations.avoma.webhooks import AvomaWebhookError, AvomaWebhookHandler
=======
Webhook handlers for Sales OS.

This module provides webhook endpoints for receiving events from external
services and triggering appropriate workflows, including Slack notifications.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.integrations.slack.client import create_client
from app.integrations.slack.messages import (
    build_call_processed_notification,
    build_content_ready_notification,
    build_coaching_feedback_notification,
    build_prospect_enriched_notification,
)
from app.models.slack import (
    SlackNotification,
    SlackNotificationTarget,
    SlackNotificationType,
)
>>>>>>> origin/claude/slack-integration-01FAipAuMUsRJRL7psy92hdb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


<<<<<<< HEAD
# Webhook handler instances
_avoma_webhook_handler: Optional[AvomaWebhookHandler] = None


async def get_avoma_webhook_handler() -> AvomaWebhookHandler:
    """
    Dependency to get the Avoma webhook handler.

    Configures the handler with proper credentials and pipeline callback.
    """
    global _avoma_webhook_handler

    if _avoma_webhook_handler is None:
        from app.core.config import get_settings

        settings = get_settings()

        auth_manager = AvomaAuthManager(
            client_id=settings.avoma_client_id,
            client_secret=settings.avoma_client_secret,
            api_key=settings.avoma_api_key,
            webhook_secret=settings.avoma_webhook_secret,
        )

        client = AvomaClient(auth_manager)

        _avoma_webhook_handler = AvomaWebhookHandler(
            client=client,
            auth_manager=auth_manager,
        )

        # Set up pipeline callback to trigger SPICED extraction
        # In production, this would be configured to call the actual service
        async def trigger_spiced_pipeline(transcript, metadata):
            """Callback to trigger SPICED extraction when transcript is received."""
            from app.integrations.avoma.webhooks import TranscriptMapper

            logger.info(f"Triggering SPICED pipeline for recording {transcript.recording_id}")

            # Map to internal format
            internal_transcript = TranscriptMapper.map_to_internal_transcript(
                transcript, metadata
            )

            # TODO: Integrate with actual SPICED extraction service
            # Example: await spiced_service.extract(internal_transcript)
            logger.info(
                f"SPICED extraction triggered for: {metadata.title} "
                f"({len(transcript.utterances)} utterances)"
            )

        _avoma_webhook_handler.set_pipeline_callback(trigger_spiced_pipeline)

    return _avoma_webhook_handler


# Response models

class WebhookResponse(BaseModel):
    """Standard webhook response."""
    status: str = Field(..., description="Processing status")
    event_id: Optional[str] = Field(None, description="Event ID that was processed")
    message: Optional[str] = Field(None, description="Additional message")


class WebhookErrorResponse(BaseModel):
    """Error response for webhook processing."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    event_id: Optional[str] = Field(None, description="Event ID if available")


# Avoma webhook endpoints

@router.post(
    "/avoma",
    response_model=WebhookResponse,
    responses={
        400: {"model": WebhookErrorResponse, "description": "Invalid webhook payload"},
        401: {"model": WebhookErrorResponse, "description": "Invalid signature"},
        500: {"model": WebhookErrorResponse, "description": "Processing error"},
    },
)
async def handle_avoma_webhook(
    request: Request,
    x_avoma_signature: Optional[str] = Header(None, alias="X-Avoma-Signature"),
    x_avoma_timestamp: Optional[str] = Header(None, alias="X-Avoma-Timestamp"),
    handler: AvomaWebhookHandler = Depends(get_avoma_webhook_handler),
) -> WebhookResponse:
    """
    Handle incoming webhooks from Avoma.

    Processes events like:
    - recording.completed: New recording ready for transcript
    - transcript.ready: Transcript available for download
    - recording.failed: Recording processing failed
    - meeting.ended: Meeting ended (transcript pending)
    - notes.updated: Meeting notes were updated

    The webhook signature is verified using the X-Avoma-Signature header.
    """
    # Get raw body for signature verification
    raw_body = await request.body()

    try:
        # Parse JSON body
        event_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    try:
        # Process the webhook
        result = await handler.handle_webhook(
            event_data=event_data,
            raw_payload=raw_body,
            signature=x_avoma_signature,
            timestamp=x_avoma_timestamp,
        )

        logger.info(f"Processed Avoma webhook: {result.get('status')} - {result.get('event_id')}")

        return WebhookResponse(
            status=result.get("status", "success"),
            event_id=result.get("event_id"),
            message=result.get("message"),
        )

    except AvomaWebhookError as e:
        logger.error(f"Webhook processing error: {e.message}")

        if "signature" in e.message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )

    except Exception as e:
        logger.exception(f"Unexpected error processing Avoma webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook",
        )


@router.post("/avoma/test", response_model=WebhookResponse)
async def test_avoma_webhook(
    handler: AvomaWebhookHandler = Depends(get_avoma_webhook_handler),
) -> WebhookResponse:
    """
    Test endpoint for Avoma webhook processing.

    Simulates a recording.completed event for testing purposes.
    Does not verify signatures.
    """
    test_event = {
        "event_id": "test-event-001",
        "event_type": "recording.completed",
        "recording_id": "test-recording-001",
        "meeting_id": "test-meeting-001",
        "timestamp": "2024-01-15T10:30:00Z",
        "organization_id": "test-org-001",
        "payload": {
            "title": "Test Meeting",
            "duration_seconds": 1800,
        },
    }

    try:
        result = await handler.handle_webhook(
            event_data=test_event,
            raw_payload=None,
            signature=None,
            timestamp=None,
        )

        return WebhookResponse(
            status=result.get("status", "success"),
            event_id=result.get("event_id"),
            message="Test webhook processed successfully",
        )

    except AvomaWebhookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# Health check for webhook endpoints

@router.get("/health")
async def webhooks_health() -> dict:
    """
    Health check for webhook endpoints.

    Returns status of configured webhook handlers.
    """
    return {
        "status": "healthy",
        "handlers": {
            "avoma": _avoma_webhook_handler is not None,
            # Add other webhook handlers as they're implemented
            # "hubspot": _hubspot_webhook_handler is not None,
        },
    }


# Placeholder for future webhook integrations

@router.post("/hubspot", include_in_schema=False)
async def handle_hubspot_webhook(request: Request) -> WebhookResponse:
    """
    Placeholder for HubSpot webhook handling.

    To be implemented by AGENT-004 (HubSpot integration).
    """
    logger.warning("HubSpot webhook endpoint not yet implemented")
    return WebhookResponse(
        status="not_implemented",
        message="HubSpot webhook handling coming soon",
=======
# === Webhook Payload Models ===


class CallProcessedWebhook(BaseModel):
    """Webhook payload for call processed events."""

    call_id: str = Field(..., description="Unique call identifier")
    title: str = Field(..., description="Call title")
    summary: str = Field(..., description="Brief call summary")
    spiced_scores: Optional[dict] = Field(None, description="SPICED methodology scores")
    next_steps: Optional[list[str]] = Field(None, description="Identified next steps")
    notify_channel: Optional[str] = Field(None, description="Slack channel ID")
    notify_user: Optional[str] = Field(None, description="Slack user ID for DM")


class ContentReadyWebhook(BaseModel):
    """Webhook payload for content ready events."""

    content_id: str = Field(..., description="Unique content identifier")
    content_type: str = Field(..., description="Type: deck, proposal, one-pager")
    title: str = Field(..., description="Content title")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    notify_channel: Optional[str] = Field(None, description="Slack channel ID")
    notify_user: Optional[str] = Field(None, description="Slack user ID for DM")


class CoachingReadyWebhook(BaseModel):
    """Webhook payload for coaching feedback ready events."""

    call_id: str = Field(..., description="Call ID")
    overall_score: int = Field(..., ge=1, le=10, description="Overall score 1-10")
    top_strength: str = Field(..., description="Primary strength")
    top_improvement: str = Field(..., description="Primary improvement area")
    notify_channel: Optional[str] = Field(None, description="Slack channel ID")
    notify_user: Optional[str] = Field(None, description="Slack user ID for DM")


class ProspectEnrichedWebhook(BaseModel):
    """Webhook payload for prospect enriched events."""

    prospect_id: str = Field(..., description="Prospect identifier")
    prospect_name: str = Field(..., description="Prospect name")
    company_name: str = Field(..., description="Company name")
    key_insights: list[str] = Field(default_factory=list, description="Key insights")
    notify_channel: Optional[str] = Field(None, description="Slack channel ID")
    notify_user: Optional[str] = Field(None, description="Slack user ID for DM")


# === Internal Notification Service ===


class SlackNotificationService:
    """
    Service for sending Slack notifications from webhooks.

    Respects user notification preferences and routes to appropriate channels.
    """

    def __init__(self):
        self.client = create_client()

    async def notify_call_processed(self, payload: CallProcessedWebhook) -> bool:
        """Send notification for a processed call."""
        blocks = build_call_processed_notification(
            call_id=payload.call_id,
            title=payload.title,
            summary=payload.summary,
            spiced_scores=payload.spiced_scores,
            next_steps=payload.next_steps,
        )

        return await self._send_notification(
            channel_id=payload.notify_channel,
            user_id=payload.notify_user,
            text=f"Call processed: {payload.title}",
            blocks=blocks,
        )

    async def notify_content_ready(self, payload: ContentReadyWebhook) -> bool:
        """Send notification for ready content."""
        blocks = build_content_ready_notification(
            content_id=payload.content_id,
            content_type=payload.content_type,
            title=payload.title,
            preview_url=payload.preview_url,
        )

        return await self._send_notification(
            channel_id=payload.notify_channel,
            user_id=payload.notify_user,
            text=f"Content ready: {payload.title}",
            blocks=blocks,
        )

    async def notify_coaching_ready(self, payload: CoachingReadyWebhook) -> bool:
        """Send notification for coaching feedback."""
        blocks = build_coaching_feedback_notification(
            call_id=payload.call_id,
            overall_score=payload.overall_score,
            top_strength=payload.top_strength,
            top_improvement=payload.top_improvement,
        )

        return await self._send_notification(
            channel_id=payload.notify_channel,
            user_id=payload.notify_user,
            text=f"Coaching feedback available (Score: {payload.overall_score}/10)",
            blocks=blocks,
        )

    async def notify_prospect_enriched(self, payload: ProspectEnrichedWebhook) -> bool:
        """Send notification for enriched prospect."""
        blocks = build_prospect_enriched_notification(
            prospect_name=payload.prospect_name,
            company_name=payload.company_name,
            key_insights=payload.key_insights,
        )

        return await self._send_notification(
            channel_id=payload.notify_channel,
            user_id=payload.notify_user,
            text=f"Prospect enriched: {payload.prospect_name} at {payload.company_name}",
            blocks=blocks,
        )

    async def _send_notification(
        self,
        channel_id: Optional[str],
        user_id: Optional[str],
        text: str,
        blocks: list[dict],
    ) -> bool:
        """
        Send notification to channel and/or user.

        Args:
            channel_id: Channel to notify (if any).
            user_id: User to DM (if any).
            text: Fallback text.
            blocks: Block Kit blocks.

        Returns:
            True if at least one notification succeeded.
        """
        success = False

        # Send to channel if specified
        if channel_id:
            result = await self.client.send_message(
                channel=channel_id,
                text=text,
                blocks=blocks,
            )
            if result.ok:
                success = True
                logger.info(f"Sent notification to channel {channel_id}")
            else:
                logger.error(f"Failed to notify channel {channel_id}: {result.error}")

        # Send DM if specified
        if user_id:
            result = await self.client.send_dm(
                user_id=user_id,
                text=text,
                blocks=blocks,
            )
            if result.ok:
                success = True
                logger.info(f"Sent DM notification to user {user_id}")
            else:
                logger.error(f"Failed to DM user {user_id}: {result.error}")

        return success


# Global notification service instance
notification_service = SlackNotificationService()


# === Webhook Endpoints ===


@router.post("/call-processed")
async def webhook_call_processed(
    payload: CallProcessedWebhook,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handle call processed webhook.

    Triggered when a call transcript has been processed and SPICED analysis
    is complete. Sends Slack notifications to configured channels/users.
    """
    logger.info(f"Received call processed webhook for call {payload.call_id}")

    # Send notification in background
    background_tasks.add_task(
        notification_service.notify_call_processed,
        payload,
    )

    return JSONResponse(
        content={
            "ok": True,
            "message": f"Processing notification for call {payload.call_id}",
        }
    )


@router.post("/content-ready")
async def webhook_content_ready(
    payload: ContentReadyWebhook,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handle content ready webhook.

    Triggered when content generation is complete (deck, proposal, one-pager).
    Sends Slack notifications to configured channels/users.
    """
    logger.info(
        f"Received content ready webhook for content {payload.content_id} "
        f"({payload.content_type})"
    )

    # Send notification in background
    background_tasks.add_task(
        notification_service.notify_content_ready,
        payload,
    )

    return JSONResponse(
        content={
            "ok": True,
            "message": f"Processing notification for content {payload.content_id}",
        }
    )


@router.post("/coaching-ready")
async def webhook_coaching_ready(
    payload: CoachingReadyWebhook,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handle coaching feedback ready webhook.

    Triggered when SPICED coaching analysis is complete for a call.
    Sends Slack notifications to configured channels/users.
    """
    logger.info(f"Received coaching ready webhook for call {payload.call_id}")

    # Send notification in background
    background_tasks.add_task(
        notification_service.notify_coaching_ready,
        payload,
    )

    return JSONResponse(
        content={
            "ok": True,
            "message": f"Processing coaching notification for call {payload.call_id}",
        }
    )


@router.post("/prospect-enriched")
async def webhook_prospect_enriched(
    payload: ProspectEnrichedWebhook,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handle prospect enriched webhook.

    Triggered when prospect research/enrichment is complete.
    Sends Slack notifications to configured channels/users.
    """
    logger.info(
        f"Received prospect enriched webhook for {payload.prospect_name} "
        f"at {payload.company_name}"
    )

    # Send notification in background
    background_tasks.add_task(
        notification_service.notify_prospect_enriched,
        payload,
    )

    return JSONResponse(
        content={
            "ok": True,
            "message": f"Processing notification for prospect {payload.prospect_id}",
        }
    )


# === Generic Notification Endpoint ===


class GenericNotificationPayload(BaseModel):
    """Generic notification payload for custom notifications."""

    notification_type: str = Field(..., description="Notification type identifier")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    channel_id: Optional[str] = Field(None, description="Slack channel ID")
    user_id: Optional[str] = Field(None, description="Slack user ID for DM")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


@router.post("/notify")
async def webhook_generic_notify(
    payload: GenericNotificationPayload,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handle generic notification webhook.

    Allows other services to send custom Slack notifications.
    """
    logger.info(f"Received generic notification: {payload.notification_type}")

    async def send_generic():
        client = create_client()

        if payload.channel_id:
            await client.send_message(
                channel=payload.channel_id,
                text=f"*{payload.title}*\n{payload.message}",
            )

        if payload.user_id:
            await client.send_dm(
                user_id=payload.user_id,
                text=f"*{payload.title}*\n{payload.message}",
            )

    background_tasks.add_task(send_generic)

    return JSONResponse(
        content={
            "ok": True,
            "message": "Processing notification",
        }
    )


# === Health Check ===


@router.get("/health")
async def webhooks_health() -> JSONResponse:
    """Check webhooks endpoint health."""
    return JSONResponse(
        content={
            "status": "ok",
            "endpoints": [
                "/webhooks/call-processed",
                "/webhooks/content-ready",
                "/webhooks/coaching-ready",
                "/webhooks/prospect-enriched",
                "/webhooks/notify",
            ],
        }
>>>>>>> origin/claude/slack-integration-01FAipAuMUsRJRL7psy92hdb
    )
=======
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
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP
