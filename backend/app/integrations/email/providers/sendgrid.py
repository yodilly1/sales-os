"""
SendGrid Email Provider Implementation

Provides email sending capabilities using SendGrid's API.
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

import httpx

from ....models.email import (
    EmailMessage,
    EmailProvider,
    EmailStatus,
    SendEmailResponse,
    EmailEvent,
    EmailEventType,
    BounceType,
    WebhookPayload,
)
from .base import EmailProviderBase


logger = logging.getLogger(__name__)


class SendGridProvider(EmailProviderBase):
    """
    SendGrid email provider implementation.

    Supports sending emails, tracking, and webhook handling via SendGrid's API.
    """

    SENDGRID_API_URL = "https://api.sendgrid.com/v3"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SendGrid provider.

        Config required keys:
            - api_key: SendGrid API key
            - webhook_verification_key: Key for verifying webhooks (optional)
        """
        super().__init__(config)
        self.api_key = config["api_key"]
        self.webhook_key = config.get("webhook_verification_key")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> EmailProvider:
        return EmailProvider.SENDGRID

    def _validate_config(self) -> None:
        if not self.config.get("api_key"):
            raise ValueError("SendGrid API key is required")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.SENDGRID_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _build_personalization(self, message: EmailMessage) -> Dict[str, Any]:
        """Build the personalization object for SendGrid."""
        personalization: Dict[str, Any] = {
            "to": [
                {"email": r.email, "name": r.name}
                if r.name else {"email": r.email}
                for r in message.to_recipients
            ],
        }

        if message.cc_recipients:
            personalization["cc"] = [
                {"email": r.email, "name": r.name}
                if r.name else {"email": r.email}
                for r in message.cc_recipients
            ]

        if message.bcc_recipients:
            personalization["bcc"] = [
                {"email": r.email, "name": r.name}
                if r.name else {"email": r.email}
                for r in message.bcc_recipients
            ]

        # Add template substitutions if using dynamic templates
        if message.template_variables:
            personalization["dynamic_template_data"] = message.template_variables

        return personalization

    def _build_payload(self, message: EmailMessage) -> Dict[str, Any]:
        """Build the complete API payload for SendGrid."""
        payload: Dict[str, Any] = {
            "personalizations": [self._build_personalization(message)],
            "from": {
                "email": message.from_email,
            },
            "subject": message.subject,
            "tracking_settings": {
                "click_tracking": {"enable": message.track_clicks},
                "open_tracking": {"enable": message.track_opens},
            },
        }

        if message.from_name:
            payload["from"]["name"] = message.from_name

        if message.reply_to:
            payload["reply_to"] = {"email": message.reply_to}

        # Content
        content = []
        if message.text_content:
            content.append({"type": "text/plain", "value": message.text_content})
        if message.html_content:
            content.append({"type": "text/html", "value": message.html_content})
        if content:
            payload["content"] = content

        # Attachments
        if message.attachments:
            payload["attachments"] = [
                {
                    "content": att.content_base64,
                    "filename": att.filename,
                    "type": att.content_type,
                }
                for att in message.attachments
                if att.content_base64
            ]

        # Categories/Tags
        if message.tags:
            payload["categories"] = message.tags[:10]  # SendGrid limit

        # Custom tracking ID
        payload["custom_args"] = {
            "tracking_id": message.tracking_id,
            "message_id": str(message.id),
        }

        if message.metadata:
            payload["custom_args"].update(message.metadata)

        return payload

    async def send_email(self, message: EmailMessage) -> SendEmailResponse:
        """Send an email via SendGrid."""
        try:
            client = await self._get_client()
            payload = self._build_payload(message)

            response = await client.post("/mail/send", json=payload)

            if response.status_code in (200, 201, 202):
                # SendGrid returns message ID in x-message-id header
                provider_message_id = response.headers.get("x-message-id", "")
                return SendEmailResponse(
                    success=True,
                    message_id=message.id,
                    provider_message_id=provider_message_id,
                    status=EmailStatus.SENT,
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = str(error_data.get("errors", response.text))
                logger.error(f"SendGrid send failed: {error_message}")
                return SendEmailResponse(
                    success=False,
                    message_id=message.id,
                    status=EmailStatus.FAILED,
                    error=error_message,
                )

        except httpx.RequestError as e:
            logger.exception("SendGrid request error")
            return SendEmailResponse(
                success=False,
                message_id=message.id,
                status=EmailStatus.FAILED,
                error=str(e),
            )

    async def send_batch(
        self, messages: List[EmailMessage]
    ) -> List[SendEmailResponse]:
        """Send multiple emails in batch."""
        # SendGrid doesn't have true batch sending via API,
        # so we send individually but concurrently
        import asyncio

        tasks = [self.send_email(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(SendEmailResponse(
                    success=False,
                    message_id=messages[i].id,
                    status=EmailStatus.FAILED,
                    error=str(result),
                ))
            else:
                responses.append(result)

        return responses

    async def get_message_status(
        self, provider_message_id: str
    ) -> Optional[EmailStatus]:
        """
        Get message status from SendGrid.

        Note: SendGrid doesn't have a direct status endpoint.
        Status is typically retrieved via webhooks or activity API.
        """
        try:
            client = await self._get_client()
            # Query the email activity API
            response = await client.get(
                "/messages",
                params={"query": f"msg_id={provider_message_id}"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("messages"):
                    msg = data["messages"][0]
                    status_map = {
                        "delivered": EmailStatus.DELIVERED,
                        "processed": EmailStatus.SENT,
                        "bounce": EmailStatus.BOUNCED,
                        "dropped": EmailStatus.FAILED,
                        "open": EmailStatus.OPENED,
                        "click": EmailStatus.CLICKED,
                    }
                    return status_map.get(msg.get("status"), EmailStatus.SENT)

            return None

        except Exception as e:
            logger.exception("Error getting message status from SendGrid")
            return None

    def verify_webhook_signature(
        self, payload: bytes, signature: str, timestamp: Optional[str] = None
    ) -> bool:
        """Verify SendGrid webhook signature."""
        if not self.webhook_key:
            logger.warning("Webhook verification key not configured")
            return True  # Skip verification if not configured

        try:
            # SendGrid uses the Event Webhook with a verification key
            # The signature is an ECDSA signature of timestamp + payload
            if not timestamp:
                return False

            # Compute expected signature
            signed_payload = f"{timestamp}{payload.decode()}"
            expected = hmac.new(
                self.webhook_key.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected, signature)

        except Exception as e:
            logger.exception("Error verifying webhook signature")
            return False

    def parse_webhook_event(
        self, payload: WebhookPayload
    ) -> Optional[EmailEvent]:
        """Parse SendGrid webhook event."""
        try:
            data = payload.data

            event_type = self._map_event_type(data.get("event", ""))
            if not event_type:
                return None

            # Extract message ID from custom args or sg_message_id
            message_id_str = (
                data.get("message_id") or
                data.get("sg_message_id", "").split(".")[0]
            )

            tracking_id = data.get("tracking_id")

            event = EmailEvent(
                event_type=event_type,
                email_id=UUID(message_id_str) if message_id_str else None,
                tracking_id=tracking_id,
                recipient_email=data.get("email"),
                timestamp=datetime.fromtimestamp(data.get("timestamp", 0)),
                ip_address=data.get("ip"),
                user_agent=data.get("useragent"),
                url=data.get("url"),
                provider=EmailProvider.SENDGRID,
                raw_event=data,
            )

            # Handle bounce details
            if event_type == EmailEventType.BOUNCED:
                event.bounce_type = self._map_bounce_type(
                    data.get("type", "soft")
                )
                event.bounce_reason = data.get("reason")

            return event

        except Exception as e:
            logger.exception("Error parsing SendGrid webhook event")
            return None

    async def add_to_suppression_list(
        self, email: str, reason: str = "bounce"
    ) -> bool:
        """Add email to SendGrid suppression list."""
        try:
            client = await self._get_client()

            # Determine which suppression group to use
            if reason == "bounce":
                endpoint = "/suppression/bounces"
                payload = {"emails": [email]}
            elif reason == "spam":
                endpoint = "/suppression/spam_reports"
                payload = {"emails": [email]}
            else:
                # Use global unsubscribes for other reasons
                endpoint = "/asm/suppressions/global"
                payload = {"recipient_emails": [email]}

            response = await client.post(endpoint, json=payload)
            return response.status_code in (200, 201)

        except Exception as e:
            logger.exception("Error adding to suppression list")
            return False

    async def remove_from_suppression_list(self, email: str) -> bool:
        """Remove email from SendGrid suppression lists."""
        try:
            client = await self._get_client()
            success = True

            # Remove from all suppression lists
            endpoints = [
                f"/suppression/bounces/{email}",
                f"/suppression/blocks/{email}",
                f"/suppression/spam_reports/{email}",
                f"/asm/suppressions/global/{email}",
            ]

            for endpoint in endpoints:
                try:
                    response = await client.delete(endpoint)
                    # 204 = deleted, 404 = not found (both are ok)
                except Exception:
                    pass

            return success

        except Exception as e:
            logger.exception("Error removing from suppression list")
            return False

    async def check_suppression_status(self, email: str) -> Optional[Dict[str, Any]]:
        """Check if email is on any SendGrid suppression list."""
        try:
            client = await self._get_client()
            result = {"suppressed": False, "lists": []}

            # Check global suppressions
            response = await client.get(f"/asm/suppressions/global/{email}")
            if response.status_code == 200:
                result["suppressed"] = True
                result["lists"].append("global")

            # Check bounces
            response = await client.get(
                "/suppression/bounces",
                params={"email": email}
            )
            if response.status_code == 200 and response.json():
                result["suppressed"] = True
                result["lists"].append("bounces")
                result["bounce_data"] = response.json()[0]

            # Check spam reports
            response = await client.get(
                "/suppression/spam_reports",
                params={"email": email}
            )
            if response.status_code == 200 and response.json():
                result["suppressed"] = True
                result["lists"].append("spam_reports")

            return result if result["suppressed"] else None

        except Exception as e:
            logger.exception("Error checking suppression status")
            return None
