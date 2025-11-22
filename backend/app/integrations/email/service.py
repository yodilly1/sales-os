"""
Email Service for Sales OS

Main service class that orchestrates email sending, tracking, and management
across different providers.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

from ...models.email import (
    EmailMessage,
    EmailMessageCreate,
    EmailTemplate,
    EmailProvider,
    EmailStatus,
    SendEmailResponse,
    EmailEvent,
    EmailEventType,
    Unsubscribe,
    BounceRecord,
    WebhookPayload,
)
from .providers.base import EmailProviderBase
from .providers.sendgrid import SendGridProvider
from .providers.ses import SESProvider
from .template_renderer import TemplateRenderer
from .tracking import TrackingService
from .bounce_handler import BounceHandler
from .unsubscribe_manager import UnsubscribeManager


logger = logging.getLogger(__name__)


class EmailService:
    """
    Main email service for Sales OS.

    Provides a unified interface for:
    - Sending emails via SendGrid or SES
    - Rendering email templates
    - Tracking opens and clicks
    - Handling bounces
    - Managing unsubscribes
    """

    def __init__(
        self,
        provider_config: Dict[str, Any],
        tracking_base_url: str,
        default_from_email: str,
        default_from_name: Optional[str] = None,
    ):
        """
        Initialize the email service.

        Args:
            provider_config: Configuration dict with provider settings
            tracking_base_url: Base URL for tracking endpoints
            default_from_email: Default sender email address
            default_from_name: Default sender name
        """
        self.tracking_base_url = tracking_base_url
        self.default_from_email = default_from_email
        self.default_from_name = default_from_name

        # Initialize provider
        self.provider = self._init_provider(provider_config)

        # Initialize services
        self.template_renderer = TemplateRenderer()
        self.tracking_service = TrackingService()
        self.bounce_handler = BounceHandler()
        self.unsubscribe_manager = UnsubscribeManager()

        # In-memory storage (replace with database in production)
        self._messages: Dict[UUID, EmailMessage] = {}
        self._events: Dict[UUID, List[EmailEvent]] = {}

    def _init_provider(self, config: Dict[str, Any]) -> EmailProviderBase:
        """Initialize the appropriate email provider."""
        provider_type = config.get("provider", "sendgrid").lower()

        if provider_type == "sendgrid":
            return SendGridProvider(config.get("sendgrid", {}))
        elif provider_type == "ses":
            return SESProvider(config.get("ses", {}))
        else:
            raise ValueError(f"Unsupported email provider: {provider_type}")

    async def close(self) -> None:
        """Clean up resources."""
        if hasattr(self.provider, 'close'):
            await self.provider.close()

    async def send_email(
        self,
        message: EmailMessageCreate,
        template: Optional[EmailTemplate] = None,
    ) -> SendEmailResponse:
        """
        Send an email message.

        Args:
            message: Email message to send
            template: Optional template to render

        Returns:
            SendEmailResponse with status and message ID
        """
        # Check unsubscribes first
        for recipient in message.to_recipients:
            if await self.unsubscribe_manager.is_unsubscribed(recipient.email):
                logger.info(f"Skipping unsubscribed recipient: {recipient.email}")
                return SendEmailResponse(
                    success=False,
                    message_id=UUID('00000000-0000-0000-0000-000000000000'),
                    status=EmailStatus.UNSUBSCRIBED,
                    error=f"Recipient {recipient.email} is unsubscribed",
                )

        # Check bounce status
        for recipient in message.to_recipients:
            bounce = await self.bounce_handler.get_bounce_record(recipient.email)
            if bounce and bounce.bounce_type.value == "hard":
                logger.info(f"Skipping hard-bounced recipient: {recipient.email}")
                return SendEmailResponse(
                    success=False,
                    message_id=UUID('00000000-0000-0000-0000-000000000000'),
                    status=EmailStatus.BOUNCED,
                    error=f"Recipient {recipient.email} has hard bounce",
                )

        # Render template if provided
        html_content = message.html_content
        text_content = message.text_content

        if template:
            rendered = self.template_renderer.render(
                template,
                message.template_variables or {}
            )
            html_content = rendered.get("html", html_content)
            text_content = rendered.get("text", text_content)

        # Create full email message
        email_msg = EmailMessage(
            subject=message.subject,
            from_email=message.from_email or self.default_from_email,
            from_name=message.from_name or self.default_from_name,
            reply_to=message.reply_to,
            html_content=html_content,
            text_content=text_content,
            to_recipients=message.to_recipients,
            cc_recipients=message.cc_recipients,
            bcc_recipients=message.bcc_recipients,
            attachments=message.attachments,
            template_id=message.template_id,
            template_variables=message.template_variables,
            track_opens=message.track_opens,
            track_clicks=message.track_clicks,
            tags=message.tags,
            metadata=message.metadata,
            campaign_id=message.campaign_id,
            sequence_id=message.sequence_id,
            sequence_step=message.sequence_step,
        )

        # Inject tracking if enabled
        if email_msg.html_content and (email_msg.track_opens or email_msg.track_clicks):
            email_msg.html_content = self.provider.inject_tracking(
                email_msg.html_content,
                email_msg.tracking_id,
                self.tracking_base_url,
            )

        # Add unsubscribe link if not present
        if email_msg.html_content and 'unsubscribe' not in email_msg.html_content.lower():
            unsubscribe_url = self.unsubscribe_manager.generate_unsubscribe_url(
                email_msg.tracking_id,
                self.tracking_base_url,
            )
            email_msg.html_content = self._inject_unsubscribe_link(
                email_msg.html_content,
                unsubscribe_url,
            )

        # Store message
        self._messages[email_msg.id] = email_msg

        # Send via provider
        response = await self.provider.send_email(email_msg)

        # Update message status
        if response.success:
            email_msg.status = EmailStatus.SENT
            email_msg.sent_at = datetime.utcnow()
            email_msg.provider = self.provider.provider_name
            email_msg.provider_message_id = response.provider_message_id

            # Record tracking
            await self.tracking_service.record_send(email_msg)
        else:
            email_msg.status = EmailStatus.FAILED

        return response

    async def send_batch(
        self,
        messages: List[EmailMessageCreate],
        template: Optional[EmailTemplate] = None,
    ) -> List[SendEmailResponse]:
        """Send multiple emails in batch."""
        import asyncio

        tasks = [self.send_email(msg, template) for msg in messages]
        return await asyncio.gather(*tasks)

    def _inject_unsubscribe_link(
        self,
        html_content: str,
        unsubscribe_url: str,
    ) -> str:
        """Inject unsubscribe link into email HTML."""
        unsubscribe_html = f'''
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>If you no longer wish to receive these emails, you can <a href="{unsubscribe_url}" style="color: #666;">unsubscribe here</a>.</p>
        </div>
        '''

        if '</body>' in html_content.lower():
            import re
            html_content = re.sub(
                r'(</body>)',
                f'{unsubscribe_html}\\1',
                html_content,
                flags=re.IGNORECASE
            )
        else:
            html_content += unsubscribe_html

        return html_content

    async def handle_webhook(
        self,
        provider: EmailProvider,
        payload: WebhookPayload,
    ) -> bool:
        """
        Handle incoming webhook from email provider.

        Args:
            provider: The email provider sending the webhook
            payload: The webhook payload

        Returns:
            True if the webhook was processed successfully
        """
        # Parse the event
        event = self.provider.parse_webhook_event(payload)
        if not event:
            logger.warning("Could not parse webhook event")
            return False

        # Store event
        if event.email_id:
            if event.email_id not in self._events:
                self._events[event.email_id] = []
            self._events[event.email_id].append(event)

        # Update message status
        message = self._messages.get(event.email_id)
        if message:
            await self._update_message_from_event(message, event)

        # Handle specific event types
        if event.event_type == EmailEventType.BOUNCED:
            await self.bounce_handler.handle_bounce(event)

        elif event.event_type == EmailEventType.SPAM_REPORT:
            await self.unsubscribe_manager.handle_spam_report(event)

        elif event.event_type == EmailEventType.UNSUBSCRIBED:
            await self.unsubscribe_manager.handle_unsubscribe_event(event)

        elif event.event_type == EmailEventType.OPENED:
            await self.tracking_service.record_open(event)

        elif event.event_type == EmailEventType.CLICKED:
            await self.tracking_service.record_click(event)

        return True

    async def _update_message_from_event(
        self,
        message: EmailMessage,
        event: EmailEvent,
    ) -> None:
        """Update message status based on event."""
        now = datetime.utcnow()
        message.updated_at = now

        if event.event_type == EmailEventType.DELIVERED:
            message.status = EmailStatus.DELIVERED
            message.delivered_at = now

        elif event.event_type == EmailEventType.OPENED:
            message.open_count += 1
            if not message.opened_at:
                message.status = EmailStatus.OPENED
                message.opened_at = now

        elif event.event_type == EmailEventType.CLICKED:
            message.click_count += 1
            if not message.clicked_at:
                message.status = EmailStatus.CLICKED
                message.clicked_at = now

        elif event.event_type == EmailEventType.BOUNCED:
            message.status = EmailStatus.BOUNCED
            message.bounced_at = now

    async def record_open(
        self,
        tracking_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Record an email open event (from tracking pixel).

        Args:
            tracking_id: The tracking ID from the pixel URL
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            True if the open was recorded
        """
        # Find message by tracking ID
        message = None
        for msg in self._messages.values():
            if msg.tracking_id == tracking_id:
                message = msg
                break

        if not message:
            logger.warning(f"No message found for tracking ID: {tracking_id}")
            return False

        # Create event
        event = EmailEvent(
            event_type=EmailEventType.OPENED,
            email_id=message.id,
            tracking_id=tracking_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Update message
        await self._update_message_from_event(message, event)

        # Record in tracking service
        await self.tracking_service.record_open(event)

        return True

    async def record_click(
        self,
        tracking_id: str,
        link_id: str,
        url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Record an email click event.

        Args:
            tracking_id: The tracking ID
            link_id: The clicked link ID
            url: The original URL
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            True if the click was recorded
        """
        # Find message by tracking ID
        message = None
        for msg in self._messages.values():
            if msg.tracking_id == tracking_id:
                message = msg
                break

        if not message:
            logger.warning(f"No message found for tracking ID: {tracking_id}")
            return False

        # Create event
        event = EmailEvent(
            event_type=EmailEventType.CLICKED,
            email_id=message.id,
            tracking_id=tracking_id,
            link_id=link_id,
            url=url,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Update message
        await self._update_message_from_event(message, event)

        # Record in tracking service
        await self.tracking_service.record_click(event)

        return True

    async def get_message(self, message_id: UUID) -> Optional[EmailMessage]:
        """Get a message by ID."""
        return self._messages.get(message_id)

    async def get_message_events(self, message_id: UUID) -> List[EmailEvent]:
        """Get all events for a message."""
        return self._events.get(message_id, [])

    async def get_message_stats(
        self,
        campaign_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated email statistics.

        Args:
            campaign_id: Optional campaign filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with email statistics
        """
        messages = list(self._messages.values())

        # Apply filters
        if campaign_id:
            messages = [m for m in messages if m.campaign_id == campaign_id]
        if start_date:
            messages = [m for m in messages if m.created_at >= start_date]
        if end_date:
            messages = [m for m in messages if m.created_at <= end_date]

        total = len(messages)
        if total == 0:
            return {
                "total_sent": 0,
                "total_delivered": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "total_bounced": 0,
                "delivery_rate": None,
                "open_rate": None,
                "click_rate": None,
                "bounce_rate": None,
            }

        sent = sum(1 for m in messages if m.status != EmailStatus.PENDING)
        delivered = sum(1 for m in messages if m.delivered_at)
        opened = sum(1 for m in messages if m.opened_at)
        clicked = sum(1 for m in messages if m.clicked_at)
        bounced = sum(1 for m in messages if m.status == EmailStatus.BOUNCED)

        return {
            "total_sent": sent,
            "total_delivered": delivered,
            "total_opened": opened,
            "total_clicked": clicked,
            "total_bounced": bounced,
            "delivery_rate": (delivered / sent * 100) if sent > 0 else None,
            "open_rate": (opened / delivered * 100) if delivered > 0 else None,
            "click_rate": (clicked / opened * 100) if opened > 0 else None,
            "bounce_rate": (bounced / sent * 100) if sent > 0 else None,
        }
