"""Zoom API routes for OAuth, recordings, and transcripts."""

import logging
import secrets
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.integrations.zoom import ZoomClient
from app.integrations.zoom.exceptions import (
    ZoomAPIError,
    ZoomAuthenticationError,
    ZoomRecordingNotFoundError,
    ZoomTranscriptNotFoundError,
)
from app.models.zoom import (
    ZoomConnectResponse,
    ZoomAccount,
    ZoomRecording,
    ZoomRecordingListResponse,
    ZoomMeetingMetadata,
    ZoomTranscript,
    ParsedTranscript,
    ZoomOAuthTokens,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory token storage (replace with database in production)
# Key: user_id or account_id, Value: ZoomOAuthTokens
_token_store: Dict[str, ZoomOAuthTokens] = {}
_state_store: Dict[str, str] = {}  # state -> user_id mapping


def get_zoom_client(user_id: str = "default") -> ZoomClient:
    """Get a Zoom client with stored tokens for a user."""
    tokens = _token_store.get(user_id)
    return ZoomClient(tokens=tokens)


# ==================== OAuth Routes ====================


@router.get("/oauth/connect")
async def initiate_oauth(
    user_id: str = Query(default="default", description="User ID for token storage"),
    redirect_url: Optional[str] = Query(
        default=None, description="URL to redirect after OAuth completion"
    ),
) -> Dict[str, str]:
    """Initiate OAuth2 flow to connect a Zoom account.

    Returns the authorization URL to redirect the user to.
    """
    client = ZoomClient()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _state_store[state] = user_id

    auth_url = client.get_authorization_url(state=state)

    return {
        "authorization_url": auth_url,
        "state": state,
        "message": "Redirect user to authorization_url to complete OAuth flow",
    }


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Zoom"),
    state: Optional[str] = Query(default=None, description="State parameter for CSRF"),
) -> RedirectResponse:
    """Handle OAuth callback from Zoom.

    Exchanges the authorization code for tokens and stores them.
    """
    # Validate state
    user_id = "default"
    if state:
        user_id = _state_store.pop(state, "default")

    async with ZoomClient() as client:
        try:
            tokens = await client.exchange_code_for_tokens(code)
            _token_store[user_id] = tokens

            # Get user info to confirm connection
            client.tokens = tokens
            user = await client.get_current_user()

            logger.info(f"Successfully connected Zoom account: {user.email}")

            # Redirect to success page (configure this URL in your frontend)
            return RedirectResponse(
                url=f"{settings.cors_origins[0]}/settings/integrations?zoom=connected"
            )

        except ZoomAuthenticationError as e:
            logger.error(f"Zoom OAuth failed: {e}")
            return RedirectResponse(
                url=f"{settings.cors_origins[0]}/settings/integrations?zoom=failed&error={str(e)}"
            )


@router.get("/oauth/status")
async def get_oauth_status(
    user_id: str = Query(default="default", description="User ID to check"),
) -> Dict[str, Any]:
    """Check if a Zoom account is connected."""
    tokens = _token_store.get(user_id)

    if not tokens:
        return {
            "connected": False,
            "message": "No Zoom account connected",
        }

    # Try to get current user to verify token validity
    async with ZoomClient(tokens=tokens) as client:
        try:
            user = await client.get_current_user()
            return {
                "connected": True,
                "account": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                },
                "token_expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            }
        except ZoomAuthenticationError:
            # Token is invalid, remove it
            _token_store.pop(user_id, None)
            return {
                "connected": False,
                "message": "Token expired or invalid",
            }


@router.post("/oauth/disconnect")
async def disconnect_account(
    user_id: str = Query(default="default", description="User ID to disconnect"),
) -> Dict[str, str]:
    """Disconnect a Zoom account by removing stored tokens."""
    if user_id in _token_store:
        _token_store.pop(user_id)
        return {"status": "disconnected", "message": "Zoom account disconnected"}

    return {"status": "not_connected", "message": "No Zoom account was connected"}


# ==================== Account Routes ====================


@router.get("/account", response_model=ZoomAccount)
async def get_account(
    user_id: str = Query(default="default", description="User ID"),
):
    """Get the connected Zoom account information."""
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            return await client.get_current_user()
        except ZoomAuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))


# ==================== Recording Routes ====================


@router.get("/recordings", response_model=ZoomRecordingListResponse)
async def list_recordings(
    user_id: str = Query(default="default", description="User ID"),
    from_date: Optional[str] = Query(
        default=None, description="Start date (YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    page_size: int = Query(default=30, ge=1, le=300, description="Results per page"),
    next_page_token: Optional[str] = Query(
        default=None, description="Pagination token"
    ),
):
    """List cloud recordings for the connected Zoom account.

    Returns recordings from the specified date range with pagination support.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            return await client.list_recordings(
                from_date=from_date,
                to_date=to_date,
                page_size=page_size,
                next_page_token=next_page_token,
            )
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/recordings/{meeting_id}", response_model=ZoomRecording)
async def get_recording(
    meeting_id: str,
    user_id: str = Query(default="default", description="User ID"),
):
    """Get a specific recording by meeting ID."""
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            return await client.get_recording(meeting_id)
        except ZoomRecordingNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"Recording not found for meeting {meeting_id}"
            )
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ==================== Transcript Routes ====================


@router.get("/recordings/{meeting_id}/transcript", response_model=ZoomTranscript)
async def get_transcript(
    meeting_id: str,
    user_id: str = Query(default="default", description="User ID"),
):
    """Download and parse the transcript for a recording.

    Returns the raw content and parsed transcript with speaker identification.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            return await client.download_transcript(meeting_id)
        except ZoomTranscriptNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Transcript not available for meeting {meeting_id}",
            )
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/recordings/{meeting_id}/transcript/parsed", response_model=ParsedTranscript
)
async def get_parsed_transcript(
    meeting_id: str,
    user_id: str = Query(default="default", description="User ID"),
):
    """Get only the parsed transcript data for a recording.

    Returns structured transcript with timing and speaker information.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            transcript = await client.download_transcript(meeting_id)
            if not transcript.parsed:
                raise HTTPException(
                    status_code=500, detail="Failed to parse transcript"
                )
            return transcript.parsed
        except ZoomTranscriptNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Transcript not available for meeting {meeting_id}",
            )
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/recordings/{meeting_id}/transcript/text")
async def get_transcript_text(
    meeting_id: str,
    user_id: str = Query(default="default", description="User ID"),
) -> Dict[str, Any]:
    """Get the transcript as plain text.

    Returns the full transcript as readable text with speaker labels.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            transcript = await client.download_transcript(meeting_id)
            full_text = (
                transcript.parsed.get_full_text() if transcript.parsed else ""
            )
            return {
                "meeting_id": meeting_id,
                "topic": transcript.parsed.meeting_topic if transcript.parsed else None,
                "text": full_text,
                "duration_seconds": transcript.parsed.total_duration
                if transcript.parsed
                else 0,
                "speakers": transcript.parsed.speakers if transcript.parsed else [],
            }
        except ZoomTranscriptNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Transcript not available for meeting {meeting_id}",
            )
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ==================== Meeting Metadata Routes ====================


@router.get("/meetings/{meeting_id}/metadata", response_model=ZoomMeetingMetadata)
async def get_meeting_metadata(
    meeting_id: str,
    user_id: str = Query(default="default", description="User ID"),
):
    """Get comprehensive metadata for a meeting.

    Includes meeting details, recording availability, and transcript status.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            return await client.get_meeting_metadata(meeting_id)
        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ==================== Utility Routes ====================


@router.get("/recordings/with-transcripts")
async def list_recordings_with_transcripts(
    user_id: str = Query(default="default", description="User ID"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    page_size: int = Query(default=30, ge=1, le=100),
) -> Dict[str, Any]:
    """List recordings that have transcripts available.

    Filters recordings to only return those with transcript files.
    """
    tokens = _token_store.get(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No Zoom account connected")

    async with ZoomClient(tokens=tokens) as client:
        try:
            recordings = await client.list_recordings(
                from_date=from_date,
                to_date=to_date,
                page_size=page_size,
            )

            # Filter to recordings with transcripts
            recordings_with_transcripts = []
            for meeting in recordings.meetings:
                transcript_file = await client.get_transcript_file(meeting)
                if transcript_file:
                    recordings_with_transcripts.append(
                        {
                            "meeting_id": str(meeting.id),
                            "uuid": meeting.uuid,
                            "topic": meeting.topic,
                            "start_time": meeting.start_time.isoformat(),
                            "duration_minutes": meeting.duration,
                            "host_email": meeting.host_email,
                            "transcript_file_type": transcript_file.file_type,
                        }
                    )

            return {
                "total": len(recordings_with_transcripts),
                "recordings": recordings_with_transcripts,
            }

        except ZoomAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))
