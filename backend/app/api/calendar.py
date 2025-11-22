"""
Calendar API Routes

Endpoints for calendar integration management, event listing, and meeting-transcript linking.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ..models.calendar import (
    CalendarProvider,
    CalendarIntegration,
    CalendarIntegrationCreate,
    CalendarIntegrationResponse,
    CalendarEvent,
    CalendarEventResponse,
    CalendarEventFilter,
    CalendarEventList,
    MeetingTranscriptLink,
    MeetingTranscriptLinkCreate,
    MeetingTranscriptLinkResponse,
    OAuthCallback,
    SyncRequest,
    SyncResult,
    CalendarWidgetData,
    UpcomingMeeting,
)
from ..integrations.calendar import (
    GoogleOAuthHandler,
    OutlookOAuthHandler,
    GoogleCalendarConfig,
    OutlookCalendarConfig,
    CalendarSyncHandler,
    MeetingTranscriptLinker,
    get_calendar_client,
)
from ..integrations.calendar.handlers import OAuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# Response models
class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class OAuthURLResponse(BaseModel):
    """OAuth authorization URL response."""
    authorization_url: str
    state: str
    provider: CalendarProvider


# In-memory storage for demo (replace with database in production)
_oauth_states: dict = {}
_integrations: dict = {}
_events: dict = {}
_links: dict = {}


# Helper functions

def get_google_config() -> GoogleCalendarConfig:
    """Get Google Calendar configuration from environment."""
    # In production, these would come from environment variables
    return GoogleCalendarConfig(
        client_id="your-google-client-id",
        client_secret="your-google-client-secret",
        redirect_uri="http://localhost:8000/api/calendar/oauth/callback/google",
    )


def get_outlook_config() -> OutlookCalendarConfig:
    """Get Outlook configuration from environment."""
    return OutlookCalendarConfig(
        client_id="your-outlook-client-id",
        client_secret="your-outlook-client-secret",
        redirect_uri="http://localhost:8000/api/calendar/oauth/callback/outlook",
    )


def get_current_user_id() -> UUID:
    """Get current authenticated user ID (placeholder)."""
    # In production, this would extract user from JWT token
    return UUID("00000000-0000-0000-0000-000000000001")


def get_current_org_id() -> UUID:
    """Get current organization ID (placeholder)."""
    return UUID("00000000-0000-0000-0000-000000000001")


# ============================================================================
# OAuth Endpoints
# ============================================================================

@router.get(
    "/oauth/connect/{provider}",
    response_model=OAuthURLResponse,
    summary="Initiate OAuth connection",
    description="Generate OAuth authorization URL for connecting a calendar provider.",
)
async def connect_calendar(
    provider: CalendarProvider,
    redirect_uri: Optional[str] = None,
):
    """
    Initiate OAuth flow for connecting a calendar provider.

    Args:
        provider: Calendar provider (google or outlook)
        redirect_uri: Optional custom redirect URI after OAuth

    Returns:
        Authorization URL and state for OAuth flow
    """
    user_id = get_current_user_id()
    org_id = get_current_org_id()

    if provider == CalendarProvider.GOOGLE:
        config = get_google_config()
        oauth_handler = GoogleOAuthHandler(config)
    elif provider == CalendarProvider.OUTLOOK:
        config = get_outlook_config()
        oauth_handler = OutlookOAuthHandler(config)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )

    # Generate state for CSRF protection
    state = oauth_handler.generate_state()

    # Store state for verification
    _oauth_states[state] = {
        "provider": provider.value,
        "user_id": str(user_id),
        "org_id": str(org_id),
        "redirect_uri": redirect_uri or "/dashboard",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Generate authorization URL
    auth_url = oauth_handler.get_authorization_url(
        state=state,
        redirect_uri=config.redirect_uri,
    )

    return OAuthURLResponse(
        authorization_url=auth_url,
        state=state,
        provider=provider,
    )


@router.get(
    "/oauth/callback/{provider}",
    summary="OAuth callback handler",
    description="Handle OAuth callback from calendar provider.",
)
async def oauth_callback(
    provider: CalendarProvider,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handle OAuth callback from calendar provider.

    This endpoint receives the authorization code from the provider
    and exchanges it for access and refresh tokens.
    """
    # Check for OAuth errors
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error_description or error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state",
        )

    # Verify state
    stored_state = _oauth_states.pop(state, None)
    if not stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )

    if stored_state["provider"] != provider.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider mismatch",
        )

    # Get configuration and exchange code for tokens
    try:
        if provider == CalendarProvider.GOOGLE:
            config = get_google_config()
            oauth_handler = GoogleOAuthHandler(config)
        else:
            config = get_outlook_config()
            oauth_handler = OutlookOAuthHandler(config)

        tokens = await oauth_handler.exchange_code_for_tokens(
            code=code,
            redirect_uri=config.redirect_uri,
        )

        # Create integration record
        integration_id = uuid4()
        integration = {
            "id": str(integration_id),
            "org_id": stored_state["org_id"],
            "user_id": stored_state["user_id"],
            "provider": provider.value,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_expires_at": tokens["expires_at"].isoformat(),
            "status": "active",
            "sync_enabled": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        _integrations[str(integration_id)] = integration

        logger.info(f"Created calendar integration: {integration_id}")

        # Redirect to success page
        redirect_uri = stored_state.get("redirect_uri", "/dashboard")
        return RedirectResponse(
            url=f"{redirect_uri}?calendar_connected=true&provider={provider.value}",
            status_code=status.HTTP_302_FOUND,
        )

    except OAuthError as e:
        logger.error(f"OAuth token exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/oauth/disconnect/{integration_id}",
    response_model=APIResponse,
    summary="Disconnect calendar",
    description="Disconnect and revoke access to a calendar integration.",
)
async def disconnect_calendar(integration_id: UUID):
    """
    Disconnect a calendar integration.

    Revokes OAuth tokens and removes the integration.
    """
    integration = _integrations.get(str(integration_id))
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    # Revoke tokens
    provider = integration["provider"]
    if provider == "google":
        config = get_google_config()
        oauth_handler = GoogleOAuthHandler(config)
    else:
        config = get_outlook_config()
        oauth_handler = OutlookOAuthHandler(config)

    await oauth_handler.revoke_token(integration["access_token"])

    # Remove integration
    del _integrations[str(integration_id)]

    logger.info(f"Disconnected calendar integration: {integration_id}")

    return APIResponse(
        success=True,
        data={"message": "Calendar disconnected successfully"},
    )


# ============================================================================
# Integration Management Endpoints
# ============================================================================

@router.get(
    "/integrations",
    response_model=List[CalendarIntegrationResponse],
    summary="List calendar integrations",
    description="List all calendar integrations for the current organization.",
)
async def list_integrations():
    """List all calendar integrations for the current organization."""
    org_id = str(get_current_org_id())

    integrations = [
        CalendarIntegrationResponse(
            id=UUID(i["id"]),
            provider=CalendarProvider(i["provider"]),
            calendar_id=i.get("calendar_id"),
            status=i["status"],
            sync_enabled=i.get("sync_enabled", True),
            last_sync_at=datetime.fromisoformat(i["last_sync_at"])
            if i.get("last_sync_at") else None,
            created_at=datetime.fromisoformat(i["created_at"]),
        )
        for i in _integrations.values()
        if i["org_id"] == org_id
    ]

    return integrations


@router.get(
    "/integrations/{integration_id}",
    response_model=CalendarIntegrationResponse,
    summary="Get integration details",
    description="Get details of a specific calendar integration.",
)
async def get_integration(integration_id: UUID):
    """Get details of a specific calendar integration."""
    integration = _integrations.get(str(integration_id))
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    return CalendarIntegrationResponse(
        id=UUID(integration["id"]),
        provider=CalendarProvider(integration["provider"]),
        calendar_id=integration.get("calendar_id"),
        status=integration["status"],
        sync_enabled=integration.get("sync_enabled", True),
        last_sync_at=datetime.fromisoformat(integration["last_sync_at"])
        if integration.get("last_sync_at") else None,
        created_at=datetime.fromisoformat(integration["created_at"]),
    )


# ============================================================================
# Calendar Events Endpoints
# ============================================================================

@router.get(
    "/events",
    response_model=CalendarEventList,
    summary="List calendar events",
    description="List calendar events with optional filtering.",
)
async def list_events(
    provider: Optional[CalendarProvider] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    has_transcript: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List calendar events with filtering and pagination.

    Args:
        provider: Filter by calendar provider
        start_date: Filter events starting after this date
        end_date: Filter events ending before this date
        has_transcript: Filter by transcript linkage
        search: Search in event titles
        page: Page number
        page_size: Items per page
    """
    org_id = str(get_current_org_id())

    # Filter events
    filtered_events = []
    for event in _events.values():
        if event.get("org_id") != org_id:
            continue
        if provider and event.get("provider") != provider.value:
            continue
        if start_date and datetime.fromisoformat(event["start_time"]) < start_date:
            continue
        if end_date and datetime.fromisoformat(event["end_time"]) > end_date:
            continue
        if search and search.lower() not in event.get("title", "").lower():
            continue

        # Check transcript linkage if needed
        if has_transcript is not None:
            linked = any(
                link["event_id"] == event["id"]
                for link in _links.values()
            )
            if linked != has_transcript:
                continue

        filtered_events.append(event)

    # Sort by start time
    filtered_events.sort(key=lambda e: e["start_time"])

    # Paginate
    total = len(filtered_events)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_events = filtered_events[start_idx:end_idx]

    # Transform to response model
    items = []
    for event in page_events:
        # Check for linked transcript
        linked_transcript = next(
            (link for link in _links.values() if link["event_id"] == event["id"]),
            None,
        )

        items.append(CalendarEventResponse(
            id=UUID(event["id"]),
            title=event["title"],
            description=event.get("description"),
            start_time=datetime.fromisoformat(event["start_time"]),
            end_time=datetime.fromisoformat(event["end_time"]),
            timezone=event.get("timezone", "UTC"),
            location=event.get("location"),
            is_all_day=event.get("is_all_day", False),
            attendees=[],  # Simplified for demo
            meeting_link=None,
            status=event.get("status", "confirmed"),
            html_link=event.get("html_link"),
            provider=CalendarProvider(event["provider"]),
            transcript_id=UUID(linked_transcript["transcript_id"])
            if linked_transcript else None,
            has_transcript=linked_transcript is not None,
        ))

    return CalendarEventList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end_idx < total,
    )


@router.get(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
    summary="Get event details",
    description="Get details of a specific calendar event.",
)
async def get_event(event_id: UUID):
    """Get details of a specific calendar event."""
    event = _events.get(str(event_id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    linked_transcript = next(
        (link for link in _links.values() if link["event_id"] == str(event_id)),
        None,
    )

    return CalendarEventResponse(
        id=UUID(event["id"]),
        title=event["title"],
        description=event.get("description"),
        start_time=datetime.fromisoformat(event["start_time"]),
        end_time=datetime.fromisoformat(event["end_time"]),
        timezone=event.get("timezone", "UTC"),
        location=event.get("location"),
        is_all_day=event.get("is_all_day", False),
        attendees=[],
        meeting_link=None,
        status=event.get("status", "confirmed"),
        html_link=event.get("html_link"),
        provider=CalendarProvider(event["provider"]),
        transcript_id=UUID(linked_transcript["transcript_id"])
        if linked_transcript else None,
        has_transcript=linked_transcript is not None,
    )


# ============================================================================
# Sync Endpoints
# ============================================================================

@router.post(
    "/sync",
    response_model=SyncResult,
    summary="Sync calendar events",
    description="Trigger synchronization of calendar events.",
)
async def sync_calendar(request: SyncRequest):
    """
    Trigger synchronization of calendar events.

    This will fetch events from the connected calendar provider
    and update the local database.
    """
    integration = _integrations.get(str(request.integration_id))
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    provider = integration["provider"]

    try:
        # Get calendar client
        if provider == "google":
            config = get_google_config()
        else:
            config = get_outlook_config()

        client = get_calendar_client(
            provider=provider,
            config=config,
            access_token=integration["access_token"],
            refresh_token=integration["refresh_token"],
            token_expires_at=datetime.fromisoformat(integration["token_expires_at"]),
        )

        # Create sync handler
        sync_handler = CalendarSyncHandler(
            client=client,
            org_id=UUID(integration["org_id"]),
            integration_id=UUID(integration["id"]),
        )

        # Perform sync
        result = await sync_handler.sync_events(
            full_sync=request.full_sync,
            start_time=request.start_date,
            end_time=request.end_date,
        )

        # Update last sync time
        integration["last_sync_at"] = datetime.utcnow().isoformat()

        await client.close()

        return SyncResult(
            integration_id=request.integration_id,
            events_synced=result["events_synced"],
            events_created=result["events_created"],
            events_updated=result["events_updated"],
            events_deleted=result["events_deleted"],
            errors=result["errors"],
        )

    except Exception as e:
        logger.exception(f"Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


# ============================================================================
# Meeting-Transcript Linking Endpoints
# ============================================================================

@router.post(
    "/events/{event_id}/link-transcript",
    response_model=MeetingTranscriptLinkResponse,
    summary="Link meeting to transcript",
    description="Create a link between a calendar event and a transcript.",
)
async def link_meeting_to_transcript(
    event_id: UUID,
    transcript_id: UUID,
    notes: Optional[str] = None,
):
    """
    Create a link between a calendar event and a transcript.

    This allows associating call recordings/transcripts with
    their corresponding calendar meetings.
    """
    # Verify event exists
    event = _events.get(str(event_id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Check for existing link
    existing_link = next(
        (link for link in _links.values()
         if link["event_id"] == str(event_id) and link["transcript_id"] == str(transcript_id)),
        None,
    )
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Link already exists",
        )

    # Create link
    link_id = uuid4()
    link = {
        "id": str(link_id),
        "event_id": str(event_id),
        "transcript_id": str(transcript_id),
        "org_id": str(get_current_org_id()),
        "confidence_score": 1.0,
        "link_type": "manual",
        "notes": notes,
        "created_by": str(get_current_user_id()),
        "created_at": datetime.utcnow().isoformat(),
    }
    _links[str(link_id)] = link

    logger.info(f"Created meeting-transcript link: {link_id}")

    return MeetingTranscriptLinkResponse(
        id=link_id,
        event_id=event_id,
        transcript_id=transcript_id,
        confidence_score=1.0,
        link_type="manual",
        created_at=datetime.fromisoformat(link["created_at"]),
    )


@router.delete(
    "/events/{event_id}/unlink-transcript/{transcript_id}",
    response_model=APIResponse,
    summary="Unlink meeting from transcript",
    description="Remove the link between a calendar event and a transcript.",
)
async def unlink_meeting_from_transcript(event_id: UUID, transcript_id: UUID):
    """Remove the link between a calendar event and a transcript."""
    link_to_delete = None
    for link_id, link in _links.items():
        if link["event_id"] == str(event_id) and link["transcript_id"] == str(transcript_id):
            link_to_delete = link_id
            break

    if not link_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    del _links[link_to_delete]

    return APIResponse(
        success=True,
        data={"message": "Link removed successfully"},
    )


# ============================================================================
# Dashboard Widget Endpoints
# ============================================================================

@router.get(
    "/widget/upcoming",
    response_model=CalendarWidgetData,
    summary="Get calendar widget data",
    description="Get data for the upcoming meetings dashboard widget.",
)
async def get_calendar_widget_data(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get data for the calendar dashboard widget.

    Returns upcoming meetings and statistics for the dashboard.
    """
    org_id = str(get_current_org_id())
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)

    # Filter upcoming events
    upcoming_events = []
    for event in _events.values():
        if event.get("org_id") != org_id:
            continue
        event_start = datetime.fromisoformat(event["start_time"])
        if now <= event_start <= end_date:
            linked = any(
                link["event_id"] == event["id"]
                for link in _links.values()
            )
            upcoming_events.append(UpcomingMeeting(
                id=UUID(event["id"]),
                title=event["title"],
                start_time=event_start,
                end_time=datetime.fromisoformat(event["end_time"]),
                attendees_count=len(event.get("attendees", [])),
                has_transcript=linked,
                meeting_link=event.get("meeting_url"),
                provider=CalendarProvider(event["provider"]),
            ))

    # Sort by start time
    upcoming_events.sort(key=lambda e: e.start_time)

    # Calculate statistics
    meetings_today = sum(
        1 for e in upcoming_events
        if e.start_time <= today_end
    )
    meetings_this_week = sum(
        1 for e in upcoming_events
        if e.start_time <= week_end
    )
    total_integrations = sum(
        1 for i in _integrations.values()
        if i["org_id"] == org_id
    )

    return CalendarWidgetData(
        upcoming_meetings=upcoming_events[:limit],
        meetings_today=meetings_today,
        meetings_this_week=meetings_this_week,
        total_integrations=total_integrations,
        next_meeting=upcoming_events[0] if upcoming_events else None,
    )


@router.get(
    "/calendars",
    summary="List available calendars",
    description="List all calendars available in connected integrations.",
)
async def list_available_calendars(integration_id: UUID):
    """
    List all calendars available in a connected integration.

    This allows users to select which calendar to sync.
    """
    integration = _integrations.get(str(integration_id))
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    provider = integration["provider"]

    try:
        if provider == "google":
            config = get_google_config()
        else:
            config = get_outlook_config()

        client = get_calendar_client(
            provider=provider,
            config=config,
            access_token=integration["access_token"],
            refresh_token=integration["refresh_token"],
            token_expires_at=datetime.fromisoformat(integration["token_expires_at"]),
        )

        calendars = await client.list_calendars()
        await client.close()

        return {
            "success": True,
            "data": {
                "calendars": [cal.model_dump() for cal in calendars],
            },
        }

    except Exception as e:
        logger.exception(f"Failed to list calendars: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list calendars: {str(e)}",
        )
