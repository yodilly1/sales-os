"""
Deal Room API Endpoints

RESTful API for managing digital deal rooms.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.models.dealroom import (
    DealRoomStatus, ContentType, AccessLevel,
    DealRoomCreateRequest, DealRoomUpdateRequest, DealRoomResponse, DealRoomListResponse,
    SectionCreateRequest, SectionUpdateRequest, SectionResponse,
    ContentCreateRequest, ContentUpdateRequest, ContentResponse,
    ActionPlanItemCreateRequest, ActionPlanItemUpdateRequest, ActionPlanItemResponse,
    InvitationCreateRequest, InvitationResponse,
    AccessVerificationRequest, AccessVerificationResponse,
    PublicDealRoomResponse, AnalyticsSummaryResponse, ViewEventResponse,
)
from backend.app.services.dealroom import (
    DealRoomService, DealRoomAnalyticsService, DealRoomAccessService,
)

# Placeholder imports - these will be implemented by other agents
# from backend.app.core.auth import get_current_user, requires_role
# from backend.app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dealrooms", tags=["Deal Rooms"])


# =============================================================================
# DEPENDENCY PLACEHOLDERS
# =============================================================================

# These will be replaced with actual implementations from AGENT-011 and AGENT-012

def get_db():
    """Get database session - placeholder for AGENT-011."""
    # This will be implemented by the database agent
    raise NotImplementedError("Database session dependency not yet implemented")


def get_current_user():
    """Get current authenticated user - placeholder for AGENT-012."""
    # This will be implemented by the auth agent
    class MockUser:
        id = UUID('00000000-0000-0000-0000-000000000001')
        team_id = UUID('00000000-0000-0000-0000-000000000002')
        email = "user@example.com"
    return MockUser()


def requires_auth(func):
    """Authentication decorator - placeholder for AGENT-012."""
    return func


def requires_role(role: str):
    """Role-based access decorator - placeholder for AGENT-012."""
    def decorator(func):
        return func
    return decorator


def get_base_url(request: Request) -> str:
    """Extract base URL from request."""
    return f"{request.url.scheme}://{request.url.netloc}"


# =============================================================================
# SERVICE FACTORIES
# =============================================================================

def get_deal_room_service(db: Session = Depends(get_db)) -> DealRoomService:
    """Get deal room service instance."""
    return DealRoomService(db)


def get_analytics_service(db: Session = Depends(get_db)) -> DealRoomAnalyticsService:
    """Get analytics service instance."""
    return DealRoomAnalyticsService(db)


def get_access_service(db: Session = Depends(get_db)) -> DealRoomAccessService:
    """Get access service instance."""
    return DealRoomAccessService(db)


# =============================================================================
# DEAL ROOM CRUD ENDPOINTS
# =============================================================================

@router.post("", response_model=DealRoomResponse, status_code=201)
async def create_deal_room(
    request: DealRoomCreateRequest,
    req: Request,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Create a new deal room.

    Creates a branded shareable space for prospect engagement.
    The deal room starts in DRAFT status and must be published to be accessible.
    """
    deal_room = service.create_deal_room(
        request=request,
        owner_id=current_user.id,
        team_id=current_user.team_id,
    )

    return service.to_response(deal_room, get_base_url(req))


@router.get("", response_model=DealRoomListResponse)
async def list_deal_rooms(
    status: Optional[DealRoomStatus] = None,
    search: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    req: Request = None,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    List deal rooms.

    Returns paginated list of deal rooms owned by the current user or their team.
    """
    deal_rooms, total = service.list_deal_rooms(
        owner_id=current_user.id,
        team_id=current_user.team_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )

    base_url = get_base_url(req) if req else None

    return DealRoomListResponse(
        items=[service.to_response(dr, base_url) for dr in deal_rooms],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{deal_room_id}", response_model=DealRoomResponse)
async def get_deal_room(
    deal_room_id: UUID,
    req: Request,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get a deal room by ID.

    Returns full deal room details including branding, settings, and analytics summary.
    """
    deal_room = service.get_deal_room(deal_room_id)

    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    # Check ownership
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return service.to_response(deal_room, get_base_url(req))


@router.patch("/{deal_room_id}", response_model=DealRoomResponse)
async def update_deal_room(
    deal_room_id: UUID,
    request: DealRoomUpdateRequest,
    req: Request,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Update a deal room.

    Updates deal room properties including branding, settings, and access controls.
    """
    # Verify ownership first
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = service.update_deal_room(deal_room_id, request)
    return service.to_response(updated, get_base_url(req))


@router.delete("/{deal_room_id}", status_code=204)
async def delete_deal_room(
    deal_room_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Delete a deal room.

    Permanently deletes the deal room and all its contents. This action cannot be undone.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.delete_deal_room(deal_room_id)
    return Response(status_code=204)


@router.post("/{deal_room_id}/publish", response_model=DealRoomResponse)
async def publish_deal_room(
    deal_room_id: UUID,
    req: Request,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Publish a deal room.

    Makes the deal room accessible via its shareable link.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    published = service.publish_deal_room(deal_room_id)
    return service.to_response(published, get_base_url(req))


@router.post("/{deal_room_id}/archive", response_model=DealRoomResponse)
async def archive_deal_room(
    deal_room_id: UUID,
    req: Request,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Archive a deal room.

    Deactivates the deal room, making it inaccessible via its shareable link.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    archived = service.archive_deal_room(deal_room_id)
    return service.to_response(archived, get_base_url(req))


@router.post("/{deal_room_id}/duplicate", response_model=DealRoomResponse, status_code=201)
async def duplicate_deal_room(
    deal_room_id: UUID,
    new_title: str = Query(..., min_length=1, max_length=255),
    req: Request = None,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Duplicate a deal room.

    Creates a copy of the deal room with all its content and settings.
    The duplicate starts in DRAFT status.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    duplicated = service.duplicate_deal_room(deal_room_id, new_title, current_user.id)
    if not duplicated:
        raise HTTPException(status_code=500, detail="Failed to duplicate deal room")

    return service.to_response(duplicated, get_base_url(req) if req else None)


# =============================================================================
# SECTION ENDPOINTS
# =============================================================================

@router.post("/{deal_room_id}/sections", response_model=SectionResponse, status_code=201)
async def create_section(
    deal_room_id: UUID,
    request: SectionCreateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Create a section in a deal room.

    Sections organize content into logical groups (folders).
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    section = service.create_section(deal_room_id, request)
    return SectionResponse.model_validate(section)


@router.get("/{deal_room_id}/sections", response_model=List[SectionResponse])
async def list_sections(
    deal_room_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    List sections in a deal room.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    sections = service.list_sections(deal_room_id)
    return [SectionResponse.model_validate(s) for s in sections]


@router.patch("/{deal_room_id}/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    deal_room_id: UUID,
    section_id: UUID,
    request: SectionUpdateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Update a section.
    """
    section = service.get_section(section_id)
    if not section or section.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Section not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = service.update_section(section_id, request)
    return SectionResponse.model_validate(updated)


@router.delete("/{deal_room_id}/sections/{section_id}", status_code=204)
async def delete_section(
    deal_room_id: UUID,
    section_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Delete a section.

    Contents in the section will be moved to unsectioned.
    """
    section = service.get_section(section_id)
    if not section or section.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Section not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.delete_section(section_id)
    return Response(status_code=204)


@router.post("/{deal_room_id}/sections/reorder", status_code=200)
async def reorder_sections(
    deal_room_id: UUID,
    section_ids: List[UUID],
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Reorder sections in a deal room.

    Pass the section IDs in the desired order.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.reorder_sections(deal_room_id, section_ids)
    return {"success": True}


# =============================================================================
# CONTENT ENDPOINTS
# =============================================================================

@router.post("/{deal_room_id}/contents", response_model=ContentResponse, status_code=201)
async def add_content(
    deal_room_id: UUID,
    request: ContentCreateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Add content to a deal room.

    Supports various content types: proposals, decks, case studies, pricing, contracts, etc.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    content = service.add_content(deal_room_id, request, current_user.id)
    return ContentResponse.model_validate(content)


@router.get("/{deal_room_id}/contents", response_model=List[ContentResponse])
async def list_contents(
    deal_room_id: UUID,
    section_id: Optional[UUID] = None,
    content_type: Optional[ContentType] = None,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    List contents in a deal room.

    Optionally filter by section or content type.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    contents = service.list_contents(deal_room_id, section_id, content_type)
    return [ContentResponse.model_validate(c) for c in contents]


@router.get("/{deal_room_id}/contents/{content_id}", response_model=ContentResponse)
async def get_content(
    deal_room_id: UUID,
    content_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get a specific content item.
    """
    content = service.get_content(content_id)
    if not content or content.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Content not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ContentResponse.model_validate(content)


@router.patch("/{deal_room_id}/contents/{content_id}", response_model=ContentResponse)
async def update_content(
    deal_room_id: UUID,
    content_id: UUID,
    request: ContentUpdateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Update a content item.
    """
    content = service.get_content(content_id)
    if not content or content.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Content not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = service.update_content(content_id, request)
    return ContentResponse.model_validate(updated)


@router.delete("/{deal_room_id}/contents/{content_id}", status_code=204)
async def delete_content(
    deal_room_id: UUID,
    content_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Delete a content item.
    """
    content = service.get_content(content_id)
    if not content or content.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Content not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.delete_content(content_id)
    return Response(status_code=204)


@router.post("/{deal_room_id}/contents/reorder", status_code=200)
async def reorder_contents(
    deal_room_id: UUID,
    content_ids: List[UUID],
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Reorder contents in a deal room.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.reorder_contents(deal_room_id, content_ids)
    return {"success": True}


# =============================================================================
# ACTION PLAN ENDPOINTS
# =============================================================================

@router.post("/{deal_room_id}/action-plan", response_model=ActionPlanItemResponse, status_code=201)
async def add_action_plan_item(
    deal_room_id: UUID,
    request: ActionPlanItemCreateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Add an item to the mutual action plan.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    item = service.add_action_plan_item(deal_room_id, request)
    return ActionPlanItemResponse.model_validate(item)


@router.get("/{deal_room_id}/action-plan", response_model=List[ActionPlanItemResponse])
async def list_action_plan_items(
    deal_room_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    List action plan items in a deal room.
    """
    deal_room = service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    items = service.list_action_plan_items(deal_room_id)
    return [ActionPlanItemResponse.model_validate(i) for i in items]


@router.patch("/{deal_room_id}/action-plan/{item_id}", response_model=ActionPlanItemResponse)
async def update_action_plan_item(
    deal_room_id: UUID,
    item_id: UUID,
    request: ActionPlanItemUpdateRequest,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Update an action plan item.
    """
    item = service.get_action_plan_item(item_id)
    if not item or item.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Action plan item not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = service.update_action_plan_item(item_id, request)
    return ActionPlanItemResponse.model_validate(updated)


@router.delete("/{deal_room_id}/action-plan/{item_id}", status_code=204)
async def delete_action_plan_item(
    deal_room_id: UUID,
    item_id: UUID,
    service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Delete an action plan item.
    """
    item = service.get_action_plan_item(item_id)
    if not item or item.deal_room_id != deal_room_id:
        raise HTTPException(status_code=404, detail="Action plan item not found")

    deal_room = service.get_deal_room(deal_room_id)
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    service.delete_action_plan_item(item_id)
    return Response(status_code=204)


# =============================================================================
# INVITATION ENDPOINTS
# =============================================================================

@router.post("/{deal_room_id}/invitations", response_model=InvitationResponse, status_code=201)
async def create_invitation(
    deal_room_id: UUID,
    request: InvitationCreateRequest,
    background_tasks: BackgroundTasks,
    service: DealRoomAccessService = Depends(get_access_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Create an invitation to a deal room.

    Generates a unique invitation link that can be sent to the prospect.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    invitation = service.create_invitation(deal_room_id, request)
    if not invitation:
        raise HTTPException(status_code=500, detail="Failed to create invitation")

    # TODO: Add background task to send invitation email
    # background_tasks.add_task(send_invitation_email, invitation)

    return service.to_response(invitation)


@router.get("/{deal_room_id}/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    deal_room_id: UUID,
    include_accepted: bool = False,
    service: DealRoomAccessService = Depends(get_access_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    List invitations for a deal room.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    invitations = service.list_invitations(deal_room_id, include_accepted)
    return [service.to_response(i) for i in invitations]


@router.post("/{deal_room_id}/invitations/{invitation_id}/resend", response_model=InvitationResponse)
async def resend_invitation(
    deal_room_id: UUID,
    invitation_id: UUID,
    background_tasks: BackgroundTasks,
    service: DealRoomAccessService = Depends(get_access_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Resend an invitation.

    Generates a new invitation token and resends the email.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    invitation = service.resend_invitation(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # TODO: Add background task to resend invitation email
    # background_tasks.add_task(send_invitation_email, invitation)

    return service.to_response(invitation)


@router.delete("/{deal_room_id}/invitations/{invitation_id}", status_code=204)
async def delete_invitation(
    deal_room_id: UUID,
    invitation_id: UUID,
    service: DealRoomAccessService = Depends(get_access_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Delete an invitation.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not service.delete_invitation(invitation_id):
        raise HTTPException(status_code=404, detail="Invitation not found")

    return Response(status_code=204)


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/{deal_room_id}/analytics", response_model=AnalyticsSummaryResponse)
async def get_analytics(
    deal_room_id: UUID,
    service: DealRoomAnalyticsService = Depends(get_analytics_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get analytics summary for a deal room.

    Returns view counts, unique viewers, engagement metrics, and content performance.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return service.get_analytics_summary(deal_room_id)


@router.get("/{deal_room_id}/analytics/engagement")
async def get_engagement_score(
    deal_room_id: UUID,
    service: DealRoomAnalyticsService = Depends(get_analytics_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get engagement score for a deal room.

    Returns an overall engagement score with breakdown by factor.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return service.get_engagement_score(deal_room_id)


@router.get("/{deal_room_id}/analytics/weekly-report")
async def get_weekly_report(
    deal_room_id: UUID,
    service: DealRoomAnalyticsService = Depends(get_analytics_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get weekly engagement report for a deal room.

    Returns metrics for the past week with trend comparison.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return service.get_weekly_report(deal_room_id)


@router.get("/{deal_room_id}/analytics/viewer/{viewer_email}")
async def get_viewer_journey(
    deal_room_id: UUID,
    viewer_email: str,
    service: DealRoomAnalyticsService = Depends(get_analytics_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Get viewing journey for a specific viewer.

    Returns all sessions and content views for the specified email.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return service.get_viewer_journey(deal_room_id, viewer_email)


@router.get("/{deal_room_id}/analytics/export")
async def export_analytics(
    deal_room_id: UUID,
    service: DealRoomAnalyticsService = Depends(get_analytics_service),
    deal_room_service: DealRoomService = Depends(get_deal_room_service),
    current_user = Depends(get_current_user),
):
    """
    Export analytics data as CSV.
    """
    deal_room = deal_room_service.get_deal_room(deal_room_id)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if deal_room.owner_id != current_user.id and deal_room.team_id != current_user.team_id:
        raise HTTPException(status_code=403, detail="Access denied")

    csv_data = service.export_analytics_csv(deal_room_id)

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=dealroom-{deal_room.slug}-analytics.csv"
        }
    )


# =============================================================================
# PUBLIC VIEW ENDPOINTS
# =============================================================================

public_router = APIRouter(prefix="/room", tags=["Public Deal Room"])


@public_router.get("/{slug}")
async def get_public_deal_room(
    slug: str,
    service: DealRoomService = Depends(get_deal_room_service),
    access_service: DealRoomAccessService = Depends(get_access_service),
):
    """
    Get a deal room for public viewing.

    Returns the deal room if it's publicly accessible, or authentication requirements.
    """
    deal_room = service.get_deal_room_by_slug(slug)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    # Check access requirements
    auth_requirements = access_service.check_requires_auth(deal_room.id)

    if deal_room.access_level != AccessLevel.PUBLIC:
        return {
            "requires_auth": True,
            "auth_requirements": auth_requirements,
            "title": deal_room.title,
            "prospect_company": deal_room.prospect_company,
            "branding": {
                "logo_url": deal_room.logo_url,
                "primary_color": deal_room.primary_color,
            }
        }

    public_room = service.get_public_deal_room(slug)
    if not public_room:
        raise HTTPException(status_code=404, detail="Deal room not available")

    return public_room


@public_router.post("/{slug}/verify", response_model=AccessVerificationResponse)
async def verify_access(
    slug: str,
    request: AccessVerificationRequest,
    access_service: DealRoomAccessService = Depends(get_access_service),
):
    """
    Verify access to a deal room.

    Validates password, email, or invitation token and returns an access token.
    """
    deal_room, response = access_service.verify_access_by_slug(slug, request)

    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    return response


@public_router.post("/{slug}/track-view")
async def track_view(
    slug: str,
    request: Request,
    viewer_email: Optional[str] = None,
    viewer_name: Optional[str] = None,
    session_id: Optional[str] = None,
    service: DealRoomService = Depends(get_deal_room_service),
    analytics_service: DealRoomAnalyticsService = Depends(get_analytics_service),
):
    """
    Track a view event for a deal room.

    Called when a viewer accesses the deal room.
    """
    deal_room = service.get_deal_room_by_slug(slug)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    # Get client info
    viewer_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    view_event = analytics_service.record_view(
        deal_room_id=deal_room.id,
        viewer_email=viewer_email,
        viewer_name=viewer_name,
        viewer_ip=viewer_ip,
        user_agent=user_agent,
        session_id=session_id,
    )

    return {
        "session_id": view_event.session_id,
        "view_event_id": str(view_event.id),
    }


@public_router.post("/{slug}/track-content-view")
async def track_content_view(
    slug: str,
    content_id: UUID,
    view_event_id: UUID,
    time_spent_seconds: int = 0,
    scroll_depth_percent: int = 0,
    downloaded: bool = False,
    service: DealRoomService = Depends(get_deal_room_service),
    analytics_service: DealRoomAnalyticsService = Depends(get_analytics_service),
):
    """
    Track a content view event.

    Called when a viewer views specific content within the deal room.
    """
    deal_room = service.get_deal_room_by_slug(slug)
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    content_view = analytics_service.record_content_view(
        view_event_id=view_event_id,
        content_id=content_id,
        time_spent_seconds=time_spent_seconds,
        scroll_depth_percent=scroll_depth_percent,
        downloaded=downloaded,
    )

    return {"success": True, "content_view_id": str(content_view.id)}


@public_router.post("/{slug}/update-session-time")
async def update_session_time(
    slug: str,
    session_id: str,
    time_spent_seconds: int,
    analytics_service: DealRoomAnalyticsService = Depends(get_analytics_service),
):
    """
    Update the total time spent in a session.

    Called periodically to update engagement metrics.
    """
    analytics_service.update_session_time(session_id, time_spent_seconds)
    return {"success": True}


# Include the public router
# This would typically be done in main.py:
# app.include_router(public_router)
