"""Audit trail service for compliance and security reporting."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import (
    ActivityCategory,
    ActivityLog,
    ActivitySeverity,
    AuditTrailEntry,
    AuditTrailResponse,
    PaginationParams,
)

logger = logging.getLogger(__name__)


# Categories that are considered security-relevant for audit trails
AUDIT_CATEGORIES = [
    ActivityCategory.USER_LOGIN,
    ActivityCategory.USER_LOGOUT,
    ActivityCategory.USER_PASSWORD_CHANGE,
    ActivityCategory.USER_SETTINGS_CHANGE,
    ActivityCategory.INTEGRATION_CONNECT,
    ActivityCategory.INTEGRATION_DISCONNECT,
    ActivityCategory.CRM_SYNC_START,
    ActivityCategory.CRM_SYNC_COMPLETE,
    ActivityCategory.CRM_SYNC_FAILED,
    ActivityCategory.CONTENT_EXPORT,
    ActivityCategory.CONTENT_DELETE,
    ActivityCategory.TRANSCRIPT_DELETE,
    ActivityCategory.SYSTEM_ERROR,
    ActivityCategory.API_ERROR,
    ActivityCategory.API_RATE_LIMITED,
]


class AuditService:
    """Service for generating audit trails and compliance reports."""

    def __init__(self, db: AsyncSession):
        """Initialize the audit service.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_audit_trail(
        self,
        user_id: int | None = None,
        organization_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        categories: list[ActivityCategory] | None = None,
        pagination: PaginationParams | None = None,
    ) -> AuditTrailResponse:
        """Get audit trail entries for compliance.

        Args:
            user_id: Filter by user ID
            organization_id: Filter by organization ID
            start_date: Start of date range
            end_date: End of date range
            categories: Filter by specific categories (defaults to AUDIT_CATEGORIES)
            pagination: Pagination parameters

        Returns:
            Paginated audit trail response
        """
        pagination = pagination or PaginationParams()
        categories = categories or AUDIT_CATEGORIES

        # Build query
        stmt = select(ActivityLog)
        conditions = [
            ActivityLog.category.in_([c.value for c in categories])
        ]

        if user_id is not None:
            conditions.append(ActivityLog.user_id == user_id)

        if organization_id is not None:
            conditions.append(ActivityLog.organization_id == organization_id)

        if start_date is not None:
            conditions.append(ActivityLog.occurred_at >= start_date)

        if end_date is not None:
            conditions.append(ActivityLog.occurred_at <= end_date)

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

        # Convert to audit trail entries
        entries = [
            AuditTrailEntry(
                id=a.id,
                occurred_at=a.occurred_at,
                user_id=a.user_id,
                user_email=a.user_email,
                category=a.category,
                action=a.action,
                resource_type=a.resource_type,
                resource_id=a.resource_id,
                ip_address=a.ip_address,
                status_code=a.status_code,
                details=a.details,
            )
            for a in activities
        ]

        total_pages = (total + pagination.page_size - 1) // pagination.page_size

        return AuditTrailResponse(
            items=entries,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1,
        )

    async def get_security_events(
        self,
        organization_id: int | None = None,
        hours: int = 24,
    ) -> list[AuditTrailEntry]:
        """Get recent security-relevant events.

        Args:
            organization_id: Filter by organization ID
            hours: Number of hours to look back

        Returns:
            List of security events
        """
        start_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        security_categories = [
            ActivityCategory.USER_LOGIN,
            ActivityCategory.USER_LOGOUT,
            ActivityCategory.USER_PASSWORD_CHANGE,
            ActivityCategory.API_ERROR,
            ActivityCategory.API_RATE_LIMITED,
            ActivityCategory.SYSTEM_ERROR,
        ]

        conditions = [
            ActivityLog.category.in_([c.value for c in security_categories]),
            ActivityLog.occurred_at >= start_date,
        ]

        if organization_id is not None:
            conditions.append(ActivityLog.organization_id == organization_id)

        result = await self.db.execute(
            select(ActivityLog)
            .where(and_(*conditions))
            .order_by(ActivityLog.occurred_at.desc())
            .limit(1000)
        )
        activities = result.scalars().all()

        return [
            AuditTrailEntry(
                id=a.id,
                occurred_at=a.occurred_at,
                user_id=a.user_id,
                user_email=a.user_email,
                category=a.category,
                action=a.action,
                resource_type=a.resource_type,
                resource_id=a.resource_id,
                ip_address=a.ip_address,
                status_code=a.status_code,
                details=a.details,
            )
            for a in activities
        ]

    async def get_failed_logins(
        self,
        user_id: int | None = None,
        hours: int = 24,
        threshold: int = 5,
    ) -> list[dict[str, Any]]:
        """Get failed login attempts, grouped by IP address.

        Args:
            user_id: Filter by user ID
            hours: Number of hours to look back
            threshold: Minimum number of failures to report

        Returns:
            List of IP addresses with failed login counts
        """
        start_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        conditions = [
            ActivityLog.category == ActivityCategory.USER_LOGIN.value,
            ActivityLog.severity.in_([
                ActivitySeverity.ERROR.value,
                ActivitySeverity.WARNING.value,
            ]),
            ActivityLog.occurred_at >= start_date,
        ]

        if user_id is not None:
            conditions.append(ActivityLog.user_id == user_id)

        result = await self.db.execute(
            select(
                ActivityLog.ip_address,
                func.count().label("failed_count"),
                func.max(ActivityLog.occurred_at).label("last_attempt"),
            )
            .where(and_(*conditions))
            .group_by(ActivityLog.ip_address)
            .having(func.count() >= threshold)
            .order_by(func.count().desc())
        )

        return [
            {
                "ip_address": row[0],
                "failed_count": row[1],
                "last_attempt": row[2],
            }
            for row in result.fetchall()
        ]

    async def get_data_export_audit(
        self,
        organization_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[AuditTrailEntry]:
        """Get audit trail for data export events.

        Args:
            organization_id: Filter by organization ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of data export audit entries
        """
        export_categories = [
            ActivityCategory.CONTENT_EXPORT,
        ]

        conditions = [
            ActivityLog.category.in_([c.value for c in export_categories]),
        ]

        if organization_id is not None:
            conditions.append(ActivityLog.organization_id == organization_id)

        if start_date is not None:
            conditions.append(ActivityLog.occurred_at >= start_date)

        if end_date is not None:
            conditions.append(ActivityLog.occurred_at <= end_date)

        result = await self.db.execute(
            select(ActivityLog)
            .where(and_(*conditions))
            .order_by(ActivityLog.occurred_at.desc())
        )
        activities = result.scalars().all()

        return [
            AuditTrailEntry(
                id=a.id,
                occurred_at=a.occurred_at,
                user_id=a.user_id,
                user_email=a.user_email,
                category=a.category,
                action=a.action,
                resource_type=a.resource_type,
                resource_id=a.resource_id,
                ip_address=a.ip_address,
                status_code=a.status_code,
                details=a.details,
            )
            for a in activities
        ]

    async def generate_compliance_report(
        self,
        organization_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Generate a compliance report for an organization.

        Args:
            organization_id: Organization ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report data
        """
        conditions = [
            ActivityLog.organization_id == organization_id,
            ActivityLog.occurred_at >= start_date,
            ActivityLog.occurred_at <= end_date,
        ]

        base_condition = and_(*conditions)

        # Get total activities
        total_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(base_condition)
        )
        total_activities = total_result.scalar() or 0

        # Get login count
        login_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(and_(
                base_condition,
                ActivityLog.category == ActivityCategory.USER_LOGIN.value,
            ))
        )
        login_count = login_result.scalar() or 0

        # Get data export count
        export_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(and_(
                base_condition,
                ActivityLog.category == ActivityCategory.CONTENT_EXPORT.value,
            ))
        )
        export_count = export_result.scalar() or 0

        # Get error count
        error_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(and_(
                base_condition,
                ActivityLog.severity.in_([
                    ActivitySeverity.ERROR.value,
                    ActivitySeverity.CRITICAL.value,
                ]),
            ))
        )
        error_count = error_result.scalar() or 0

        # Get unique users
        users_result = await self.db.execute(
            select(func.count(func.distinct(ActivityLog.user_id)))
            .select_from(ActivityLog)
            .where(and_(base_condition, ActivityLog.user_id.isnot(None)))
        )
        unique_users = users_result.scalar() or 0

        return {
            "organization_id": organization_id,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_activities": total_activities,
                "login_count": login_count,
                "export_count": export_count,
                "error_count": error_count,
                "unique_users": unique_users,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
