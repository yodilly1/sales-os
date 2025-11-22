"""
Meeting Prep API Routes

REST API endpoints for the meeting preparation service.
Handles meeting management, prep brief generation, and delivery.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.meetingprep import (
    MeetingCreateRequest,
    MeetingSyncRequest,
    PrepBriefGenerateRequest,
    PrepBriefDeliveryRequest,
    BulkPrepGenerateRequest,
    MeetingSchema,
    MeetingListResponse,
    MeetingPrepBriefSchema,
    PrepBriefStatusResponse,
    DeliveryStatusResponse,
    PrepStatus,
    DeliveryMethod,
)
from app.services.meetingprep import MeetingPrepService
from app.services.meetingprep.brief_generator import BriefGenerator
from app.services.meetingprep.calendar_integration import CalendarIntegration
from app.services.meetingprep.delivery import DeliveryService

router = APIRouter(prefix="/api/meetingprep", tags=["Meeting Prep"])


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_meeting_prep_service(
    db: AsyncSession = Depends(get_db),
) -> MeetingPrepService:
    """Get an instance of the MeetingPrepService with all dependencies."""
    # These would be injected from the app's dependency container
    from app.core.dependencies import (
        get_claude_client,
        get_enrichment_service,
        get_transcript_service,
        get_content_service,
        get_oauth_client,
        get_email_client,
    )

    claude_client = get_claude_client()
    enrichment_service = get_enrichment_service(db)
    transcript_service = get_transcript_service(db)
    content_service = get_content_service(db)
    oauth_client = get_oauth_client()
    email_client = get_email_client()

    brief_generator = BriefGenerator(
        claude_client=claude_client,
        enrichment_service=enrichment_service,
        transcript_service=transcript_service,
        content_service=content_service,
    )

    calendar_integration = CalendarIntegration(oauth_client=oauth_client)

    delivery_service = DeliveryService(
        email_client=email_client,
        calendar_integration=calendar_integration,
    )

    return MeetingPrepService(
        db=db,
        brief_generator=brief_generator,
        calendar_integration=calendar_integration,
        delivery_service=delivery_service,
    )


# ============================================================================
# Meeting Endpoints
# ============================================================================

@router.post("/meetings", response_model=MeetingSchema, status_code=201)
async def create_meeting(
    request: MeetingCreateRequest,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> MeetingSchema:
    """
    Create a new meeting manually.

    Use this when you want to track a meeting that isn't synced from a calendar,
    or when you need to manually enter meeting details.
    """
    meeting = await service.create_meeting(
        user_id=current_user.id,
        request=request,
    )
    return service.to_meeting_schema(meeting)


@router.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    include_past: bool = Query(False, description="Include past meetings"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> MeetingListResponse:
    """
    List meetings for the current user.

    By default, returns only upcoming meetings. Use `include_past=true` to
    include historical meetings.
    """
    meetings, total = await service.list_meetings(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        include_past=include_past,
        page=page,
        per_page=per_page,
    )

    return MeetingListResponse(
        meetings=[service.to_meeting_schema(m) for m in meetings],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/meetings/upcoming", response_model=list[MeetingSchema])
async def get_upcoming_meetings(
    days_ahead: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> list[MeetingSchema]:
    """
    Get upcoming meetings within the specified number of days.

    This is a convenience endpoint for quickly viewing your upcoming schedule.
    """
    meetings = await service.get_upcoming_meetings(
        user_id=current_user.id,
        days_ahead=days_ahead,
    )
    return [service.to_meeting_schema(m) for m in meetings]


@router.get("/meetings/{meeting_id}", response_model=MeetingSchema)
async def get_meeting(
    meeting_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> MeetingSchema:
    """Get a specific meeting by ID."""
    meeting = await service.get_meeting(meeting_id, current_user.id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return service.to_meeting_schema(meeting)


@router.post("/meetings/sync", response_model=list[MeetingSchema])
async def sync_calendar(
    request: MeetingSyncRequest,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> list[MeetingSchema]:
    """
    Sync meetings from a calendar provider.

    Supported providers: google, outlook/microsoft

    This will fetch events from your connected calendar and create/update
    meeting records in Sales OS.
    """
    try:
        meetings = await service.sync_from_calendar(
            user_id=current_user.id,
            request=request,
        )
        return [service.to_meeting_schema(m) for m in meetings]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Prep Brief Endpoints
# ============================================================================

@router.post("/briefs/generate", response_model=PrepBriefStatusResponse)
async def generate_prep_brief(
    request: PrepBriefGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> PrepBriefStatusResponse:
    """
    Generate a prep brief for a meeting.

    The brief will be generated asynchronously. Use the status endpoint
    to check progress, or poll the brief endpoint until complete.

    Includes:
    - Attendee profiles (from enrichment)
    - Company research summary
    - Previous call history
    - SPICED context from prior interactions
    - Suggested agenda
    - Suggested questions
    - Content recommendations
    """
    try:
        # Start generation (could be async via background task for long operations)
        brief = await service.generate_prep_brief(
            user_id=current_user.id,
            request=request,
        )

        return PrepBriefStatusResponse(
            meeting_id=request.meeting_id,
            brief_id=brief.id,
            status=brief.status,
            message="Brief generated successfully" if brief.status == PrepStatus.COMPLETED else "Generation in progress",
            generated_at=brief.generated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate brief: {str(e)}")


@router.get("/briefs/{meeting_id}", response_model=MeetingPrepBriefSchema)
async def get_prep_brief(
    meeting_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> MeetingPrepBriefSchema:
    """
    Get the prep brief for a meeting.

    Returns the full brief content if available. This endpoint also marks
    the brief as "viewed" for analytics.
    """
    brief = await service.get_prep_brief(meeting_id, current_user.id)
    if not brief:
        raise HTTPException(
            status_code=404,
            detail="No prep brief found for this meeting"
        )
    return service.to_brief_schema(brief)


@router.get("/briefs/{meeting_id}/status", response_model=PrepBriefStatusResponse)
async def get_brief_status(
    meeting_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> PrepBriefStatusResponse:
    """
    Get the status of prep brief generation.

    Use this to poll for completion when generating briefs asynchronously.
    """
    meeting = await service.get_meeting(meeting_id, current_user.id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting.prep_brief:
        return PrepBriefStatusResponse(
            meeting_id=meeting_id,
            status=PrepStatus.PENDING,
            message="No brief has been generated yet",
        )

    return PrepBriefStatusResponse(
        meeting_id=meeting_id,
        brief_id=meeting.prep_brief.id,
        status=meeting.prep_brief.status,
        message=meeting.prep_brief.generation_error if meeting.prep_brief.status == PrepStatus.FAILED else None,
        generated_at=meeting.prep_brief.generated_at,
    )


@router.post("/briefs/{meeting_id}/regenerate", response_model=PrepBriefStatusResponse)
async def regenerate_prep_brief(
    meeting_id: UUID,
    delivery_methods: list[DeliveryMethod] = Query(default=[DeliveryMethod.IN_APP]),
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> PrepBriefStatusResponse:
    """
    Force regenerate a prep brief.

    Use this when you want to refresh the brief with updated information,
    or if the initial generation failed.
    """
    try:
        brief = await service.regenerate_prep_brief(
            meeting_id=meeting_id,
            user_id=current_user.id,
            delivery_methods=delivery_methods,
        )

        return PrepBriefStatusResponse(
            meeting_id=meeting_id,
            brief_id=brief.id,
            status=brief.status,
            message="Brief regenerated successfully" if brief.status == PrepStatus.COMPLETED else "Regeneration in progress",
            generated_at=brief.generated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/briefs/bulk-generate", response_model=list[PrepBriefStatusResponse])
async def bulk_generate_briefs(
    request: BulkPrepGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> list[PrepBriefStatusResponse]:
    """
    Bulk generate prep briefs for multiple meetings.

    You can either specify meeting IDs directly, or use a date range
    to generate briefs for all meetings in that period.
    """
    briefs = await service.bulk_generate_preps(
        user_id=current_user.id,
        meeting_ids=request.meeting_ids,
        date_range_start=request.date_range_start,
        date_range_end=request.date_range_end,
        delivery_methods=request.delivery_methods,
    )

    return [
        PrepBriefStatusResponse(
            meeting_id=b.meeting_id,
            brief_id=b.id,
            status=b.status,
            generated_at=b.generated_at,
        )
        for b in briefs
    ]


# ============================================================================
# Delivery Endpoints
# ============================================================================

@router.post("/briefs/{brief_id}/deliver", response_model=DeliveryStatusResponse)
async def deliver_prep_brief(
    brief_id: UUID,
    request: PrepBriefDeliveryRequest,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> DeliveryStatusResponse:
    """
    Deliver a prep brief via specified methods.

    Available delivery methods:
    - email: Send to user's email
    - in_app: Mark as available in app (default)
    - calendar: Attach to calendar event
    - all: Use all delivery methods
    """
    # Get the brief
    from sqlalchemy import select
    from app.models.meetingprep import MeetingPrepBrief

    result = await service.db.execute(
        select(MeetingPrepBrief).where(MeetingPrepBrief.id == brief_id)
    )
    brief = result.scalar_one_or_none()

    if not brief or brief.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Brief not found")

    if brief.status != PrepStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot deliver incomplete brief"
        )

    # Deliver
    await service._deliver_brief(brief, request.delivery_methods)

    return DeliveryStatusResponse(
        brief_id=brief.id,
        email_sent=brief.email_sent,
        email_sent_at=brief.email_sent_at,
        calendar_attached=brief.calendar_attached,
        in_app_available=True,
    )


@router.get("/briefs/{brief_id}/delivery-status", response_model=DeliveryStatusResponse)
async def get_delivery_status(
    brief_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> DeliveryStatusResponse:
    """Get the delivery status of a prep brief."""
    from sqlalchemy import select
    from app.models.meetingprep import MeetingPrepBrief

    result = await service.db.execute(
        select(MeetingPrepBrief).where(MeetingPrepBrief.id == brief_id)
    )
    brief = result.scalar_one_or_none()

    if not brief or brief.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Brief not found")

    return DeliveryStatusResponse(
        brief_id=brief.id,
        email_sent=brief.email_sent,
        email_sent_at=brief.email_sent_at,
        calendar_attached=brief.calendar_attached,
        in_app_available=True,
    )


# ============================================================================
# Automation Endpoints
# ============================================================================

@router.post("/automation/trigger-auto-prep")
async def trigger_auto_prep(
    hours_before_meeting: int = Query(24, ge=1, le=72),
    current_user: User = Depends(get_current_user),
    service: MeetingPrepService = Depends(get_meeting_prep_service),
) -> dict:
    """
    Manually trigger auto-prep generation.

    This is typically run by a scheduled job, but can be triggered manually
    for testing or catching up on missed runs.

    Generates briefs for meetings within the specified time window.
    """
    briefs = await service.schedule_auto_prep(
        user_id=current_user.id,
        hours_before_meeting=hours_before_meeting,
    )

    return {
        "message": f"Generated {len(briefs)} prep briefs",
        "briefs_generated": len(briefs),
        "brief_ids": [str(b.id) for b in briefs],
    }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for the meeting prep service."""
    return {
        "service": "meeting-prep",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
