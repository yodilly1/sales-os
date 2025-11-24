"""
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


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
    )
