"""Activity log retention service for managing log lifecycle."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.activity import ActivityLog, ActivitySeverity

logger = logging.getLogger(__name__)
settings = get_settings()


class RetentionService:
    """Service for managing activity log retention and cleanup."""

    def __init__(self, db: AsyncSession):
        """Initialize the retention service.

        Args:
            db: Async database session
        """
        self.db = db

    async def apply_retention_policy(
        self,
        retention_days: int | None = None,
        batch_size: int | None = None,
    ) -> int:
        """Apply retention policy and delete old logs.

        This method deletes activity logs older than the retention period.
        Critical and error severity logs may be retained longer based on policy.

        Args:
            retention_days: Number of days to retain logs (defaults to config)
            batch_size: Number of records to delete per batch (defaults to config)

        Returns:
            Total number of records deleted
        """
        retention_days = retention_days or settings.ACTIVITY_LOG_RETENTION_DAYS
        batch_size = batch_size or settings.ACTIVITY_LOG_BATCH_SIZE

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        logger.info(
            "Applying retention policy: deleting logs older than %s (retention_days=%d)",
            cutoff_date.isoformat(),
            retention_days,
        )

        total_deleted = 0

        # Delete non-critical logs first (normal retention)
        while True:
            # Find IDs to delete in batches
            stmt = (
                select(ActivityLog.id)
                .where(
                    and_(
                        ActivityLog.occurred_at < cutoff_date,
                        ActivityLog.severity.notin_([
                            ActivitySeverity.ERROR.value,
                            ActivitySeverity.CRITICAL.value,
                        ]),
                    )
                )
                .limit(batch_size)
            )

            result = await self.db.execute(stmt)
            ids_to_delete = [row[0] for row in result.fetchall()]

            if not ids_to_delete:
                break

            # Delete the batch
            await self.db.execute(
                delete(ActivityLog).where(ActivityLog.id.in_(ids_to_delete))
            )
            await self.db.commit()

            total_deleted += len(ids_to_delete)
            logger.debug("Deleted batch of %d records", len(ids_to_delete))

        # Delete critical/error logs with extended retention (2x normal retention)
        extended_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days * 2)

        while True:
            stmt = (
                select(ActivityLog.id)
                .where(
                    and_(
                        ActivityLog.occurred_at < extended_cutoff,
                        ActivityLog.severity.in_([
                            ActivitySeverity.ERROR.value,
                            ActivitySeverity.CRITICAL.value,
                        ]),
                    )
                )
                .limit(batch_size)
            )

            result = await self.db.execute(stmt)
            ids_to_delete = [row[0] for row in result.fetchall()]

            if not ids_to_delete:
                break

            await self.db.execute(
                delete(ActivityLog).where(ActivityLog.id.in_(ids_to_delete))
            )
            await self.db.commit()

            total_deleted += len(ids_to_delete)

        logger.info("Retention policy applied: deleted %d records total", total_deleted)
        return total_deleted

    async def get_retention_stats(self) -> dict:
        """Get statistics about log retention.

        Returns:
            Dictionary with retention statistics
        """
        now = datetime.now(timezone.utc)
        retention_days = settings.ACTIVITY_LOG_RETENTION_DAYS

        # Total logs
        total_result = await self.db.execute(
            select(func.count()).select_from(ActivityLog)
        )
        total_logs = total_result.scalar() or 0

        # Logs within retention period
        cutoff_date = now - timedelta(days=retention_days)
        within_retention_result = await self.db.execute(
            select(func.count())
            .select_from(ActivityLog)
            .where(ActivityLog.occurred_at >= cutoff_date)
        )
        within_retention = within_retention_result.scalar() or 0

        # Logs past retention (eligible for deletion)
        past_retention = total_logs - within_retention

        # Oldest log
        oldest_result = await self.db.execute(
            select(func.min(ActivityLog.occurred_at))
        )
        oldest_log_date = oldest_result.scalar()

        # Newest log
        newest_result = await self.db.execute(
            select(func.max(ActivityLog.occurred_at))
        )
        newest_log_date = newest_result.scalar()

        # Storage estimate (rough calculation)
        avg_record_size_bytes = 500  # Estimated average size per record
        estimated_storage_mb = (total_logs * avg_record_size_bytes) / (1024 * 1024)

        return {
            "retention_policy": {
                "normal_retention_days": retention_days,
                "error_retention_days": retention_days * 2,
                "cutoff_date": cutoff_date.isoformat(),
            },
            "statistics": {
                "total_logs": total_logs,
                "within_retention": within_retention,
                "past_retention": past_retention,
                "oldest_log_date": oldest_log_date.isoformat() if oldest_log_date else None,
                "newest_log_date": newest_log_date.isoformat() if newest_log_date else None,
                "estimated_storage_mb": round(estimated_storage_mb, 2),
            },
        }

    async def archive_logs(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Export logs for archiving before deletion.

        Args:
            start_date: Start of date range to archive
            end_date: End of date range to archive

        Returns:
            List of log entries for archiving
        """
        result = await self.db.execute(
            select(ActivityLog)
            .where(
                and_(
                    ActivityLog.occurred_at >= start_date,
                    ActivityLog.occurred_at <= end_date,
                )
            )
            .order_by(ActivityLog.occurred_at.asc())
        )
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_email": log.user_email,
                "organization_id": log.organization_id,
                "category": log.category,
                "action": log.action,
                "severity": log.severity,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "request_id": log.request_id,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "status_code": log.status_code,
                "response_time_ms": log.response_time_ms,
                "details": log.details,
                "error_message": log.error_message,
                "occurred_at": log.occurred_at.isoformat(),
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    async def delete_logs_by_user(
        self,
        user_id: int,
        anonymize: bool = True,
    ) -> int:
        """Delete or anonymize logs for a specific user (GDPR compliance).

        Args:
            user_id: User ID to delete logs for
            anonymize: If True, anonymize instead of delete

        Returns:
            Number of records affected
        """
        if anonymize:
            # Anonymize user data instead of deleting
            result = await self.db.execute(
                select(ActivityLog).where(ActivityLog.user_id == user_id)
            )
            logs = result.scalars().all()

            for log in logs:
                log.user_id = None
                log.user_email = "[REDACTED]"
                log.ip_address = "[REDACTED]"
                log.user_agent = None
                if log.details:
                    # Remove any PII from details
                    log.details = {"redacted": True, "reason": "user_deletion_request"}

            await self.db.commit()
            return len(logs)
        else:
            # Hard delete
            result = await self.db.execute(
                delete(ActivityLog).where(ActivityLog.user_id == user_id)
            )
            await self.db.commit()
            return result.rowcount
