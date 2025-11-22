"""
Email Bounce Handler

Handles processing and management of bounced emails.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from ...models.email import (
    EmailEvent,
    EmailEventType,
    BounceType,
    BounceRecord,
)


logger = logging.getLogger(__name__)


class BounceHandler:
    """
    Handles email bounce processing and management.

    Provides:
    - Bounce event processing
    - Hard/soft bounce classification
    - Retry logic for soft bounces
    - Suppression list management
    """

    # Configuration
    MAX_SOFT_BOUNCE_RETRIES = 3
    SOFT_BOUNCE_RETRY_DELAY = timedelta(hours=24)
    HARD_BOUNCE_SUPPRESSION_DAYS = 365

    def __init__(self):
        """Initialize the bounce handler."""
        # In-memory storage (replace with database in production)
        self._bounce_records: Dict[str, BounceRecord] = {}  # keyed by email
        self._suppression_list: Dict[str, Dict[str, Any]] = {}  # keyed by email

    async def handle_bounce(self, event: EmailEvent) -> BounceRecord:
        """
        Process a bounce event.

        Args:
            event: The bounce event to process

        Returns:
            BounceRecord with bounce details
        """
        email = event.recipient_email
        if not email:
            raise ValueError("Bounce event must have a recipient email")

        bounce_type = event.bounce_type or BounceType.SOFT
        bounce_reason = event.bounce_reason

        # Check for existing bounce record
        existing = self._bounce_records.get(email)

        if existing:
            # Update existing record
            existing.retry_count += 1
            existing.last_retry_at = datetime.utcnow()

            # Upgrade to hard bounce if too many soft bounces
            if (existing.bounce_type == BounceType.SOFT and
                existing.retry_count >= self.MAX_SOFT_BOUNCE_RETRIES):
                logger.info(
                    f"Upgrading {email} to hard bounce after "
                    f"{existing.retry_count} soft bounces"
                )
                existing.bounce_type = BounceType.HARD
                await self._add_to_suppression(email, "repeated_soft_bounce")

            record = existing
        else:
            # Create new bounce record
            record = BounceRecord(
                email=email,
                bounce_type=bounce_type,
                bounce_reason=bounce_reason,
                email_id=event.email_id,
                provider=event.provider,
                bounced_at=event.timestamp or datetime.utcnow(),
            )
            self._bounce_records[email] = record

            # Hard bounces go straight to suppression
            if bounce_type == BounceType.HARD:
                await self._add_to_suppression(email, "hard_bounce")

            # Block bounces also get suppressed
            elif bounce_type == BounceType.BLOCK:
                await self._add_to_suppression(email, "blocked")

        logger.info(
            f"Processed bounce for {email}: type={bounce_type.value}, "
            f"reason={bounce_reason}"
        )

        return record

    async def _add_to_suppression(
        self,
        email: str,
        reason: str,
    ) -> None:
        """Add an email to the local suppression list."""
        self._suppression_list[email] = {
            "email": email,
            "reason": reason,
            "suppressed_at": datetime.utcnow(),
        }
        logger.info(f"Added {email} to suppression list: {reason}")

    async def get_bounce_record(self, email: str) -> Optional[BounceRecord]:
        """Get bounce record for an email address."""
        return self._bounce_records.get(email)

    async def is_suppressed(self, email: str) -> bool:
        """Check if an email address is suppressed due to bounce."""
        return email in self._suppression_list

    async def get_suppression_info(
        self,
        email: str,
    ) -> Optional[Dict[str, Any]]:
        """Get suppression information for an email."""
        return self._suppression_list.get(email)

    async def should_retry(self, email: str) -> bool:
        """
        Check if an email should be retried after a soft bounce.

        Args:
            email: Email address to check

        Returns:
            True if the email can be retried
        """
        record = self._bounce_records.get(email)

        if not record:
            return True

        # Hard bounces should not be retried
        if record.bounce_type == BounceType.HARD:
            return False

        # Check retry count
        if record.retry_count >= self.MAX_SOFT_BOUNCE_RETRIES:
            return False

        # Check retry delay
        if record.last_retry_at:
            next_retry = record.last_retry_at + self.SOFT_BOUNCE_RETRY_DELAY
            if datetime.utcnow() < next_retry:
                return False

        return True

    async def remove_from_suppression(self, email: str) -> bool:
        """
        Remove an email from the suppression list.

        Use with caution - typically only for manual corrections.

        Args:
            email: Email address to remove

        Returns:
            True if removed, False if not found
        """
        if email in self._suppression_list:
            del self._suppression_list[email]
            logger.info(f"Removed {email} from suppression list")
            return True

        if email in self._bounce_records:
            del self._bounce_records[email]
            logger.info(f"Removed bounce record for {email}")
            return True

        return False

    async def get_bounce_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get bounce statistics.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with bounce statistics
        """
        records = list(self._bounce_records.values())

        # Apply date filters
        if start_date:
            records = [r for r in records if r.bounced_at >= start_date]
        if end_date:
            records = [r for r in records if r.bounced_at <= end_date]

        total = len(records)
        hard = sum(1 for r in records if r.bounce_type == BounceType.HARD)
        soft = sum(1 for r in records if r.bounce_type == BounceType.SOFT)
        block = sum(1 for r in records if r.bounce_type == BounceType.BLOCK)

        return {
            "total_bounces": total,
            "hard_bounces": hard,
            "soft_bounces": soft,
            "blocked": block,
            "suppressed_count": len(self._suppression_list),
            "hard_bounce_rate": (hard / total * 100) if total > 0 else 0,
        }

    async def get_bounced_emails(
        self,
        bounce_type: Optional[BounceType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BounceRecord]:
        """
        Get list of bounced email addresses.

        Args:
            bounce_type: Optional filter by bounce type
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of BounceRecord objects
        """
        records = list(self._bounce_records.values())

        if bounce_type:
            records = [r for r in records if r.bounce_type == bounce_type]

        # Sort by most recent first
        records.sort(key=lambda r: r.bounced_at, reverse=True)

        return records[offset:offset + limit]

    async def cleanup_old_soft_bounces(
        self,
        days: int = 30,
    ) -> int:
        """
        Remove old soft bounce records.

        Soft bounces older than specified days can be cleaned up
        to allow retry attempts.

        Args:
            days: Age threshold in days

        Returns:
            Number of records removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        removed = 0

        to_remove = []
        for email, record in self._bounce_records.items():
            if (record.bounce_type == BounceType.SOFT and
                record.bounced_at < cutoff):
                to_remove.append(email)

        for email in to_remove:
            del self._bounce_records[email]
            removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} old soft bounce records")

        return removed

    def classify_bounce(
        self,
        error_code: Optional[str],
        error_message: Optional[str],
    ) -> BounceType:
        """
        Classify a bounce based on error information.

        Args:
            error_code: SMTP error code or provider error code
            error_message: Error message from the provider

        Returns:
            Classified BounceType
        """
        if not error_code and not error_message:
            return BounceType.SOFT

        # Convert to strings for comparison
        code = str(error_code or "").lower()
        message = str(error_message or "").lower()

        # Hard bounce indicators
        hard_bounce_codes = ["550", "551", "552", "553", "554"]
        hard_bounce_terms = [
            "user unknown",
            "mailbox not found",
            "invalid recipient",
            "does not exist",
            "no such user",
            "invalid address",
            "permanent failure",
            "address rejected",
            "recipient rejected",
        ]

        # Block indicators
        block_terms = [
            "blocked",
            "blacklisted",
            "spam",
            "rejected",
            "policy",
            "denied",
        ]

        # Check for hard bounce
        for hb_code in hard_bounce_codes:
            if code.startswith(hb_code):
                return BounceType.HARD

        for term in hard_bounce_terms:
            if term in message:
                return BounceType.HARD

        # Check for block
        for term in block_terms:
            if term in message:
                return BounceType.BLOCK

        # Default to soft bounce
        return BounceType.SOFT
