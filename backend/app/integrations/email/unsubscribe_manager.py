"""
Email Unsubscribe Manager

Handles unsubscribe requests and compliance management.
"""

import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4

from ...models.email import (
    EmailEvent,
    EmailEventType,
    Unsubscribe,
    UnsubscribeCreate,
    UnsubscribeReason,
)


logger = logging.getLogger(__name__)


class UnsubscribeManager:
    """
    Manages email unsubscribe functionality.

    Provides:
    - Unsubscribe link generation with secure tokens
    - Unsubscribe processing
    - Resubscribe handling
    - Compliance tracking (CAN-SPAM, GDPR)
    """

    def __init__(self, secret_key: str = "change-me-in-production"):
        """
        Initialize the unsubscribe manager.

        Args:
            secret_key: Secret key for generating secure unsubscribe tokens
        """
        self.secret_key = secret_key

        # In-memory storage (replace with database in production)
        self._unsubscribes: Dict[str, Unsubscribe] = {}  # keyed by email
        self._tokens: Dict[str, str] = {}  # token -> email mapping

    def generate_unsubscribe_url(
        self,
        tracking_id: str,
        base_url: str,
        email: Optional[str] = None,
        list_id: Optional[str] = None,
    ) -> str:
        """
        Generate a secure unsubscribe URL.

        Args:
            tracking_id: Message tracking identifier
            base_url: Base URL for the unsubscribe endpoint
            email: Optional email address (for pre-filled form)
            list_id: Optional specific list to unsubscribe from

        Returns:
            Complete unsubscribe URL with secure token
        """
        # Generate secure token
        token = self._generate_token(tracking_id, email)

        url = f"{base_url}/api/email/unsubscribe/{tracking_id}?token={token}"

        if list_id:
            url += f"&list={list_id}"

        return url

    def _generate_token(
        self,
        tracking_id: str,
        email: Optional[str] = None,
    ) -> str:
        """Generate a secure token for unsubscribe verification."""
        data = f"{tracking_id}:{email or ''}"
        signature = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:32]

        # Store mapping for verification
        self._tokens[signature] = data

        return signature

    def verify_token(
        self,
        tracking_id: str,
        token: str,
        email: Optional[str] = None,
    ) -> bool:
        """
        Verify an unsubscribe token.

        Args:
            tracking_id: Message tracking identifier
            token: The token to verify
            email: Optional email for additional verification

        Returns:
            True if the token is valid
        """
        expected_data = f"{tracking_id}:{email or ''}"
        expected_token = hmac.new(
            self.secret_key.encode(),
            expected_data.encode(),
            hashlib.sha256
        ).hexdigest()[:32]

        return hmac.compare_digest(token, expected_token)

    async def process_unsubscribe(
        self,
        request: UnsubscribeCreate,
    ) -> Unsubscribe:
        """
        Process an unsubscribe request.

        Args:
            request: Unsubscribe request details

        Returns:
            Created Unsubscribe record
        """
        email = request.email.lower()

        # Check if already unsubscribed
        existing = self._unsubscribes.get(email)
        if existing and not existing.resubscribed:
            logger.info(f"{email} is already unsubscribed")
            return existing

        # Create unsubscribe record
        unsub = Unsubscribe(
            email=email,
            reason=request.reason,
            global_unsubscribe=request.global_unsubscribe,
            list_ids=request.list_ids,
            campaign_id=request.campaign_id,
            source_email_id=request.source_email_id,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
        )

        self._unsubscribes[email] = unsub

        logger.info(
            f"Processed unsubscribe for {email}: "
            f"reason={request.reason.value}, global={request.global_unsubscribe}"
        )

        return unsub

    async def handle_unsubscribe_event(self, event: EmailEvent) -> None:
        """
        Handle an unsubscribe event from a webhook.

        Args:
            event: The unsubscribe event
        """
        email = event.recipient_email
        if not email:
            logger.warning("Unsubscribe event without email address")
            return

        request = UnsubscribeCreate(
            email=email,
            reason=UnsubscribeReason.USER_REQUEST,
            global_unsubscribe=True,
            source_email_id=event.email_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
        )

        await self.process_unsubscribe(request)

    async def handle_spam_report(self, event: EmailEvent) -> None:
        """
        Handle a spam report event.

        Spam reports should result in immediate unsubscribe.

        Args:
            event: The spam report event
        """
        email = event.recipient_email
        if not email:
            logger.warning("Spam report event without email address")
            return

        request = UnsubscribeCreate(
            email=email,
            reason=UnsubscribeReason.SPAM_COMPLAINT,
            global_unsubscribe=True,
            source_email_id=event.email_id,
            ip_address=event.ip_address,
        )

        await self.process_unsubscribe(request)

        logger.warning(f"Spam complaint from {email} - added to global unsubscribe")

    async def is_unsubscribed(
        self,
        email: str,
        list_id: Optional[str] = None,
        campaign_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if an email is unsubscribed.

        Args:
            email: Email address to check
            list_id: Optional specific list to check
            campaign_id: Optional specific campaign to check

        Returns:
            True if the email should not receive emails
        """
        email = email.lower()
        unsub = self._unsubscribes.get(email)

        if not unsub:
            return False

        # If resubscribed, they're not unsubscribed
        if unsub.resubscribed:
            return False

        # Global unsubscribe covers everything
        if unsub.global_unsubscribe:
            return True

        # Check specific list
        if list_id and unsub.list_ids:
            if list_id in unsub.list_ids:
                return True

        # Check specific campaign
        if campaign_id and unsub.campaign_id:
            if campaign_id == unsub.campaign_id:
                return True

        return False

    async def process_resubscribe(
        self,
        email: str,
        list_id: Optional[str] = None,
    ) -> bool:
        """
        Process a resubscribe request.

        Args:
            email: Email address to resubscribe
            list_id: Optional specific list to resubscribe to

        Returns:
            True if successfully resubscribed
        """
        email = email.lower()
        unsub = self._unsubscribes.get(email)

        if not unsub:
            return True  # Not unsubscribed, nothing to do

        # Can't resubscribe from spam complaints
        if unsub.reason == UnsubscribeReason.SPAM_COMPLAINT:
            logger.warning(
                f"Cannot resubscribe {email} - was a spam complaint"
            )
            return False

        # Handle list-specific resubscribe
        if list_id and unsub.list_ids:
            if list_id in unsub.list_ids:
                unsub.list_ids.remove(list_id)
                if not unsub.list_ids and not unsub.global_unsubscribe:
                    unsub.resubscribed = True
                    unsub.resubscribed_at = datetime.utcnow()
                logger.info(f"Resubscribed {email} to list {list_id}")
                return True
        else:
            # Global resubscribe
            unsub.resubscribed = True
            unsub.resubscribed_at = datetime.utcnow()
            logger.info(f"Globally resubscribed {email}")
            return True

        return False

    async def get_unsubscribe_record(
        self,
        email: str,
    ) -> Optional[Unsubscribe]:
        """Get unsubscribe record for an email."""
        return self._unsubscribes.get(email.lower())

    async def get_unsubscribe_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get unsubscribe statistics.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with unsubscribe statistics
        """
        records = list(self._unsubscribes.values())

        # Apply date filters
        if start_date:
            records = [r for r in records if r.created_at >= start_date]
        if end_date:
            records = [r for r in records if r.created_at <= end_date]

        total = len(records)
        user_requests = sum(
            1 for r in records if r.reason == UnsubscribeReason.USER_REQUEST
        )
        spam_complaints = sum(
            1 for r in records if r.reason == UnsubscribeReason.SPAM_COMPLAINT
        )
        bounces = sum(
            1 for r in records if r.reason == UnsubscribeReason.BOUNCE
        )
        resubscribed = sum(1 for r in records if r.resubscribed)

        return {
            "total_unsubscribes": total,
            "user_requests": user_requests,
            "spam_complaints": spam_complaints,
            "from_bounces": bounces,
            "resubscribed": resubscribed,
            "active_unsubscribes": total - resubscribed,
        }

    async def get_unsubscribed_emails(
        self,
        reason: Optional[UnsubscribeReason] = None,
        include_resubscribed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Unsubscribe]:
        """
        Get list of unsubscribed emails.

        Args:
            reason: Optional filter by reason
            include_resubscribed: Include resubscribed emails
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of Unsubscribe records
        """
        records = list(self._unsubscribes.values())

        if reason:
            records = [r for r in records if r.reason == reason]

        if not include_resubscribed:
            records = [r for r in records if not r.resubscribed]

        # Sort by most recent first
        records.sort(key=lambda r: r.created_at, reverse=True)

        return records[offset:offset + limit]

    async def export_suppression_list(self) -> List[Dict[str, Any]]:
        """
        Export the suppression list for compliance.

        Returns:
            List of suppressed email records
        """
        return [
            {
                "email": unsub.email,
                "reason": unsub.reason.value,
                "unsubscribed_at": unsub.created_at.isoformat(),
                "global": unsub.global_unsubscribe,
                "resubscribed": unsub.resubscribed,
            }
            for unsub in self._unsubscribes.values()
            if not unsub.resubscribed
        ]

    def generate_list_unsubscribe_header(
        self,
        tracking_id: str,
        base_url: str,
        email: str,
    ) -> str:
        """
        Generate List-Unsubscribe header value for email compliance.

        Args:
            tracking_id: Message tracking identifier
            base_url: Base URL for unsubscribe endpoint
            email: Recipient email

        Returns:
            Header value for List-Unsubscribe
        """
        unsub_url = self.generate_unsubscribe_url(tracking_id, base_url, email)
        # RFC 8058 one-click unsubscribe
        return f"<{unsub_url}>, <mailto:unsubscribe@{base_url.split('//')[1]}?subject=unsubscribe&body={tracking_id}>"

    def generate_one_click_unsubscribe_header(
        self,
        tracking_id: str,
        base_url: str,
    ) -> str:
        """
        Generate List-Unsubscribe-Post header for one-click unsubscribe.

        Required by Gmail and other major providers.

        Returns:
            Header value for List-Unsubscribe-Post
        """
        return "List-Unsubscribe=One-Click"
