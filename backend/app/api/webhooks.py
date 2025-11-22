"""
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


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
    )
