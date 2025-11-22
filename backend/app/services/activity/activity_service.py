"""Core activity logging service for tracking all system events."""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.activity import (
    ActivityCategory,
    ActivityFeedResponse,
    ActivityLog,
    ActivityLogCreate,
    ActivityLogQuery,
    ActivityLogResponse,
    ActivitySeverity,
    ActivityStats,
    PaginationParams,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ActivityService:
    """Service for logging and querying activity events."""

    def __init__(self, db: AsyncSession):
        """Initialize the activity service.

        Args:
            db: Async database session
        """
        self.db = db

    async def log_activity(
        self,
        category: ActivityCategory,
        action: str,
        *,
        user_id: int | None = None,
        user_email: str | None = None,
        organization_id: int | None = None,
        severity: ActivitySeverity = ActivitySeverity.INFO,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        status_code: int | None = None,
        response_time_ms: int | None = None,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
        occurred_at: datetime | None = None,
    ) -> ActivityLog:
        """Log an activity event.

        Args:
            category: Category of the activity
            action: Human-readable description of the action
            user_id: ID of the user performing the action
            user_email: Email of the user performing the action
            organization_id: ID of the organization context
            severity: Severity level of the activity
            resource_type: Type of resource affected (e.g., "Transcript", "Content")
            resource_id: ID of the affected resource
            ip_address: Client IP address
            user_agent: Client user agent string
            request_id: Unique request identifier for tracing
            request_method: HTTP method (GET, POST, etc.)
            request_path: Request URL path
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds
            details: Additional structured details
            error_message: Error message if applicable
            occurred_at: Timestamp of when the event occurred

        Returns:
            The created ActivityLog instance
        """
        if not settings.ACTIVITY_LOG_ENABLED:
            logger.debug("Activity logging disabled, skipping log")
            return None

        activity_log = ActivityLog(
            category=category.value,
            action=action,
            severity=severity.value,
            user_id=user_id,
            user_email=user_email,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
            response_time_ms=response_time_ms,
            details=details,
            error_message=error_message,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )

        self.db.add(activity_log)
        await self.db.flush()
        await self.db.refresh(activity_log)

        logger.debug(
            "Activity logged: category=%s, action=%s, user_id=%s",
            category.value,
            action,
            user_id,
        )

        return activity_log

    async def log_from_schema(self, data: ActivityLogCreate) -> ActivityLog:
        """Log an activity from a Pydantic schema.

        Args:
            data: Activity log creation data

        Returns:
            The created ActivityLog instance
        """
        return await self.log_activity(
            category=data.category,
            action=data.action,
            user_id=data.user_id,
            user_email=data.user_email,
            organization_id=data.organization_id,
            severity=data.severity,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            request_id=data.request_id,
            request_method=data.request_method,
            request_path=data.request_path,
            status_code=data.status_code,
            response_time_ms=data.response_time_ms,
            details=data.details,
            error_message=data.error_message,
            occurred_at=data.occurred_at,
        )

    async def get_activity_by_id(self, activity_id: int) -> ActivityLog | None:
        """Get a single activity log by ID.

        Args:
            activity_id: The activity log ID

        Returns:
            The ActivityLog instance or None if not found
        """
        result = await self.db.execute(
            select(ActivityLog).where(ActivityLog.id == activity_id)
        )
        return result.scalar_one_or_none()

    async def query_activities(
        self,
        query: ActivityLogQuery,
        pagination: PaginationParams | None = None,
    ) -> ActivityFeedResponse:
        """Query activity logs with filters and pagination.

        Args:
            query: Query filters
            pagination: Pagination parameters

        Returns:
            Paginated activity feed response
        """
        pagination = pagination or PaginationParams()

        # Build base query
        stmt = select(ActivityLog)
        conditions = []

        # Apply filters
        if query.user_id is not None:
            conditions.append(ActivityLog.user_id == query.user_id)

        if query.organization_id is not None:
            conditions.append(ActivityLog.organization_id == query.organization_id)

        if query.category is not None:
            conditions.append(ActivityLog.category == query.category.value)

        if query.categories:
            conditions.append(
                ActivityLog.category.in_([c.value for c in query.categories])
            )

        if query.severity is not None:
            conditions.append(ActivityLog.severity == query.severity.value)

        if query.severities:
            conditions.append(
                ActivityLog.severity.in_([s.value for s in query.severities])
            )

        if query.resource_type is not None:
            conditions.append(ActivityLog.resource_type == query.resource_type)

        if query.resource_id is not None:
            conditions.append(ActivityLog.resource_id == str(query.resource_id))

        if query.request_id is not None:
            conditions.append(ActivityLog.request_id == query.request_id)

        if query.start_date is not None:
            conditions.append(ActivityLog.occurred_at >= query.start_date)

        if query.end_date is not None:
            conditions.append(ActivityLog.occurred_at <= query.end_date)

        if query.search:
            search_term = f"%{query.search}%"
            conditions.append(
                or_(
                    ActivityLog.action.ilike(search_term),
                    ActivityLog.resource_type.ilike(search_term),
                    ActivityLog.error_message.ilike(search_term),
                )
            )

        # Apply conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (pagination.page - 1) * pagination.page_size
        stmt = (
            stmt.order_by(ActivityLog.occurred_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        # Execute query
        result = await self.db.execute(stmt)
        activities = result.scalars().all()

        # Calculate pagination info
        total_pages = (total + pagination.page_size - 1) // pagination.page_size

        return ActivityFeedResponse(
            items=[ActivityLogResponse.model_validate(a) for a in activities],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1,
        )

    async def get_activity_feed(
        self,
        user_id: int | None = None,
        organization_id: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ActivityFeedResponse:
        """Get a chronological activity feed.

        Args:
            user_id: Filter by user ID
            organization_id: Filter by organization ID
            page: Page number
            page_size: Number of items per page

        Returns:
            Paginated activity feed
        """
        query = ActivityLogQuery(
            user_id=user_id,
            organization_id=organization_id,
        )
        pagination = PaginationParams(page=page, page_size=page_size)
        return await self.query_activities(query, pagination)

    async def get_activities_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> ActivityFeedResponse:
        """Get all activities for a specific resource.

        Args:
            resource_type: Type of the resource
            resource_id: ID of the resource
            page: Page number
            page_size: Number of items per page

        Returns:
            Paginated activity feed for the resource
        """
        query = ActivityLogQuery(
            resource_type=resource_type,
            resource_id=resource_id,
        )
        pagination = PaginationParams(page=page, page_size=page_size)
        return await self.query_activities(query, pagination)

    async def get_activities_by_request(
        self,
        request_id: str,
    ) -> Sequence[ActivityLog]:
        """Get all activities for a specific request.

        Args:
            request_id: The request ID

        Returns:
            List of activities for the request
        """
        result = await self.db.execute(
            select(ActivityLog)
            .where(ActivityLog.request_id == request_id)
            .order_by(ActivityLog.occurred_at.asc())
        )
        return result.scalars().all()

    async def get_activity_stats(
        self,
        user_id: int | None = None,
        organization_id: int | None = None,
        days: int = 30,
    ) -> ActivityStats:
        """Get activity statistics for a time period.

        Args:
            user_id: Filter by user ID
            organization_id: Filter by organization ID
            days: Number of days to look back

        Returns:
            Activity statistics summary
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Build base condition
        conditions = [ActivityLog.occurred_at >= start_date]
        if user_id is not None:
            conditions.append(ActivityLog.user_id == user_id)
        if organization_id is not None:
            conditions.append(ActivityLog.organization_id == organization_id)

        base_condition = and_(*conditions)

        # Get total count
        total_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(base_condition)
        )
        total_activities = total_result.scalar() or 0

        # Get counts by category
        category_result = await self.db.execute(
            select(ActivityLog.category, func.count())
            .where(base_condition)
            .group_by(ActivityLog.category)
        )
        activities_by_category = {
            row[0]: row[1] for row in category_result.fetchall()
        }

        # Get counts by severity
        severity_result = await self.db.execute(
            select(ActivityLog.severity, func.count())
            .where(base_condition)
            .group_by(ActivityLog.severity)
        )
        activities_by_severity = {
            row[0]: row[1] for row in severity_result.fetchall()
        }

        # Get counts by day
        day_result = await self.db.execute(
            select(
                func.date(ActivityLog.occurred_at).label("day"),
                func.count().label("count"),
            )
            .where(base_condition)
            .group_by(func.date(ActivityLog.occurred_at))
            .order_by(func.date(ActivityLog.occurred_at))
        )
        activities_by_day = {
            str(row[0]): row[1] for row in day_result.fetchall()
        }

        # Get top users
        top_users_result = await self.db.execute(
            select(
                ActivityLog.user_id,
                ActivityLog.user_email,
                func.count().label("count"),
            )
            .where(and_(base_condition, ActivityLog.user_id.isnot(None)))
            .group_by(ActivityLog.user_id, ActivityLog.user_email)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_users = [
            {"user_id": row[0], "user_email": row[1], "count": row[2]}
            for row in top_users_result.fetchall()
        ]

        # Calculate error rate
        error_count = activities_by_severity.get(ActivitySeverity.ERROR.value, 0)
        error_count += activities_by_severity.get(ActivitySeverity.CRITICAL.value, 0)
        error_rate = error_count / total_activities if total_activities > 0 else 0.0

        return ActivityStats(
            total_activities=total_activities,
            activities_by_category=activities_by_category,
            activities_by_severity=activities_by_severity,
            activities_by_day=activities_by_day,
            top_users=top_users,
            error_rate=error_rate,
        )


# Convenience functions for logging common activities


async def log_user_login(
    service: ActivityService,
    user_id: int,
    user_email: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    **kwargs,
) -> ActivityLog:
    """Log a user login event."""
    return await service.log_activity(
        category=ActivityCategory.USER_LOGIN,
        action=f"User {user_email} logged in",
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        user_agent=user_agent,
        **kwargs,
    )


async def log_transcript_upload(
    service: ActivityService,
    user_id: int,
    transcript_id: int,
    source: str,
    **kwargs,
) -> ActivityLog:
    """Log a transcript upload event."""
    return await service.log_activity(
        category=ActivityCategory.TRANSCRIPT_UPLOAD,
        action=f"Transcript uploaded from {source}",
        user_id=user_id,
        resource_type="Transcript",
        resource_id=str(transcript_id),
        details={"source": source},
        **kwargs,
    )


async def log_content_generate(
    service: ActivityService,
    user_id: int,
    content_id: int,
    content_type: str,
    **kwargs,
) -> ActivityLog:
    """Log a content generation event."""
    return await service.log_activity(
        category=ActivityCategory.CONTENT_GENERATE,
        action=f"Generated {content_type} content",
        user_id=user_id,
        resource_type="Content",
        resource_id=str(content_id),
        details={"content_type": content_type},
        **kwargs,
    )


async def log_crm_sync(
    service: ActivityService,
    user_id: int,
    crm_type: str,
    status: str,
    records_synced: int = 0,
    **kwargs,
) -> ActivityLog:
    """Log a CRM sync event."""
    category = (
        ActivityCategory.CRM_SYNC_COMPLETE
        if status == "success"
        else ActivityCategory.CRM_SYNC_FAILED
    )
    severity = ActivitySeverity.INFO if status == "success" else ActivitySeverity.ERROR

    return await service.log_activity(
        category=category,
        action=f"CRM sync {status} with {crm_type}",
        user_id=user_id,
        severity=severity,
        details={"crm_type": crm_type, "status": status, "records_synced": records_synced},
        **kwargs,
    )
