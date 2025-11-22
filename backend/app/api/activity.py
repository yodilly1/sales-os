"""Activity logging and audit trail API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity import (
    ActivityCategory,
    ActivityFeedResponse,
    ActivityLogCreate,
    ActivityLogQuery,
    ActivityLogResponse,
    ActivitySeverity,
    ActivityStats,
    AuditTrailResponse,
    PaginationParams,
)
from app.services.activity import ActivityService, AuditService, RetentionService

router = APIRouter()


# Dependency to get activity service
async def get_activity_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActivityService:
    """Get activity service dependency."""
    return ActivityService(db)


async def get_audit_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditService:
    """Get audit service dependency."""
    return AuditService(db)


async def get_retention_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RetentionService:
    """Get retention service dependency."""
    return RetentionService(db)


# Activity Feed Endpoints


@router.get("", response_model=ActivityFeedResponse)
async def get_activity_feed(
    service: Annotated[ActivityService, Depends(get_activity_service)],
    user_id: Annotated[int | None, Query(description="Filter by user ID")] = None,
    organization_id: Annotated[
        int | None, Query(description="Filter by organization ID")
    ] = None,
    category: Annotated[
        ActivityCategory | None, Query(description="Filter by category")
    ] = None,
    severity: Annotated[
        ActivitySeverity | None, Query(description="Filter by severity")
    ] = None,
    resource_type: Annotated[
        str | None, Query(description="Filter by resource type")
    ] = None,
    resource_id: Annotated[str | None, Query(description="Filter by resource ID")] = None,
    start_date: Annotated[
        datetime | None, Query(description="Start date filter (ISO format)")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="End date filter (ISO format)")
    ] = None,
    search: Annotated[str | None, Query(description="Search in action and error messages")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> ActivityFeedResponse:
    """Get paginated activity feed with optional filters.

    Returns a chronologically ordered list of activity events, with the most
    recent activities first. Supports filtering by user, organization, category,
    severity, resource, and date range.
    """
    query = ActivityLogQuery(
        user_id=user_id,
        organization_id=organization_id,
        category=category,
        severity=severity,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    pagination = PaginationParams(page=page, page_size=page_size)

    return await service.query_activities(query, pagination)


@router.get("/{activity_id}", response_model=ActivityLogResponse)
async def get_activity(
    activity_id: int,
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> ActivityLogResponse:
    """Get a single activity log by ID."""
    activity = await service.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    return ActivityLogResponse.model_validate(activity)


@router.post("", response_model=ActivityLogResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityLogCreate,
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> ActivityLogResponse:
    """Create a new activity log entry.

    This endpoint is primarily used for logging activities from external systems
    or for manual logging. Most activities are automatically logged by the
    activity logging middleware.
    """
    activity = await service.log_from_schema(data)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Activity logging is disabled",
        )
    return ActivityLogResponse.model_validate(activity)


@router.get("/resource/{resource_type}/{resource_id}", response_model=ActivityFeedResponse)
async def get_resource_activities(
    resource_type: str,
    resource_id: str,
    service: Annotated[ActivityService, Depends(get_activity_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> ActivityFeedResponse:
    """Get all activities for a specific resource.

    Useful for viewing the complete activity history of a transcript, content,
    prospect, or other resource.
    """
    return await service.get_activities_by_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )


@router.get("/request/{request_id}", response_model=list[ActivityLogResponse])
async def get_request_activities(
    request_id: str,
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> list[ActivityLogResponse]:
    """Get all activities for a specific request.

    Useful for debugging and tracing a single request through the system.
    """
    activities = await service.get_activities_by_request(request_id)
    return [ActivityLogResponse.model_validate(a) for a in activities]


# Statistics Endpoints


@router.get("/stats/summary", response_model=ActivityStats)
async def get_activity_stats(
    service: Annotated[ActivityService, Depends(get_activity_service)],
    user_id: Annotated[int | None, Query(description="Filter by user ID")] = None,
    organization_id: Annotated[
        int | None, Query(description="Filter by organization ID")
    ] = None,
    days: Annotated[int, Query(ge=1, le=365, description="Number of days to look back")] = 30,
) -> ActivityStats:
    """Get activity statistics summary.

    Returns aggregated statistics including activity counts by category and
    severity, daily activity trends, top users, and error rates.
    """
    return await service.get_activity_stats(
        user_id=user_id,
        organization_id=organization_id,
        days=days,
    )


# Audit Trail Endpoints


@router.get("/audit/trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    service: Annotated[AuditService, Depends(get_audit_service)],
    user_id: Annotated[int | None, Query(description="Filter by user ID")] = None,
    organization_id: Annotated[
        int | None, Query(description="Filter by organization ID")
    ] = None,
    start_date: Annotated[
        datetime | None, Query(description="Start date filter (ISO format)")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="End date filter (ISO format)")
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> AuditTrailResponse:
    """Get audit trail for compliance reporting.

    Returns security-relevant events including logins, logouts, data exports,
    integration changes, and error events. This endpoint is designed for
    compliance and security auditing.
    """
    return await service.get_audit_trail(
        user_id=user_id,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        pagination=PaginationParams(page=page, page_size=page_size),
    )


@router.get("/audit/security")
async def get_security_events(
    service: Annotated[AuditService, Depends(get_audit_service)],
    organization_id: Annotated[
        int | None, Query(description="Filter by organization ID")
    ] = None,
    hours: Annotated[int, Query(ge=1, le=168, description="Hours to look back")] = 24,
):
    """Get recent security events.

    Returns security-relevant events from the last N hours including login
    attempts, password changes, API errors, and rate limiting events.
    """
    events = await service.get_security_events(
        organization_id=organization_id,
        hours=hours,
    )
    return {"events": events, "count": len(events)}


@router.get("/audit/failed-logins")
async def get_failed_logins(
    service: Annotated[AuditService, Depends(get_audit_service)],
    user_id: Annotated[int | None, Query(description="Filter by user ID")] = None,
    hours: Annotated[int, Query(ge=1, le=168, description="Hours to look back")] = 24,
    threshold: Annotated[int, Query(ge=1, description="Minimum failures to report")] = 5,
):
    """Get failed login attempts grouped by IP address.

    Returns IP addresses that have had multiple failed login attempts,
    useful for detecting brute force attacks.
    """
    results = await service.get_failed_logins(
        user_id=user_id,
        hours=hours,
        threshold=threshold,
    )
    return {"failed_logins": results, "count": len(results)}


@router.get("/audit/data-exports")
async def get_data_export_audit(
    service: Annotated[AuditService, Depends(get_audit_service)],
    organization_id: Annotated[
        int | None, Query(description="Filter by organization ID")
    ] = None,
    start_date: Annotated[
        datetime | None, Query(description="Start date filter (ISO format)")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="End date filter (ISO format)")
    ] = None,
):
    """Get audit trail for data export events.

    Returns all data export activities for compliance tracking.
    """
    events = await service.get_data_export_audit(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    return {"exports": events, "count": len(events)}


@router.post("/audit/compliance-report")
async def generate_compliance_report(
    service: Annotated[AuditService, Depends(get_audit_service)],
    organization_id: Annotated[int, Query(description="Organization ID")],
    start_date: Annotated[datetime, Query(description="Report start date (ISO format)")],
    end_date: Annotated[datetime, Query(description="Report end date (ISO format)")],
):
    """Generate a compliance report for an organization.

    Returns a summary report suitable for compliance audits including
    activity counts, login statistics, export history, and error rates.
    """
    return await service.generate_compliance_report(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )


# Retention Management Endpoints


@router.get("/retention/stats")
async def get_retention_stats(
    service: Annotated[RetentionService, Depends(get_retention_service)],
):
    """Get retention policy statistics.

    Returns information about the current retention policy, log counts,
    and storage estimates.
    """
    return await service.get_retention_stats()


@router.post("/retention/apply")
async def apply_retention_policy(
    service: Annotated[RetentionService, Depends(get_retention_service)],
    retention_days: Annotated[
        int | None, Query(ge=1, le=365, description="Retention period in days")
    ] = None,
    batch_size: Annotated[
        int | None, Query(ge=10, le=1000, description="Batch size for deletion")
    ] = None,
):
    """Apply the retention policy and delete old logs.

    This operation deletes logs older than the retention period. Critical
    and error logs are retained for twice the normal retention period.
    Use with caution in production.
    """
    deleted_count = await service.apply_retention_policy(
        retention_days=retention_days,
        batch_size=batch_size,
    )
    return {
        "status": "completed",
        "deleted_count": deleted_count,
    }


@router.post("/retention/archive")
async def archive_logs(
    service: Annotated[RetentionService, Depends(get_retention_service)],
    start_date: Annotated[datetime, Query(description="Archive start date (ISO format)")],
    end_date: Annotated[datetime, Query(description="Archive end date (ISO format)")],
):
    """Export logs for archiving before deletion.

    Returns all logs in the specified date range in a format suitable
    for external storage and archival.
    """
    logs = await service.archive_logs(start_date=start_date, end_date=end_date)
    return {
        "logs": logs,
        "count": len(logs),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
    }


@router.delete("/user/{user_id}")
async def delete_user_logs(
    user_id: int,
    service: Annotated[RetentionService, Depends(get_retention_service)],
    anonymize: Annotated[
        bool, Query(description="Anonymize instead of delete (GDPR-compliant)")
    ] = True,
):
    """Delete or anonymize logs for a specific user.

    This endpoint is used for GDPR compliance when a user requests
    data deletion. By default, logs are anonymized rather than deleted
    to maintain audit trail integrity.
    """
    affected_count = await service.delete_logs_by_user(
        user_id=user_id,
        anonymize=anonymize,
    )
    return {
        "status": "completed",
        "action": "anonymized" if anonymize else "deleted",
        "affected_count": affected_count,
    }
