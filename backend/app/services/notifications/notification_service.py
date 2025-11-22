"""
Core notification service for Sales OS.

This module provides the main service class for managing notifications,
including creating, reading, updating, and delivering notifications
through various channels.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.notification import (
    Notification,
    NotificationPreference,
    NotificationDigestQueue,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    UnreadCountResponse,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for managing notifications.

    Handles creation, retrieval, updates, and delivery of notifications
    to users through various channels (in-app, email, WebSocket).
    """

    def __init__(
        self,
        db: AsyncSession,
        websocket_manager: Optional["WebSocketManager"] = None,
        email_service: Optional["EmailNotificationService"] = None,
    ):
        """
        Initialize the notification service.

        Args:
            db: Async database session
            websocket_manager: Optional WebSocket manager for real-time delivery
            email_service: Optional email service for email notifications
        """
        self.db = db
        self.websocket_manager = websocket_manager
        self.email_service = email_service

    async def create_notification(
        self,
        notification_data: NotificationCreate,
        send_realtime: bool = True,
    ) -> NotificationResponse:
        """
        Create a new notification and optionally send it in real-time.

        Args:
            notification_data: The notification data to create
            send_realtime: Whether to send via WebSocket immediately

        Returns:
            The created notification response

        Raises:
            ValueError: If the notification already exists (duplicate idempotency key)
        """
        # Check for duplicate using idempotency key
        if notification_data.idempotency_key:
            existing = await self._get_by_idempotency_key(notification_data.idempotency_key)
            if existing:
                logger.info(
                    f"Duplicate notification detected with key: {notification_data.idempotency_key}"
                )
                return NotificationResponse.model_validate(existing)

        # Check user preferences
        preferences = await self.get_user_preferences(
            notification_data.user_id, notification_data.type
        )

        # Determine which channels to use based on preferences
        channels_to_use = self._get_enabled_channels(preferences, notification_data.channel)

        if not channels_to_use:
            logger.info(
                f"All channels disabled for user {notification_data.user_id}, "
                f"notification type {notification_data.type}"
            )
            # Still create the notification but mark as archived
            notification_data_dict = notification_data.model_dump()
            notification_data_dict["status"] = NotificationStatus.ARCHIVED
            notification = Notification(**notification_data_dict)
            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)
            return NotificationResponse.model_validate(notification)

        # Create the notification
        notification = Notification(**notification_data.model_dump())
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        response = NotificationResponse.model_validate(notification)

        # Deliver through enabled channels
        await self._deliver_notification(response, channels_to_use, send_realtime)

        return response

    async def _deliver_notification(
        self,
        notification: NotificationResponse,
        channels: List[NotificationChannel],
        send_realtime: bool,
    ) -> None:
        """
        Deliver a notification through the specified channels.

        Args:
            notification: The notification to deliver
            channels: List of channels to deliver through
            send_realtime: Whether to send via WebSocket immediately
        """
        for channel in channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    # In-app notifications are stored and fetched on demand
                    await self._update_status(notification.id, NotificationStatus.DELIVERED)

                elif channel == NotificationChannel.WEBSOCKET and send_realtime:
                    if self.websocket_manager:
                        await self.websocket_manager.send_notification(
                            str(notification.user_id), notification
                        )
                        await self._update_status(notification.id, NotificationStatus.DELIVERED)

                elif channel == NotificationChannel.EMAIL_INSTANT:
                    if self.email_service:
                        await self.email_service.send_instant_notification(notification)
                        await self._update_status(notification.id, NotificationStatus.SENT)

                elif channel == NotificationChannel.EMAIL_DIGEST:
                    # Queue for digest
                    await self._queue_for_digest(notification)

            except Exception as e:
                logger.error(f"Failed to deliver notification via {channel}: {e}")
                await self._update_status(notification.id, NotificationStatus.FAILED)

    async def _queue_for_digest(self, notification: NotificationResponse) -> None:
        """Queue a notification for email digest delivery."""
        # Get user's digest preferences
        preferences = await self.get_user_preferences(
            notification.user_id, notification.type, NotificationChannel.EMAIL_DIGEST
        )

        if not preferences:
            return

        pref = preferences[0]
        frequency = pref.digest_frequency or "daily"

        # Calculate next scheduled digest time
        scheduled_for = self._calculate_next_digest_time(
            frequency, pref.digest_time, pref.digest_timezone
        )

        queue_entry = NotificationDigestQueue(
            user_id=notification.user_id,
            notification_id=notification.id,
            digest_frequency=frequency,
            scheduled_for=scheduled_for,
        )
        self.db.add(queue_entry)
        await self.db.commit()

    def _calculate_next_digest_time(
        self, frequency: str, time_str: Optional[str], timezone: Optional[str]
    ) -> datetime:
        """Calculate the next scheduled digest time based on frequency."""
        now = datetime.utcnow()

        if frequency == "daily":
            next_time = now + timedelta(days=1)
        elif frequency == "weekly":
            # Next Monday
            days_until_monday = (7 - now.weekday()) % 7 or 7
            next_time = now + timedelta(days=days_until_monday)
        elif frequency == "monthly":
            # First of next month
            if now.month == 12:
                next_time = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_time = now.replace(month=now.month + 1, day=1)
        else:
            next_time = now + timedelta(days=1)

        # Apply time if specified
        if time_str:
            try:
                hour, minute = map(int, time_str.split(":"))
                next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                pass

        return next_time

    def _get_enabled_channels(
        self,
        preferences: List[NotificationPreference],
        default_channel: NotificationChannel,
    ) -> List[NotificationChannel]:
        """
        Get the list of enabled channels based on user preferences.

        Args:
            preferences: List of user preferences for the notification type
            default_channel: The default channel if no preferences exist

        Returns:
            List of enabled channels
        """
        if not preferences:
            # Default: in-app and websocket
            return [NotificationChannel.IN_APP, NotificationChannel.WEBSOCKET]

        enabled_channels = []
        for pref in preferences:
            if pref.enabled:
                enabled_channels.append(pref.channel)

        return enabled_channels

    async def _get_by_idempotency_key(self, key: str) -> Optional[Notification]:
        """Get a notification by its idempotency key."""
        result = await self.db.execute(
            select(Notification).where(Notification.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def _update_status(self, notification_id: UUID, status: NotificationStatus) -> None:
        """Update the status of a notification."""
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def get_notification(
        self, notification_id: UUID, user_id: UUID
    ) -> Optional[NotificationResponse]:
        """
        Get a single notification by ID.

        Args:
            notification_id: The notification ID
            user_id: The user ID (for authorization)

        Returns:
            The notification if found and authorized, None otherwise
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            return NotificationResponse.model_validate(notification)
        return None

    async def get_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        priority: Optional[NotificationPriority] = None,
    ) -> NotificationListResponse:
        """
        Get a paginated list of notifications for a user.

        Args:
            user_id: The user ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            notification_type: Optional filter by type
            is_read: Optional filter by read status
            priority: Optional filter by priority

        Returns:
            Paginated list of notifications
        """
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        # Apply filters
        if notification_type:
            query = query.where(Notification.type == notification_type)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if priority:
            query = query.where(Notification.priority == priority)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return NotificationListResponse(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(notifications)) < total,
        )

    async def get_unread_count(self, user_id: UUID) -> UnreadCountResponse:
        """
        Get the count of unread notifications for a user.

        Args:
            user_id: The user ID

        Returns:
            Unread count response with total and breakdown by type
        """
        # Total unread count
        total_query = select(func.count()).where(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        # Count by type
        by_type_query = (
            select(Notification.type, func.count())
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
            .group_by(Notification.type)
        )
        by_type_result = await self.db.execute(by_type_query)
        by_type = {str(row[0].value): row[1] for row in by_type_result.all()}

        return UnreadCountResponse(count=total, by_type=by_type)

    async def mark_as_read(self, notification_ids: List[UUID], user_id: UUID) -> int:
        """
        Mark specific notifications as read.

        Args:
            notification_ids: List of notification IDs to mark as read
            user_id: The user ID (for authorization)

        Returns:
            Number of notifications marked as read
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            .values(is_read=True, read_at=now, status=NotificationStatus.READ, updated_at=now)
        )
        await self.db.commit()
        return result.rowcount

    async def mark_all_as_read(
        self,
        user_id: UUID,
        before_date: Optional[datetime] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: The user ID
            before_date: Optional cutoff date
            notification_type: Optional filter by type

        Returns:
            Number of notifications marked as read
        """
        now = datetime.utcnow()
        query = update(Notification).where(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        )

        if before_date:
            query = query.where(Notification.created_at <= before_date)
        if notification_type:
            query = query.where(Notification.type == notification_type)

        result = await self.db.execute(
            query.values(is_read=True, read_at=now, status=NotificationStatus.READ, updated_at=now)
        )
        await self.db.commit()
        return result.rowcount

    async def archive_notifications(self, notification_ids: List[UUID], user_id: UUID) -> int:
        """
        Archive notifications (hide from main view).

        Args:
            notification_ids: List of notification IDs to archive
            user_id: The user ID (for authorization)

        Returns:
            Number of notifications archived
        """
        result = await self.db.execute(
            update(Notification)
            .where(
                and_(Notification.id.in_(notification_ids), Notification.user_id == user_id)
            )
            .values(status=NotificationStatus.ARCHIVED, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: The notification ID
            user_id: The user ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        return False

    # =========================================================================
    # User Preferences
    # =========================================================================

    async def get_user_preferences(
        self,
        user_id: UUID,
        notification_type: Optional[NotificationType] = None,
        channel: Optional[NotificationChannel] = None,
    ) -> List[NotificationPreference]:
        """
        Get notification preferences for a user.

        Args:
            user_id: The user ID
            notification_type: Optional filter by notification type
            channel: Optional filter by channel

        Returns:
            List of notification preferences
        """
        query = select(NotificationPreference).where(NotificationPreference.user_id == user_id)

        if notification_type:
            query = query.where(NotificationPreference.notification_type == notification_type)
        if channel:
            query = query.where(NotificationPreference.channel == channel)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_preferences(self, user_id: UUID) -> List[NotificationPreferenceResponse]:
        """
        Get all notification preferences for a user, including defaults.

        Returns a complete preference matrix for all notification types and channels.
        """
        existing = await self.get_user_preferences(user_id)
        existing_map = {(p.notification_type, p.channel): p for p in existing}

        all_preferences = []

        # Generate complete preference matrix
        for ntype in NotificationType:
            for channel in NotificationChannel:
                key = (ntype, channel)
                if key in existing_map:
                    all_preferences.append(
                        NotificationPreferenceResponse.model_validate(existing_map[key])
                    )
                else:
                    # Create default preference
                    default_enabled = channel in [
                        NotificationChannel.IN_APP,
                        NotificationChannel.WEBSOCKET,
                    ]
                    all_preferences.append(
                        NotificationPreferenceResponse(
                            id=None,
                            user_id=user_id,
                            notification_type=ntype,
                            channel=channel,
                            enabled=default_enabled,
                            digest_frequency=None,
                            digest_time=None,
                            digest_timezone=None,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                    )

        return all_preferences

    async def update_preference(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        enabled: bool,
        digest_frequency: Optional[str] = None,
        digest_time: Optional[str] = None,
        digest_timezone: Optional[str] = None,
    ) -> NotificationPreferenceResponse:
        """
        Update or create a notification preference.

        Args:
            user_id: The user ID
            notification_type: The notification type
            channel: The notification channel
            enabled: Whether the channel is enabled
            digest_frequency: Digest frequency (for email digest)
            digest_time: Digest time (for email digest)
            digest_timezone: Digest timezone (for email digest)

        Returns:
            The updated preference
        """
        # Check if preference exists
        result = await self.db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type,
                    NotificationPreference.channel == channel,
                )
            )
        )
        preference = result.scalar_one_or_none()

        if preference:
            # Update existing
            preference.enabled = enabled
            if digest_frequency is not None:
                preference.digest_frequency = digest_frequency
            if digest_time is not None:
                preference.digest_time = digest_time
            if digest_timezone is not None:
                preference.digest_timezone = digest_timezone
            preference.updated_at = datetime.utcnow()
        else:
            # Create new
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                enabled=enabled,
                digest_frequency=digest_frequency,
                digest_time=digest_time,
                digest_timezone=digest_timezone,
            )
            self.db.add(preference)

        await self.db.commit()
        await self.db.refresh(preference)

        return NotificationPreferenceResponse.model_validate(preference)

    async def bulk_update_preferences(
        self, user_id: UUID, preferences: List[NotificationPreferenceCreate]
    ) -> List[NotificationPreferenceResponse]:
        """
        Bulk update notification preferences.

        Args:
            user_id: The user ID
            preferences: List of preferences to update

        Returns:
            List of updated preferences
        """
        results = []
        for pref in preferences:
            result = await self.update_preference(
                user_id=user_id,
                notification_type=pref.notification_type,
                channel=pref.channel,
                enabled=pref.enabled,
                digest_frequency=pref.digest_frequency,
                digest_time=pref.digest_time,
                digest_timezone=pref.digest_timezone,
            )
            results.append(result)
        return results

    # =========================================================================
    # Event-Driven Notification Creation
    # =========================================================================

    async def notify_transcript_processed(
        self,
        user_id: UUID,
        organization_id: UUID,
        transcript_id: UUID,
        transcript_title: str,
    ) -> NotificationResponse:
        """Create notification when a transcript has been processed."""
        return await self.create_notification(
            NotificationCreate(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.TRANSCRIPT_PROCESSED,
                title="Transcript Processed",
                body=f'Your transcript "{transcript_title}" has been processed and is ready for review.',
                priority=NotificationPriority.NORMAL,
                entity_type="transcript",
                entity_id=transcript_id,
                channel=NotificationChannel.IN_APP,
                idempotency_key=f"transcript_processed_{transcript_id}",
            )
        )

    async def notify_content_generated(
        self,
        user_id: UUID,
        organization_id: UUID,
        content_id: UUID,
        content_type: str,
        content_title: str,
    ) -> NotificationResponse:
        """Create notification when content has been generated."""
        return await self.create_notification(
            NotificationCreate(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.CONTENT_GENERATED,
                title="Content Generated",
                body=f'Your {content_type} "{content_title}" has been generated and is ready for download.',
                priority=NotificationPriority.NORMAL,
                entity_type="content",
                entity_id=content_id,
                metadata={"content_type": content_type},
                channel=NotificationChannel.IN_APP,
                idempotency_key=f"content_generated_{content_id}",
            )
        )

    async def notify_enrichment_complete(
        self,
        user_id: UUID,
        organization_id: UUID,
        prospect_id: UUID,
        prospect_name: str,
    ) -> NotificationResponse:
        """Create notification when prospect enrichment is complete."""
        return await self.create_notification(
            NotificationCreate(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.ENRICHMENT_COMPLETE,
                title="Enrichment Complete",
                body=f'Prospect "{prospect_name}" has been enriched with additional data.',
                priority=NotificationPriority.NORMAL,
                entity_type="prospect",
                entity_id=prospect_id,
                channel=NotificationChannel.IN_APP,
                idempotency_key=f"enrichment_complete_{prospect_id}",
            )
        )

    async def notify_coaching_feedback_ready(
        self,
        user_id: UUID,
        organization_id: UUID,
        coaching_report_id: UUID,
        call_title: str,
    ) -> NotificationResponse:
        """Create notification when coaching feedback is ready."""
        return await self.create_notification(
            NotificationCreate(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.COACHING_FEEDBACK_READY,
                title="Coaching Feedback Ready",
                body=f'Coaching feedback for "{call_title}" is ready for review.',
                priority=NotificationPriority.NORMAL,
                entity_type="coaching_report",
                entity_id=coaching_report_id,
                channel=NotificationChannel.IN_APP,
                idempotency_key=f"coaching_ready_{coaching_report_id}",
            )
        )

    async def notify_integration_sync_status(
        self,
        user_id: UUID,
        organization_id: UUID,
        integration_name: str,
        status: str,
        details: Optional[str] = None,
    ) -> NotificationResponse:
        """Create notification for integration sync status updates."""
        priority = (
            NotificationPriority.HIGH
            if status == "failed"
            else NotificationPriority.NORMAL
        )

        body = f"{integration_name} sync {status}."
        if details:
            body += f" {details}"

        return await self.create_notification(
            NotificationCreate(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.INTEGRATION_SYNC_STATUS,
                title=f"{integration_name} Sync {status.capitalize()}",
                body=body,
                priority=priority,
                metadata={"integration": integration_name, "status": status},
                channel=NotificationChannel.IN_APP,
                idempotency_key=f"integration_sync_{integration_name}_{datetime.utcnow().isoformat()}",
            )
        )
