"""
Base Email Provider Abstract Class

Defines the interface that all email providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

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


class EmailProviderBase(ABC):
    """
    Abstract base class for email providers.

    All email provider implementations (SendGrid, SES, etc.) must inherit
    from this class and implement the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email provider.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self._validate_config()

    @property
    @abstractmethod
    def provider_name(self) -> EmailProvider:
        """Return the provider enum value."""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the provider configuration.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        pass

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> SendEmailResponse:
        """
        Send an email message.

        Args:
            message: The email message to send

        Returns:
            SendEmailResponse with status and provider message ID
        """
        pass

    @abstractmethod
    async def send_batch(
        self, messages: List[EmailMessage]
    ) -> List[SendEmailResponse]:
        """
        Send multiple emails in batch.

        Args:
            messages: List of email messages to send

        Returns:
            List of SendEmailResponse objects
        """
        pass

    @abstractmethod
    async def get_message_status(
        self, provider_message_id: str
    ) -> Optional[EmailStatus]:
        """
        Get the current status of a sent message.

        Args:
            provider_message_id: The provider's message ID

        Returns:
            Current EmailStatus or None if not found
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self, payload: bytes, signature: str, timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify the authenticity of an incoming webhook.

        Args:
            payload: Raw webhook payload bytes
            signature: Signature header from the webhook
            timestamp: Optional timestamp header

        Returns:
            True if the signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook_event(
        self, payload: WebhookPayload
    ) -> Optional[EmailEvent]:
        """
        Parse a webhook payload into an EmailEvent.

        Args:
            payload: The incoming webhook payload

        Returns:
            Parsed EmailEvent or None if not parseable
        """
        pass

    @abstractmethod
    async def add_to_suppression_list(
        self, email: str, reason: str = "bounce"
    ) -> bool:
        """
        Add an email address to the provider's suppression list.

        Args:
            email: Email address to suppress
            reason: Reason for suppression

        Returns:
            True if successfully added
        """
        pass

    @abstractmethod
    async def remove_from_suppression_list(self, email: str) -> bool:
        """
        Remove an email address from the provider's suppression list.

        Args:
            email: Email address to remove

        Returns:
            True if successfully removed
        """
        pass

    @abstractmethod
    async def check_suppression_status(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Check if an email is on the suppression list.

        Args:
            email: Email address to check

        Returns:
            Suppression details or None if not suppressed
        """
        pass

    def generate_tracking_pixel_url(
        self, tracking_id: str, base_url: str
    ) -> str:
        """
        Generate a tracking pixel URL for open tracking.

        Args:
            tracking_id: Unique tracking identifier
            base_url: Base URL for the tracking endpoint

        Returns:
            Complete tracking pixel URL
        """
        return f"{base_url}/api/email/track/open/{tracking_id}"

    def generate_tracked_link(
        self, original_url: str, tracking_id: str, link_id: str, base_url: str
    ) -> str:
        """
        Generate a tracked link URL for click tracking.

        Args:
            original_url: Original destination URL
            tracking_id: Message tracking identifier
            link_id: Unique link identifier
            base_url: Base URL for the tracking endpoint

        Returns:
            Complete tracked link URL
        """
        import urllib.parse

        encoded_url = urllib.parse.quote(original_url, safe='')
        return f"{base_url}/api/email/track/click/{tracking_id}/{link_id}?url={encoded_url}"

    def inject_tracking(
        self, html_content: str, tracking_id: str, base_url: str
    ) -> str:
        """
        Inject tracking pixel and convert links for tracking.

        Args:
            html_content: Original HTML content
            tracking_id: Message tracking identifier
            base_url: Base URL for tracking endpoints

        Returns:
            Modified HTML with tracking enabled
        """
        import re
        from uuid import uuid4

        # Inject tracking pixel before </body>
        tracking_pixel = f'<img src="{self.generate_tracking_pixel_url(tracking_id, base_url)}" width="1" height="1" style="display:none" alt="" />'

        if '</body>' in html_content.lower():
            html_content = re.sub(
                r'(</body>)',
                f'{tracking_pixel}\\1',
                html_content,
                flags=re.IGNORECASE
            )
        else:
            html_content += tracking_pixel

        # Convert links for click tracking
        def replace_link(match):
            original_url = match.group(1)
            # Skip tracking for unsubscribe links and mailto:
            if 'unsubscribe' in original_url.lower() or original_url.startswith('mailto:'):
                return match.group(0)
            link_id = str(uuid4())
            tracked_url = self.generate_tracked_link(
                original_url, tracking_id, link_id, base_url
            )
            return f'href="{tracked_url}"'

        html_content = re.sub(
            r'href=["\']([^"\']+)["\']',
            replace_link,
            html_content
        )

        return html_content

    def _map_event_type(self, provider_event: str) -> Optional[EmailEventType]:
        """
        Map provider-specific event type to standard EmailEventType.

        Override in subclasses for provider-specific mappings.
        """
        event_mapping = {
            'sent': EmailEventType.SENT,
            'delivered': EmailEventType.DELIVERED,
            'opened': EmailEventType.OPENED,
            'open': EmailEventType.OPENED,
            'clicked': EmailEventType.CLICKED,
            'click': EmailEventType.CLICKED,
            'bounced': EmailEventType.BOUNCED,
            'bounce': EmailEventType.BOUNCED,
            'dropped': EmailEventType.DROPPED,
            'drop': EmailEventType.DROPPED,
            'spamreport': EmailEventType.SPAM_REPORT,
            'spam': EmailEventType.SPAM_REPORT,
            'complaint': EmailEventType.SPAM_REPORT,
            'unsubscribe': EmailEventType.UNSUBSCRIBED,
            'unsubscribed': EmailEventType.UNSUBSCRIBED,
            'deferred': EmailEventType.DEFERRED,
        }
        return event_mapping.get(provider_event.lower())

    def _map_bounce_type(self, provider_bounce_type: str) -> BounceType:
        """
        Map provider-specific bounce type to standard BounceType.

        Override in subclasses for provider-specific mappings.
        """
        bounce_mapping = {
            'hard': BounceType.HARD,
            'permanent': BounceType.HARD,
            'soft': BounceType.SOFT,
            'transient': BounceType.SOFT,
            'temporary': BounceType.SOFT,
            'block': BounceType.BLOCK,
            'blocked': BounceType.BLOCK,
        }
        return bounce_mapping.get(provider_bounce_type.lower(), BounceType.SOFT)
