"""
Email Tracking Service

Handles open and click tracking for emails.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from ...models.email import (
    EmailMessage,
    EmailEvent,
    EmailEventType,
    EmailStatsResponse,
)


logger = logging.getLogger(__name__)


class TrackingService:
    """
    Service for tracking email opens and clicks.

    Provides:
    - Recording of open/click events
    - Aggregated statistics
    - Time-series analytics
    - Deduplication of events
    """

    def __init__(self):
        """Initialize the tracking service."""
        # In-memory storage (replace with database in production)
        self._events: Dict[UUID, List[EmailEvent]] = defaultdict(list)
        self._open_tracking: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._click_tracking: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Deduplication windows (to avoid counting same user multiple times)
        self._dedup_window_opens = timedelta(hours=1)
        self._dedup_window_clicks = timedelta(minutes=5)

    async def record_send(self, message: EmailMessage) -> None:
        """
        Record that an email was sent.

        Args:
            message: The sent email message
        """
        event = EmailEvent(
            event_type=EmailEventType.SENT,
            email_id=message.id,
            tracking_id=message.tracking_id,
            timestamp=datetime.utcnow(),
        )
        self._events[message.id].append(event)

        logger.info(
            f"Recorded send event for message {message.id}, "
            f"tracking_id={message.tracking_id}"
        )

    async def record_open(
        self,
        event: EmailEvent,
    ) -> bool:
        """
        Record an email open event.

        Args:
            event: The open event to record

        Returns:
            True if this is a unique open, False if deduplicated
        """
        tracking_id = event.tracking_id

        # Check for duplicate opens from same IP/UA in dedup window
        if not self._is_unique_open(event):
            logger.debug(f"Deduplicated open event for {tracking_id}")
            return False

        # Store event
        if event.email_id:
            self._events[event.email_id].append(event)

        # Store detailed tracking data
        self._open_tracking[tracking_id].append({
            "timestamp": event.timestamp or datetime.utcnow(),
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
        })

        logger.info(
            f"Recorded open event for tracking_id={tracking_id}, "
            f"ip={event.ip_address}"
        )
        return True

    async def record_click(
        self,
        event: EmailEvent,
    ) -> bool:
        """
        Record an email click event.

        Args:
            event: The click event to record

        Returns:
            True if recorded, False if deduplicated
        """
        tracking_id = event.tracking_id

        # Check for duplicate clicks on same link from same user
        if not self._is_unique_click(event):
            logger.debug(f"Deduplicated click event for {tracking_id}")
            return False

        # Store event
        if event.email_id:
            self._events[event.email_id].append(event)

        # Store detailed tracking data
        self._click_tracking[tracking_id].append({
            "timestamp": event.timestamp or datetime.utcnow(),
            "link_id": event.link_id,
            "url": event.url,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
        })

        logger.info(
            f"Recorded click event for tracking_id={tracking_id}, "
            f"link_id={event.link_id}, url={event.url}"
        )
        return True

    def _is_unique_open(self, event: EmailEvent) -> bool:
        """Check if an open event is unique (not a duplicate)."""
        tracking_id = event.tracking_id
        existing = self._open_tracking.get(tracking_id, [])

        if not existing:
            return True

        now = event.timestamp or datetime.utcnow()
        cutoff = now - self._dedup_window_opens

        for prev in existing:
            if prev["timestamp"] > cutoff:
                # Same IP and user agent within window = duplicate
                if (prev["ip_address"] == event.ip_address and
                    prev["user_agent"] == event.user_agent):
                    return False

        return True

    def _is_unique_click(self, event: EmailEvent) -> bool:
        """Check if a click event is unique."""
        tracking_id = event.tracking_id
        existing = self._click_tracking.get(tracking_id, [])

        if not existing:
            return True

        now = event.timestamp or datetime.utcnow()
        cutoff = now - self._dedup_window_clicks

        for prev in existing:
            if prev["timestamp"] > cutoff:
                # Same link, IP, and user agent within window = duplicate
                if (prev["link_id"] == event.link_id and
                    prev["ip_address"] == event.ip_address and
                    prev["user_agent"] == event.user_agent):
                    return False

        return True

    async def get_message_events(
        self,
        message_id: UUID,
    ) -> List[EmailEvent]:
        """Get all tracking events for a message."""
        return self._events.get(message_id, [])

    async def get_tracking_data(
        self,
        tracking_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed tracking data for a message.

        Args:
            tracking_id: The tracking identifier

        Returns:
            Dictionary with opens, clicks, and statistics
        """
        opens = self._open_tracking.get(tracking_id, [])
        clicks = self._click_tracking.get(tracking_id, [])

        # Aggregate click data by URL
        clicks_by_url: Dict[str, int] = defaultdict(int)
        for click in clicks:
            if click.get("url"):
                clicks_by_url[click["url"]] += 1

        return {
            "tracking_id": tracking_id,
            "total_opens": len(opens),
            "unique_opens": len(set(o.get("ip_address") for o in opens)),
            "total_clicks": len(clicks),
            "unique_clicks": len(set(c.get("ip_address") for c in clicks)),
            "first_open": opens[0]["timestamp"] if opens else None,
            "last_open": opens[-1]["timestamp"] if opens else None,
            "first_click": clicks[0]["timestamp"] if clicks else None,
            "clicks_by_url": dict(clicks_by_url),
            "open_events": opens,
            "click_events": clicks,
        }

    async def get_stats(
        self,
        message_ids: Optional[List[UUID]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> EmailStatsResponse:
        """
        Get aggregated tracking statistics.

        Args:
            message_ids: Optional list of message IDs to filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            EmailStatsResponse with aggregated statistics
        """
        # Gather all events
        all_events = []
        target_ids = message_ids if message_ids else list(self._events.keys())

        for msg_id in target_ids:
            events = self._events.get(msg_id, [])
            for event in events:
                # Apply date filters
                if start_date and event.timestamp and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp and event.timestamp > end_date:
                    continue
                all_events.append(event)

        # Count by type
        sent = sum(1 for e in all_events if e.event_type == EmailEventType.SENT)
        delivered = sum(1 for e in all_events if e.event_type == EmailEventType.DELIVERED)
        opened = sum(1 for e in all_events if e.event_type == EmailEventType.OPENED)
        clicked = sum(1 for e in all_events if e.event_type == EmailEventType.CLICKED)
        bounced = sum(1 for e in all_events if e.event_type == EmailEventType.BOUNCED)
        unsubscribed = sum(1 for e in all_events if e.event_type == EmailEventType.UNSUBSCRIBED)

        # Calculate rates
        delivery_rate = (delivered / sent * 100) if sent > 0 else None
        open_rate = (opened / delivered * 100) if delivered > 0 else None
        click_rate = (clicked / opened * 100) if opened > 0 else None
        bounce_rate = (bounced / sent * 100) if sent > 0 else None

        return EmailStatsResponse(
            total_sent=sent,
            total_delivered=delivered,
            total_opened=opened,
            total_clicked=clicked,
            total_bounced=bounced,
            total_unsubscribed=unsubscribed,
            delivery_rate=delivery_rate,
            open_rate=open_rate,
            click_rate=click_rate,
            bounce_rate=bounce_rate,
        )

    async def get_time_series(
        self,
        tracking_id: Optional[str] = None,
        interval: str = "day",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get time-series tracking data.

        Args:
            tracking_id: Optional specific tracking ID
            interval: Time interval ("hour", "day", "week")
            start_date: Start date for the series
            end_date: End date for the series

        Returns:
            Time-series data for opens and clicks
        """
        # Determine time buckets based on interval
        if interval == "hour":
            bucket_format = "%Y-%m-%d %H:00"
            bucket_delta = timedelta(hours=1)
        elif interval == "week":
            bucket_format = "%Y-W%W"
            bucket_delta = timedelta(weeks=1)
        else:  # day
            bucket_format = "%Y-%m-%d"
            bucket_delta = timedelta(days=1)

        # Initialize series
        opens_series: Dict[str, int] = defaultdict(int)
        clicks_series: Dict[str, int] = defaultdict(int)

        # Aggregate data
        if tracking_id:
            open_data = self._open_tracking.get(tracking_id, [])
            click_data = self._click_tracking.get(tracking_id, [])
        else:
            open_data = [o for opens in self._open_tracking.values() for o in opens]
            click_data = [c for clicks in self._click_tracking.values() for c in clicks]

        for open_event in open_data:
            ts = open_event.get("timestamp")
            if ts:
                if start_date and ts < start_date:
                    continue
                if end_date and ts > end_date:
                    continue
                bucket = ts.strftime(bucket_format)
                opens_series[bucket] += 1

        for click_event in click_data:
            ts = click_event.get("timestamp")
            if ts:
                if start_date and ts < start_date:
                    continue
                if end_date and ts > end_date:
                    continue
                bucket = ts.strftime(bucket_format)
                clicks_series[bucket] += 1

        # Convert to sorted lists
        all_buckets = sorted(set(opens_series.keys()) | set(clicks_series.keys()))

        return {
            "opens": [
                {"time": b, "count": opens_series.get(b, 0)}
                for b in all_buckets
            ],
            "clicks": [
                {"time": b, "count": clicks_series.get(b, 0)}
                for b in all_buckets
            ],
        }

    def generate_tracking_pixel(self, tracking_id: str, base_url: str) -> str:
        """
        Generate HTML for a tracking pixel.

        Args:
            tracking_id: The tracking identifier
            base_url: Base URL for the tracking endpoint

        Returns:
            HTML img tag for the tracking pixel
        """
        url = f"{base_url}/api/email/track/open/{tracking_id}"
        return (
            f'<img src="{url}" width="1" height="1" '
            f'style="display:none" alt="" />'
        )

    def wrap_link_for_tracking(
        self,
        original_url: str,
        tracking_id: str,
        link_id: str,
        base_url: str,
    ) -> str:
        """
        Generate a tracked link URL.

        Args:
            original_url: Original destination URL
            tracking_id: Message tracking identifier
            link_id: Unique link identifier
            base_url: Base URL for the tracking endpoint

        Returns:
            Tracked link URL
        """
        import urllib.parse

        encoded_url = urllib.parse.quote(original_url, safe='')
        return f"{base_url}/api/email/track/click/{tracking_id}/{link_id}?url={encoded_url}"
