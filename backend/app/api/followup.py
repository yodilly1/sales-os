"""
Follow-up automation API endpoints.

Provides REST API for generating, managing, and scheduling follow-ups
based on SPICED analysis from sales calls.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..models.followup import (
    ApprovalMode,
    FollowUpApprovalRequest,
    FollowUpBulkActionRequest,
    FollowUpContentRecommendation,
    FollowUpEmail,
    FollowUpGenerationRequest,
    FollowUpGenerationResponse,
    FollowUpListRequest,
    FollowUpMeetingSuggestion,
    FollowUpScheduleRequest,
    FollowUpSequence,
    FollowUpStatus,
    FollowUpTask,
    FollowUpType,
    ProspectContext,
    ScheduleConfig,
    SequenceStatus,
    SPICEDContext,
)
from ..services.followup import (
    ApprovalWorkflow,
    CRMSyncService,
    FollowUpGenerator,
    FollowUpScheduler,
    SequenceManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/followup", tags=["followup"])


# ============================================================================
# Response Models
# ============================================================================


class FollowUpListResponse(BaseModel):
    """Response for listing follow-ups."""
    items: list[FollowUpEmail | FollowUpTask | FollowUpContentRecommendation | FollowUpMeetingSuggestion]
    total: int
    limit: int
    offset: int


class SequenceListResponse(BaseModel):
    """Response for listing sequences."""
    items: list[FollowUpSequence]
    total: int
    limit: int
    offset: int


class SchedulePreviewResponse(BaseModel):
    """Response for schedule preview."""
    slots: list[datetime]


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""
    success_count: int
    failure_count: int
    results: dict[str, dict]


class SyncStatusResponse(BaseModel):
    """Response for sync status."""
    followup_id: str
    crm_synced: bool
    crm_object_id: Optional[str]
    synced_at: Optional[datetime]
    error_message: Optional[str]


# ============================================================================
# Dependency Injection
# ============================================================================


def get_generator() -> FollowUpGenerator:
    """Get follow-up generator instance."""
    return FollowUpGenerator()


def get_scheduler() -> FollowUpScheduler:
    """Get follow-up scheduler instance."""
    return FollowUpScheduler()


def get_workflow() -> ApprovalWorkflow:
    """Get approval workflow instance."""
    return ApprovalWorkflow()


def get_sequence_manager() -> SequenceManager:
    """Get sequence manager instance."""
    return SequenceManager()


def get_crm_sync() -> CRMSyncService:
    """Get CRM sync service instance."""
    return CRMSyncService()


# ============================================================================
# Generation Endpoints
# ============================================================================


@router.post(
    "/generate",
    response_model=FollowUpGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate follow-ups from call",
    description="Generate follow-up content based on SPICED analysis from a sales call.",
)
async def generate_followups(
    request: FollowUpGenerationRequest,
    generator: FollowUpGenerator = Depends(get_generator),
) -> FollowUpGenerationResponse:
    """
    Generate follow-ups from a call's SPICED analysis.

    This endpoint analyzes the SPICED context and generates:
    - Follow-up email drafts
    - Tasks and reminders
    - Content recommendations
    - Meeting suggestions
    """
    try:
        response = await generator.generate_followups(request)
        logger.info(
            f"Generated {response.total_items} follow-ups for call {request.call_id}",
            extra={
                "call_id": str(request.call_id),
                "emails": len(response.emails),
                "tasks": len(response.tasks),
                "recommendations": len(response.content_recommendations),
                "meetings": len(response.meeting_suggestions),
            },
        )
        return response
    except Exception as e:
        logger.error(f"Failed to generate follow-ups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate follow-ups: {str(e)}",
        )


@router.post(
    "/generate/quick",
    response_model=FollowUpGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Quick generate from call ID",
    description="Generate follow-ups using minimal input (call ID and prospect email).",
)
async def quick_generate_followups(
    call_id: UUID,
    prospect_name: str,
    prospect_email: str,
    prospect_company: str,
    sender_name: str,
    sender_company: str,
    situation: Optional[str] = None,
    pain: Optional[str] = None,
    impact: Optional[str] = None,
    critical_event: Optional[str] = None,
    action_items: Optional[list[str]] = Query(default=None),
    generator: FollowUpGenerator = Depends(get_generator),
) -> FollowUpGenerationResponse:
    """
    Quick generation endpoint with flattened parameters.

    Useful for simple integrations that don't want to build the full request object.
    """
    request = FollowUpGenerationRequest(
        call_id=call_id,
        spiced_context=SPICEDContext(
            situation=situation,
            pain=pain,
            impact=impact,
            critical_event=critical_event,
            action_items=action_items or [],
        ),
        prospect_context=ProspectContext(
            name=prospect_name,
            email=prospect_email,
            company=prospect_company,
        ),
        sender_name=sender_name,
        sender_company=sender_company,
    )

    return await generate_followups(request, generator)


# ============================================================================
# Follow-Up CRUD Endpoints
# ============================================================================


@router.get(
    "",
    response_model=FollowUpListResponse,
    summary="List follow-ups",
    description="List follow-ups with optional filtering.",
)
async def list_followups(
    prospect_id: Optional[UUID] = None,
    call_id: Optional[UUID] = None,
    status: Optional[FollowUpStatus] = None,
    type: Optional[FollowUpType] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FollowUpListResponse:
    """
    List follow-ups with optional filters.

    Supports filtering by prospect, call, status, and type.
    """
    # This would query the database
    # Placeholder implementation
    return FollowUpListResponse(
        items=[],
        total=0,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{followup_id}",
    summary="Get follow-up",
    description="Get a specific follow-up by ID.",
)
async def get_followup(
    followup_id: UUID,
):
    """Get a specific follow-up by ID."""
    # This would query the database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.put(
    "/{followup_id}",
    summary="Update follow-up",
    description="Update a follow-up's content or settings.",
)
async def update_followup(
    followup_id: UUID,
    updates: dict,
):
    """
    Update a follow-up.

    Only draft and pending approval follow-ups can be updated.
    """
    # This would update the database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.delete(
    "/{followup_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete follow-up",
    description="Delete a follow-up.",
)
async def delete_followup(followup_id: UUID):
    """
    Delete a follow-up.

    Only draft and cancelled follow-ups can be deleted.
    """
    # This would delete from the database
    pass


# ============================================================================
# Approval Endpoints
# ============================================================================


@router.post(
    "/{followup_id}/submit",
    summary="Submit for approval",
    description="Submit a follow-up for approval.",
)
async def submit_for_approval(
    followup_id: UUID,
    workflow: ApprovalWorkflow = Depends(get_workflow),
):
    """Submit a follow-up for approval."""
    # Would fetch follow-up from database and submit
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.post(
    "/{followup_id}/approve",
    summary="Approve follow-up",
    description="Approve or reject a follow-up.",
)
async def approve_followup(
    followup_id: UUID,
    request: FollowUpApprovalRequest,
    workflow: ApprovalWorkflow = Depends(get_workflow),
):
    """
    Approve or reject a follow-up.

    Can optionally include modifications and scheduling info.
    """
    # Would fetch follow-up and process approval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.get(
    "/approvals/pending",
    summary="Get pending approvals",
    description="Get all follow-ups pending approval.",
)
async def get_pending_approvals(
    limit: int = Query(default=50, ge=1, le=100),
    workflow: ApprovalWorkflow = Depends(get_workflow),
) -> FollowUpListResponse:
    """Get all follow-ups pending approval."""
    pending = await workflow.get_pending_approvals(limit=limit)
    return FollowUpListResponse(
        items=pending,
        total=len(pending),
        limit=limit,
        offset=0,
    )


# ============================================================================
# Scheduling Endpoints
# ============================================================================


@router.post(
    "/{followup_id}/schedule",
    summary="Schedule follow-up",
    description="Schedule a follow-up for delivery.",
)
async def schedule_followup(
    followup_id: UUID,
    request: FollowUpScheduleRequest,
    scheduler: FollowUpScheduler = Depends(get_scheduler),
):
    """
    Schedule a follow-up for a specific time.

    The time will be adjusted to fit within the schedule window
    unless force is specified.
    """
    # Would fetch follow-up and schedule
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.post(
    "/{followup_id}/reschedule",
    summary="Reschedule follow-up",
    description="Reschedule a scheduled follow-up.",
)
async def reschedule_followup(
    followup_id: UUID,
    new_time: datetime,
    scheduler: FollowUpScheduler = Depends(get_scheduler),
):
    """Reschedule a follow-up to a new time."""
    # Would fetch follow-up and reschedule
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.post(
    "/{followup_id}/cancel",
    summary="Cancel follow-up",
    description="Cancel a scheduled follow-up.",
)
async def cancel_followup(
    followup_id: UUID,
    scheduler: FollowUpScheduler = Depends(get_scheduler),
):
    """Cancel a scheduled follow-up."""
    # Would fetch follow-up and cancel
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.get(
    "/schedule/preview",
    response_model=SchedulePreviewResponse,
    summary="Preview schedule slots",
    description="Get available schedule slots for follow-ups.",
)
async def preview_schedule_slots(
    count: int = Query(default=10, ge=1, le=50),
    start_from: Optional[datetime] = None,
    scheduler: FollowUpScheduler = Depends(get_scheduler),
) -> SchedulePreviewResponse:
    """Get upcoming available schedule slots."""
    slots = scheduler.get_schedule_preview(count=count, start_from=start_from)
    return SchedulePreviewResponse(slots=slots)


@router.get(
    "/schedule/config",
    response_model=ScheduleConfig,
    summary="Get schedule config",
    description="Get the current scheduling configuration.",
)
async def get_schedule_config(
    scheduler: FollowUpScheduler = Depends(get_scheduler),
) -> ScheduleConfig:
    """Get the current scheduling configuration."""
    return scheduler.config


# ============================================================================
# Bulk Action Endpoints
# ============================================================================


@router.post(
    "/bulk/action",
    response_model=BulkActionResponse,
    summary="Bulk action",
    description="Perform bulk actions on multiple follow-ups.",
)
async def bulk_action(
    request: FollowUpBulkActionRequest,
    workflow: ApprovalWorkflow = Depends(get_workflow),
    scheduler: FollowUpScheduler = Depends(get_scheduler),
) -> BulkActionResponse:
    """
    Perform bulk actions on multiple follow-ups.

    Supported actions: approve, cancel, reschedule, send
    """
    results = {}
    success_count = 0
    failure_count = 0

    for followup_id in request.followup_ids:
        try:
            if request.action == "approve":
                # Would approve the follow-up
                results[str(followup_id)] = {"success": True}
                success_count += 1
            elif request.action == "cancel":
                # Would cancel the follow-up
                results[str(followup_id)] = {"success": True}
                success_count += 1
            elif request.action == "reschedule":
                if not request.schedule_at:
                    results[str(followup_id)] = {
                        "success": False,
                        "error": "schedule_at required for reschedule",
                    }
                    failure_count += 1
                else:
                    results[str(followup_id)] = {"success": True}
                    success_count += 1
            else:
                results[str(followup_id)] = {
                    "success": False,
                    "error": f"Unknown action: {request.action}",
                }
                failure_count += 1
        except Exception as e:
            results[str(followup_id)] = {"success": False, "error": str(e)}
            failure_count += 1

    return BulkActionResponse(
        success_count=success_count,
        failure_count=failure_count,
        results=results,
    )


# ============================================================================
# Sequence Endpoints
# ============================================================================


@router.post(
    "/sequences",
    response_model=FollowUpSequence,
    status_code=status.HTTP_201_CREATED,
    summary="Create sequence",
    description="Create a multi-touch follow-up sequence.",
)
async def create_sequence(
    name: str,
    prospect_id: UUID,
    steps: list[dict],
    call_id: Optional[UUID] = None,
    approval_mode: ApprovalMode = ApprovalMode.MANUAL,
    stop_on_reply: bool = True,
    manager: SequenceManager = Depends(get_sequence_manager),
) -> FollowUpSequence:
    """
    Create a new follow-up sequence.

    Sequences consist of multiple steps (emails, tasks, waits, conditions)
    that are executed in order with configurable delays.
    """
    sequence = await manager.create_sequence(
        name=name,
        prospect_id=prospect_id,
        steps=steps,
        call_id=call_id,
        approval_mode=approval_mode,
        stop_on_reply=stop_on_reply,
    )
    return sequence


@router.get(
    "/sequences",
    response_model=SequenceListResponse,
    summary="List sequences",
    description="List all sequences with optional filtering.",
)
async def list_sequences(
    prospect_id: Optional[UUID] = None,
    status: Optional[SequenceStatus] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SequenceListResponse:
    """List sequences with optional filters."""
    # Would query database
    return SequenceListResponse(
        items=[],
        total=0,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/sequences/{sequence_id}",
    response_model=FollowUpSequence,
    summary="Get sequence",
    description="Get a specific sequence by ID.",
)
async def get_sequence(sequence_id: UUID) -> FollowUpSequence:
    """Get a specific sequence by ID."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.post(
    "/sequences/{sequence_id}/start",
    summary="Start sequence",
    description="Start executing a sequence.",
)
async def start_sequence(
    sequence_id: UUID,
    manager: SequenceManager = Depends(get_sequence_manager),
):
    """Start executing a sequence."""
    # Would fetch sequence and start
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.post(
    "/sequences/{sequence_id}/pause",
    summary="Pause sequence",
    description="Pause an active sequence.",
)
async def pause_sequence(
    sequence_id: UUID,
    manager: SequenceManager = Depends(get_sequence_manager),
):
    """Pause an active sequence."""
    # Would fetch sequence and pause
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.post(
    "/sequences/{sequence_id}/resume",
    summary="Resume sequence",
    description="Resume a paused sequence.",
)
async def resume_sequence(
    sequence_id: UUID,
    manager: SequenceManager = Depends(get_sequence_manager),
):
    """Resume a paused sequence."""
    # Would fetch sequence and resume
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.post(
    "/sequences/{sequence_id}/cancel",
    summary="Cancel sequence",
    description="Cancel a sequence.",
)
async def cancel_sequence(
    sequence_id: UUID,
    manager: SequenceManager = Depends(get_sequence_manager),
):
    """Cancel a sequence."""
    # Would fetch sequence and cancel
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.get(
    "/sequences/{sequence_id}/status",
    summary="Get sequence status",
    description="Get detailed status of a sequence.",
)
async def get_sequence_status(
    sequence_id: UUID,
    manager: SequenceManager = Depends(get_sequence_manager),
) -> dict:
    """Get detailed status of a sequence."""
    # Would fetch sequence and get status
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sequence {sequence_id} not found",
    )


@router.get(
    "/sequences/templates",
    summary="Get sequence templates",
    description="Get available sequence templates.",
)
async def get_sequence_templates() -> dict:
    """Get available sequence templates."""
    from ..services.followup.sequence import SEQUENCE_TEMPLATES
    return SEQUENCE_TEMPLATES


# ============================================================================
# CRM Sync Endpoints
# ============================================================================


@router.post(
    "/{followup_id}/sync",
    response_model=SyncStatusResponse,
    summary="Sync to CRM",
    description="Sync a follow-up to the CRM.",
)
async def sync_to_crm(
    followup_id: UUID,
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    crm_sync: CRMSyncService = Depends(get_crm_sync),
) -> SyncStatusResponse:
    """Sync a follow-up to the CRM."""
    # Would fetch follow-up and sync
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Follow-up {followup_id} not found",
    )


@router.get(
    "/{followup_id}/sync/status",
    response_model=SyncStatusResponse,
    summary="Get sync status",
    description="Get the CRM sync status for a follow-up.",
)
async def get_sync_status(
    followup_id: UUID,
    crm_sync: CRMSyncService = Depends(get_crm_sync),
) -> SyncStatusResponse:
    """Get the CRM sync status for a follow-up."""
    record = crm_sync.get_sync_status(followup_id)
    if not record:
        return SyncStatusResponse(
            followup_id=str(followup_id),
            crm_synced=False,
            crm_object_id=None,
            synced_at=None,
            error_message=None,
        )

    return SyncStatusResponse(
        followup_id=str(followup_id),
        crm_synced=record.status.value == "synced",
        crm_object_id=record.crm_object_id,
        synced_at=record.synced_at,
        error_message=record.error_message,
    )


@router.post(
    "/sync/bulk",
    summary="Bulk sync to CRM",
    description="Sync multiple follow-ups to CRM.",
)
async def bulk_sync_to_crm(
    followup_ids: list[UUID],
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    crm_sync: CRMSyncService = Depends(get_crm_sync),
) -> BulkActionResponse:
    """Bulk sync multiple follow-ups to CRM."""
    # Would fetch follow-ups and bulk sync
    return BulkActionResponse(
        success_count=0,
        failure_count=len(followup_ids),
        results={str(id): {"error": "Not implemented"} for id in followup_ids},
    )


# ============================================================================
# Email-specific Endpoints
# ============================================================================


@router.get(
    "/emails",
    summary="List email follow-ups",
    description="List email follow-ups with optional filtering.",
)
async def list_email_followups(
    prospect_id: Optional[UUID] = None,
    status: Optional[FollowUpStatus] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FollowUpListResponse:
    """List email follow-ups."""
    # Would query database filtered by type=email
    return FollowUpListResponse(
        items=[],
        total=0,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/emails/{email_id}/send",
    summary="Send email",
    description="Send an approved email follow-up immediately.",
)
async def send_email(
    email_id: UUID,
    scheduler: FollowUpScheduler = Depends(get_scheduler),
):
    """Send an approved email follow-up immediately."""
    # Would fetch email and send
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Email {email_id} not found",
    )


# ============================================================================
# Task-specific Endpoints
# ============================================================================


@router.get(
    "/tasks",
    summary="List task follow-ups",
    description="List task follow-ups with optional filtering.",
)
async def list_task_followups(
    prospect_id: Optional[UUID] = None,
    status: Optional[FollowUpStatus] = None,
    due_before: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FollowUpListResponse:
    """List task follow-ups."""
    # Would query database filtered by type=task
    return FollowUpListResponse(
        items=[],
        total=0,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/tasks/{task_id}/complete",
    summary="Complete task",
    description="Mark a task as completed.",
)
async def complete_task(
    task_id: UUID,
    completion_notes: Optional[str] = None,
):
    """Mark a task as completed."""
    # Would fetch task and mark complete
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found",
    )


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get(
    "/analytics/summary",
    summary="Get analytics summary",
    description="Get summary analytics for follow-ups.",
)
async def get_analytics_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Get summary analytics for follow-ups."""
    # Would aggregate analytics data
    return {
        "total_generated": 0,
        "total_sent": 0,
        "pending_approval": 0,
        "scheduled": 0,
        "by_type": {
            "email": 0,
            "task": 0,
            "content_recommendation": 0,
            "meeting_suggestion": 0,
        },
        "email_engagement": {
            "open_rate": 0.0,
            "click_rate": 0.0,
            "reply_rate": 0.0,
        },
        "active_sequences": 0,
        "completed_sequences": 0,
    }


@router.get(
    "/analytics/by-call/{call_id}",
    summary="Get follow-ups by call",
    description="Get all follow-ups generated from a specific call.",
)
async def get_followups_by_call(
    call_id: UUID,
) -> FollowUpListResponse:
    """Get all follow-ups generated from a specific call."""
    # Would query by call_id
    return FollowUpListResponse(
        items=[],
        total=0,
        limit=100,
        offset=0,
    )
