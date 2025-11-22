"""
Avoma webhook handler for new recording notifications.

Handles incoming webhooks from Avoma to:
- Process new recordings automatically
- Trigger the SPICED extraction pipeline
- Map meeting metadata to internal models
"""

import logging
from datetime import datetime
from typing import Any, Callable, Coroutine, Optional

from app.models.avoma import (
    AvomaMeetingMetadata,
    AvomaRecordingStatus,
    AvomaTranscript,
    AvomaWebhookEvent,
    AvomaWebhookEventType,
)

from .auth import AvomaAuthManager
from .client import AvomaAPIError, AvomaClient

logger = logging.getLogger(__name__)


# Type alias for pipeline callback
PipelineCallback = Callable[
    [AvomaTranscript, AvomaMeetingMetadata],
    Coroutine[Any, Any, None]
]


class AvomaWebhookError(Exception):
    """Exception raised for webhook processing errors."""

    def __init__(self, message: str, event_id: Optional[str] = None):
        self.message = message
        self.event_id = event_id
        super().__init__(self.message)


class AvomaWebhookHandler:
    """
    Handles webhook events from Avoma.

    Processes recording completion events and triggers the
    SPICED extraction pipeline automatically.
    """

    def __init__(
        self,
        client: AvomaClient,
        auth_manager: AvomaAuthManager,
        pipeline_callback: Optional[PipelineCallback] = None,
    ):
        """
        Initialize the webhook handler.

        Args:
            client: AvomaClient instance for API calls
            auth_manager: AvomaAuthManager for signature verification
            pipeline_callback: Callback function to trigger SPICED pipeline
        """
        self.client = client
        self.auth_manager = auth_manager
        self.pipeline_callback = pipeline_callback
        self._processed_events: set[str] = set()  # For idempotency

    def set_pipeline_callback(self, callback: PipelineCallback) -> None:
        """
        Set the callback function for triggering the transcript processing pipeline.

        Args:
            callback: Async function that takes (transcript, metadata) and processes them
        """
        self.pipeline_callback = callback

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify the webhook signature.

        Args:
            payload: Raw request body
            signature: X-Avoma-Signature header value
            timestamp: X-Avoma-Timestamp header value (optional)

        Returns:
            True if signature is valid
        """
        return self.auth_manager.verify_webhook_signature(payload, signature, timestamp)

    def _is_event_processed(self, event_id: str) -> bool:
        """Check if an event has already been processed (idempotency)."""
        return event_id in self._processed_events

    def _mark_event_processed(self, event_id: str) -> None:
        """Mark an event as processed."""
        self._processed_events.add(event_id)
        # Keep the set bounded to prevent memory issues
        if len(self._processed_events) > 10000:
            # Remove oldest entries (simple approach - in production use LRU cache)
            excess = len(self._processed_events) - 5000
            for _ in range(excess):
                self._processed_events.pop()

    async def handle_webhook(
        self,
        event_data: dict,
        raw_payload: Optional[bytes] = None,
        signature: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Process an incoming webhook event.

        Args:
            event_data: Parsed webhook event data
            raw_payload: Raw request body for signature verification
            signature: X-Avoma-Signature header value
            timestamp: X-Avoma-Timestamp header value

        Returns:
            Dictionary with processing result

        Raises:
            AvomaWebhookError: If processing fails
        """
        # Verify signature if provided
        if raw_payload and signature:
            if not self.verify_signature(raw_payload, signature, timestamp):
                raise AvomaWebhookError("Invalid webhook signature")

        # Parse the event
        try:
            event = AvomaWebhookEvent(
                event_id=event_data["event_id"],
                event_type=AvomaWebhookEventType(event_data["event_type"]),
                recording_id=event_data["recording_id"],
                meeting_id=event_data.get("meeting_id"),
                timestamp=datetime.fromisoformat(
                    event_data["timestamp"].replace("Z", "+00:00")
                ),
                organization_id=event_data["organization_id"],
                payload=event_data.get("payload", {}),
            )
        except (KeyError, ValueError) as e:
            raise AvomaWebhookError(f"Invalid webhook payload: {str(e)}")

        # Check idempotency
        if self._is_event_processed(event.event_id):
            logger.info(f"Event {event.event_id} already processed, skipping")
            return {
                "status": "skipped",
                "event_id": event.event_id,
                "reason": "already_processed",
            }

        logger.info(
            f"Processing webhook event: {event.event_type} for recording {event.recording_id}"
        )

        # Route to appropriate handler
        result = await self._route_event(event)

        # Mark as processed
        self._mark_event_processed(event.event_id)

        return result

    async def _route_event(self, event: AvomaWebhookEvent) -> dict[str, Any]:
        """Route event to appropriate handler based on type."""
        handlers = {
            AvomaWebhookEventType.RECORDING_COMPLETED: self._handle_recording_completed,
            AvomaWebhookEventType.TRANSCRIPT_READY: self._handle_transcript_ready,
            AvomaWebhookEventType.RECORDING_FAILED: self._handle_recording_failed,
            AvomaWebhookEventType.MEETING_ENDED: self._handle_meeting_ended,
            AvomaWebhookEventType.NOTES_UPDATED: self._handle_notes_updated,
        }

        handler = handlers.get(event.event_type)
        if handler:
            return await handler(event)

        logger.warning(f"Unknown event type: {event.event_type}")
        return {
            "status": "ignored",
            "event_id": event.event_id,
            "reason": f"unknown_event_type: {event.event_type}",
        }

    async def _handle_recording_completed(
        self, event: AvomaWebhookEvent
    ) -> dict[str, Any]:
        """
        Handle recording completed event.

        Fetches transcript and metadata, then triggers SPICED extraction.
        """
        recording_id = event.recording_id
        logger.info(f"Recording completed: {recording_id}")

        try:
            # Fetch transcript and metadata
            transcript = await self.client.get_transcript(recording_id)
            metadata = await self.client.get_meeting_metadata(recording_id)

            # Trigger SPICED extraction pipeline
            if self.pipeline_callback:
                await self.pipeline_callback(transcript, metadata)
                logger.info(f"SPICED pipeline triggered for recording {recording_id}")

            return {
                "status": "success",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "transcript_id": transcript.id,
                "pipeline_triggered": self.pipeline_callback is not None,
            }

        except AvomaAPIError as e:
            logger.error(f"Failed to process recording {recording_id}: {e.message}")
            return {
                "status": "error",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "error": e.message,
            }

    async def _handle_transcript_ready(
        self, event: AvomaWebhookEvent
    ) -> dict[str, Any]:
        """
        Handle transcript ready event.

        Similar to recording completed, but specifically for transcript availability.
        """
        recording_id = event.recording_id
        logger.info(f"Transcript ready: {recording_id}")

        try:
            # Fetch transcript and metadata
            transcript = await self.client.get_transcript(recording_id)
            metadata = await self.client.get_meeting_metadata(recording_id)

            # Trigger SPICED extraction pipeline
            if self.pipeline_callback:
                await self.pipeline_callback(transcript, metadata)
                logger.info(f"SPICED pipeline triggered for recording {recording_id}")

            return {
                "status": "success",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "transcript_id": transcript.id,
                "pipeline_triggered": self.pipeline_callback is not None,
            }

        except AvomaAPIError as e:
            logger.error(f"Failed to fetch transcript {recording_id}: {e.message}")
            return {
                "status": "error",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "error": e.message,
            }

    async def _handle_recording_failed(
        self, event: AvomaWebhookEvent
    ) -> dict[str, Any]:
        """Handle recording failed event."""
        recording_id = event.recording_id
        error_reason = event.payload.get("error", "unknown")

        logger.error(f"Recording failed: {recording_id}, reason: {error_reason}")

        return {
            "status": "acknowledged",
            "event_id": event.event_id,
            "recording_id": recording_id,
            "recording_status": "failed",
            "error_reason": error_reason,
        }

    async def _handle_meeting_ended(self, event: AvomaWebhookEvent) -> dict[str, Any]:
        """
        Handle meeting ended event.

        This is an early notification - transcript may not be ready yet.
        """
        recording_id = event.recording_id
        logger.info(f"Meeting ended: {recording_id}")

        return {
            "status": "acknowledged",
            "event_id": event.event_id,
            "recording_id": recording_id,
            "message": "Meeting ended, waiting for transcript",
        }

    async def _handle_notes_updated(self, event: AvomaWebhookEvent) -> dict[str, Any]:
        """Handle notes updated event."""
        recording_id = event.recording_id
        logger.info(f"Notes updated for recording: {recording_id}")

        try:
            # Fetch updated metadata with new notes
            metadata = await self.client.get_meeting_metadata(recording_id)

            return {
                "status": "success",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "notes_present": metadata.notes is not None,
                "action_items_count": len(metadata.action_items),
            }

        except AvomaAPIError as e:
            logger.error(f"Failed to fetch updated notes: {e.message}")
            return {
                "status": "error",
                "event_id": event.event_id,
                "recording_id": recording_id,
                "error": e.message,
            }


class TranscriptMapper:
    """
    Maps Avoma transcript and metadata to internal models.

    Used to transform Avoma data structures into the internal
    Sales OS data models for storage and processing.
    """

    @staticmethod
    def map_to_internal_transcript(
        avoma_transcript: AvomaTranscript,
        avoma_metadata: AvomaMeetingMetadata,
    ) -> dict[str, Any]:
        """
        Map Avoma transcript to internal transcript format.

        Args:
            avoma_transcript: The Avoma transcript
            avoma_metadata: The meeting metadata

        Returns:
            Dictionary with internal transcript format
        """
        # Build speaker map from attendees
        speaker_map = {}
        for attendee in avoma_metadata.attendees:
            if attendee.speaker_id:
                speaker_map[attendee.speaker_id] = {
                    "name": attendee.name,
                    "email": attendee.email,
                    "is_internal": attendee.is_internal,
                }

        # Map utterances with speaker info
        segments = []
        for utterance in avoma_transcript.utterances:
            speaker_info = speaker_map.get(utterance.speaker_id, {})
            segments.append({
                "speaker": speaker_info.get("name", utterance.speaker_name or f"Speaker {utterance.speaker_id}"),
                "speaker_email": speaker_info.get("email"),
                "is_internal": speaker_info.get("is_internal", False),
                "text": utterance.text,
                "start_time": utterance.start_time,
                "end_time": utterance.end_time,
            })

        return {
            "source": "avoma",
            "source_id": avoma_transcript.recording_id,
            "title": avoma_metadata.title,
            "meeting_type": avoma_metadata.meeting_type,
            "duration_seconds": avoma_metadata.duration_seconds,
            "meeting_date": avoma_metadata.actual_start.isoformat(),
            "segments": segments,
            "full_text": avoma_transcript.get_formatted_transcript(),
            "attendees": [
                {
                    "name": a.name,
                    "email": a.email,
                    "role": a.role,
                    "is_internal": a.is_internal,
                }
                for a in avoma_metadata.attendees
            ],
            "tags": avoma_metadata.tags,
            "crm_opportunity_id": avoma_metadata.crm_opportunity_id,
            "crm_contact_ids": avoma_metadata.crm_contact_ids,
            "metadata": {
                "avoma_recording_id": avoma_transcript.recording_id,
                "avoma_meeting_id": avoma_metadata.id,
                "language": avoma_transcript.language,
                "sentiment_score": avoma_metadata.sentiment_score,
                "action_items": avoma_metadata.action_items,
                "topics_discussed": avoma_metadata.topics_discussed,
            },
        }

    @staticmethod
    def extract_participants(metadata: AvomaMeetingMetadata) -> dict[str, list[dict]]:
        """
        Extract and categorize meeting participants.

        Args:
            metadata: Meeting metadata

        Returns:
            Dictionary with internal and external participants
        """
        internal = []
        external = []

        for attendee in metadata.attendees:
            participant = {
                "name": attendee.name,
                "email": attendee.email,
                "role": attendee.role,
            }
            if attendee.is_internal:
                internal.append(participant)
            else:
                external.append(participant)

        return {
            "internal": internal,
            "external": external,
            "host": {
                "name": metadata.host.name if metadata.host else None,
                "email": metadata.host.email if metadata.host else None,
            },
        }
