"""
Notification API endpoints for Sales OS.

This module provides REST API endpoints for managing notifications,
including listing, reading, and configuring notification preferences.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceBulkUpdate,
    UnreadCountResponse,
    MarkReadRequest,
    MarkAllReadRequest,
)
from ..services.notifications import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# =============================================================================
# Dependency Injection
# =============================================================================


async def get_current_user() -> dict:
    """
    Get the current authenticated user.

    This is a placeholder that should be replaced with actual
    authentication dependency in production.

    Returns:
        Dictionary with user_id and organization_id
    """
    # TODO: Implement actual authentication
    # This should verify JWT token and return user info
    return {
        "user_id": UUID("00000000-0000-0000-0000-000000000001"),
        "organization_id": UUID("00000000-0000-0000-0000-000000000001"),
    }


async def get_notification_service() -> NotificationService:
    """
    Get notification service instance.

    This is a placeholder that should be replaced with actual
    dependency injection using database session and other services.

    Returns:
        NotificationService instance
    """
    # TODO: Implement proper dependency injection with database session
    # In production:
    # async def get_notification_service(
    #     db: AsyncSession = Depends(get_db),
    #     websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    #     email_service: EmailNotificationService = Depends(get_email_service),
    # ) -> NotificationService:
    #     return NotificationService(db, websocket_manager, email_service)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Notification service not configured. Please set up database connection.",
    )


# =============================================================================
# Notification Endpoints
# =============================================================================


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    priority: Optional[NotificationPriority] = Query(None, description="Filter by priority"),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """
    Get a paginated list of notifications for the current user.

    Supports filtering by type, read status, and priority. Results are
    ordered by creation date (newest first).

    Query Parameters:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        type: Filter by notification type
        is_read: Filter by read status (true/false)
        priority: Filter by priority level

    Returns:
        Paginated list of notifications with metadata
    """
    return await service.get_notifications(
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size,
        notification_type=type,
        is_read=is_read,
        priority=priority,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    """
    Get the count of unread notifications for the current user.

    Returns:
        Total unread count and breakdown by notification type
    """
    return await service.get_unread_count(user_id=current_user["user_id"])


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """
    Get a single notification by ID.

    Path Parameters:
        notification_id: The notification UUID

    Returns:
        The notification details

    Raises:
        404: If the notification is not found or doesn't belong to the user
    """
    notification = await service.get_notification(
        notification_id=notification_id,
        user_id=current_user["user_id"],
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


@router.post("/mark-read")
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Mark specific notifications as read.

    Request Body:
        notification_ids: List of notification UUIDs to mark as read

    Returns:
        Number of notifications marked as read
    """
    count = await service.mark_as_read(
        notification_ids=request.notification_ids,
        user_id=current_user["user_id"],
    )

    return {"marked_read": count}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    request: Optional[MarkAllReadRequest] = None,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Mark all notifications as read for the current user.

    Optionally filter by date or notification type.

    Request Body (optional):
        before_date: Only mark notifications before this date
        notification_type: Only mark notifications of this type

    Returns:
        Number of notifications marked as read
    """
    before_date = request.before_date if request else None
    notification_type = request.notification_type if request else None

    count = await service.mark_all_as_read(
        user_id=current_user["user_id"],
        before_date=before_date,
        notification_type=notification_type,
    )

    return {"marked_read": count}


@router.post("/archive")
async def archive_notifications(
    request: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Archive notifications (hide from main view).

    Request Body:
        notification_ids: List of notification UUIDs to archive

    Returns:
        Number of notifications archived
    """
    count = await service.archive_notifications(
        notification_ids=request.notification_ids,
        user_id=current_user["user_id"],
    )

    return {"archived": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Delete a notification.

    Path Parameters:
        notification_id: The notification UUID to delete

    Returns:
        Success status

    Raises:
        404: If the notification is not found or doesn't belong to the user
    """
    deleted = await service.delete_notification(
        notification_id=notification_id,
        user_id=current_user["user_id"],
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"deleted": True}


# =============================================================================
# Preferences Endpoints
# =============================================================================


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> List[NotificationPreferenceResponse]:
    """
    Get all notification preferences for the current user.

    Returns a complete preference matrix for all notification types
    and channels, including default values for preferences not yet set.

    Returns:
        List of notification preferences
    """
    return await service.get_all_preferences(user_id=current_user["user_id"])


@router.put("/preferences")
async def update_notification_preferences(
    request: NotificationPreferenceBulkUpdate,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> List[NotificationPreferenceResponse]:
    """
    Bulk update notification preferences.

    Request Body:
        preferences: List of preference settings to update

    Returns:
        Updated list of preferences
    """
    return await service.bulk_update_preferences(
        user_id=current_user["user_id"],
        preferences=request.preferences,
    )


@router.put("/preferences/{notification_type}/{channel}")
async def update_single_preference(
    notification_type: NotificationType,
    channel: str,
    enabled: bool = Query(..., description="Whether this channel is enabled"),
    digest_frequency: Optional[str] = Query(None, description="Digest frequency (daily/weekly/monthly)"),
    digest_time: Optional[str] = Query(None, description="Digest time in HH:MM format"),
    digest_timezone: Optional[str] = Query(None, description="Digest timezone"),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    """
    Update a single notification preference.

    Path Parameters:
        notification_type: The notification type
        channel: The notification channel (in_app, email_instant, email_digest, websocket)

    Query Parameters:
        enabled: Whether this channel is enabled for this notification type
        digest_frequency: For email_digest, the frequency (daily/weekly/monthly)
        digest_time: For email_digest, the time to send (HH:MM format)
        digest_timezone: For email_digest, the timezone

    Returns:
        The updated preference
    """
    from ..models.notification import NotificationChannel

    try:
        channel_enum = NotificationChannel(channel)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel: {channel}. Must be one of: {[c.value for c in NotificationChannel]}",
        )

    return await service.update_preference(
        user_id=current_user["user_id"],
        notification_type=notification_type,
        channel=channel_enum,
        enabled=enabled,
        digest_frequency=digest_frequency,
        digest_time=digest_time,
        digest_timezone=digest_timezone,
    )


# =============================================================================
# Health Check
# =============================================================================


@router.get("/health")
async def notifications_health() -> dict:
    """
    Health check endpoint for the notifications service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "notifications",
    }
