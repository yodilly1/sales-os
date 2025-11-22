"""Zoom API client with OAuth2 authentication."""

import base64
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.models.zoom import (
    ZoomAccount,
    ZoomOAuthTokens,
    ZoomRecording,
    ZoomRecordingFile,
    ZoomRecordingListResponse,
    ZoomMeeting,
    ZoomMeetingMetadata,
    ZoomTranscript,
    ParsedTranscript,
    RecordingType,
)
from app.integrations.zoom.exceptions import (
    ZoomAPIError,
    ZoomAuthenticationError,
    ZoomRateLimitError,
    ZoomRecordingNotFoundError,
    ZoomTranscriptNotFoundError,
    ZoomTokenExpiredError,
    ZoomWebhookValidationError,
)
from app.integrations.zoom.parsers import get_parser

logger = logging.getLogger(__name__)


class ZoomClient:
    """Zoom API client with OAuth2 authentication and token management."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        tokens: Optional[ZoomOAuthTokens] = None,
    ):
        """Initialize the Zoom client.

        Args:
            client_id: Zoom OAuth app client ID
            client_secret: Zoom OAuth app client secret
            redirect_uri: OAuth redirect URI
            tokens: Pre-existing OAuth tokens
        """
        self.client_id = client_id or settings.zoom_client_id
        self.client_secret = client_secret or settings.zoom_client_secret
        self.redirect_uri = redirect_uri or settings.zoom_redirect_uri
        self.api_base_url = settings.zoom_api_base_url
        self.oauth_base_url = settings.zoom_oauth_base_url
        self.tokens = tokens
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating one if necessary."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    # ==================== OAuth2 Methods ====================

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the OAuth2 authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            The authorization URL to redirect users to
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        if state:
            params["state"] = state

        return f"{self.oauth_base_url}/authorize?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> ZoomOAuthTokens:
        """Exchange an authorization code for access and refresh tokens.

        Args:
            code: The authorization code from OAuth callback

        Returns:
            ZoomOAuthTokens with access and refresh tokens
        """
        auth_header = self._get_basic_auth_header()

        response = await self.http_client.post(
            f"{self.oauth_base_url}/token",
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
        )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise ZoomAuthenticationError(
                f"Failed to exchange code: {error_data.get('reason', response.text)}"
            )

        data = response.json()
        self.tokens = ZoomOAuthTokens(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
            scope=data.get("scope", ""),
            expires_at=datetime.utcnow() + timedelta(seconds=data["expires_in"]),
        )

        return self.tokens

    async def refresh_access_token(self) -> ZoomOAuthTokens:
        """Refresh the access token using the refresh token.

        Returns:
            Updated ZoomOAuthTokens
        """
        if not self.tokens or not self.tokens.refresh_token:
            raise ZoomAuthenticationError("No refresh token available")

        auth_header = self._get_basic_auth_header()

        response = await self.http_client.post(
            f"{self.oauth_base_url}/token",
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.tokens.refresh_token,
            },
        )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise ZoomAuthenticationError(
                f"Failed to refresh token: {error_data.get('reason', response.text)}"
            )

        data = response.json()
        self.tokens = ZoomOAuthTokens(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data.get("refresh_token", self.tokens.refresh_token),
            expires_in=data["expires_in"],
            scope=data.get("scope", ""),
            expires_at=datetime.utcnow() + timedelta(seconds=data["expires_in"]),
        )

        return self.tokens

    async def ensure_valid_token(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.tokens:
            raise ZoomAuthenticationError("No tokens available")

        if self.tokens.is_expired():
            await self.refresh_access_token()

    def _get_basic_auth_header(self) -> str:
        """Get the Basic auth header for OAuth requests."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with Bearer token for API requests."""
        await self.ensure_valid_token()
        return {
            "Authorization": f"Bearer {self.tokens.access_token}",
            "Content-Type": "application/json",
        }

    # ==================== API Request Methods ====================

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers

        Returns:
            JSON response data
        """
        auth_headers = await self._get_auth_headers()
        if headers:
            auth_headers.update(headers)

        url = f"{self.api_base_url}{endpoint}"

        response = await self.http_client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=auth_headers,
        )

        if response.status_code == 401:
            # Try refreshing the token and retry once
            await self.refresh_access_token()
            auth_headers = await self._get_auth_headers()
            response = await self.http_client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=auth_headers,
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise ZoomRateLimitError(retry_after=retry_after)

        if response.status_code == 404:
            raise ZoomAPIError("Resource not found", status_code=404)

        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            raise ZoomAPIError(
                message=error_data.get("message", f"API error: {response.status_code}"),
                status_code=response.status_code,
                error_code=error_data.get("code"),
            )

        return response.json() if response.content else {}

    # ==================== User/Account Methods ====================

    async def get_current_user(self) -> ZoomAccount:
        """Get the current authenticated user's information.

        Returns:
            ZoomAccount with user details
        """
        data = await self._make_request("GET", "/users/me")

        return ZoomAccount(
            id=data["id"],
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            display_name=data.get("display_name"),
            account_id=data["account_id"],
            timezone=data.get("timezone"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            if data.get("created_at")
            else None,
            tokens=self.tokens,
        )

    # ==================== Recording Methods ====================

    async def list_recordings(
        self,
        user_id: str = "me",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
    ) -> ZoomRecordingListResponse:
        """List cloud recordings for a user.

        Args:
            user_id: User ID or 'me' for current user
            from_date: Start date (YYYY-MM-DD), defaults to 30 days ago
            to_date: End date (YYYY-MM-DD), defaults to today
            page_size: Number of results per page (1-300)
            next_page_token: Token for pagination

        Returns:
            ZoomRecordingListResponse with recordings list
        """
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "from": from_date,
            "to": to_date,
            "page_size": page_size,
        }
        if next_page_token:
            params["next_page_token"] = next_page_token

        data = await self._make_request(
            "GET", f"/users/{user_id}/recordings", params=params
        )

        meetings = []
        for meeting_data in data.get("meetings", []):
            recording_files = [
                ZoomRecordingFile(
                    id=rf["id"],
                    meeting_id=rf["meeting_id"],
                    recording_start=datetime.fromisoformat(
                        rf["recording_start"].replace("Z", "+00:00")
                    ),
                    recording_end=datetime.fromisoformat(
                        rf["recording_end"].replace("Z", "+00:00")
                    ),
                    file_type=rf["file_type"],
                    file_extension=rf.get("file_extension"),
                    file_size=rf.get("file_size"),
                    play_url=rf.get("play_url"),
                    download_url=rf.get("download_url"),
                    recording_type=rf.get("recording_type"),
                )
                for rf in meeting_data.get("recording_files", [])
            ]

            meetings.append(
                ZoomRecording(
                    uuid=meeting_data["uuid"],
                    id=meeting_data["id"],
                    account_id=meeting_data["account_id"],
                    host_id=meeting_data["host_id"],
                    host_email=meeting_data.get("host_email"),
                    topic=meeting_data["topic"],
                    type=meeting_data.get("type", 2),
                    start_time=datetime.fromisoformat(
                        meeting_data["start_time"].replace("Z", "+00:00")
                    ),
                    duration=meeting_data.get("duration", 0),
                    timezone=meeting_data.get("timezone"),
                    total_size=meeting_data.get("total_size"),
                    recording_count=meeting_data.get("recording_count", 0),
                    share_url=meeting_data.get("share_url"),
                    recording_files=recording_files,
                    password=meeting_data.get("password"),
                )
            )

        return ZoomRecordingListResponse(
            **{
                "from": from_date,
                "to": to_date,
            },
            page_size=data.get("page_size", page_size),
            next_page_token=data.get("next_page_token"),
            meetings=meetings,
        )

    async def get_recording(self, meeting_id: str) -> ZoomRecording:
        """Get a specific recording by meeting ID.

        Args:
            meeting_id: The meeting ID or UUID

        Returns:
            ZoomRecording with all recording files
        """
        try:
            data = await self._make_request("GET", f"/meetings/{meeting_id}/recordings")
        except ZoomAPIError as e:
            if e.status_code == 404:
                raise ZoomRecordingNotFoundError(meeting_id)
            raise

        recording_files = [
            ZoomRecordingFile(
                id=rf["id"],
                meeting_id=rf["meeting_id"],
                recording_start=datetime.fromisoformat(
                    rf["recording_start"].replace("Z", "+00:00")
                ),
                recording_end=datetime.fromisoformat(
                    rf["recording_end"].replace("Z", "+00:00")
                ),
                file_type=rf["file_type"],
                file_extension=rf.get("file_extension"),
                file_size=rf.get("file_size"),
                play_url=rf.get("play_url"),
                download_url=rf.get("download_url"),
                recording_type=rf.get("recording_type"),
            )
            for rf in data.get("recording_files", [])
        ]

        return ZoomRecording(
            uuid=data["uuid"],
            id=data["id"],
            account_id=data["account_id"],
            host_id=data["host_id"],
            host_email=data.get("host_email"),
            topic=data["topic"],
            type=data.get("type", 2),
            start_time=datetime.fromisoformat(
                data["start_time"].replace("Z", "+00:00")
            ),
            duration=data.get("duration", 0),
            timezone=data.get("timezone"),
            total_size=data.get("total_size"),
            recording_count=data.get("recording_count", 0),
            share_url=data.get("share_url"),
            recording_files=recording_files,
            password=data.get("password"),
        )

    # ==================== Transcript Methods ====================

    async def get_transcript_file(
        self, recording: ZoomRecording
    ) -> Optional[ZoomRecordingFile]:
        """Find the transcript file in a recording.

        Args:
            recording: The recording to search

        Returns:
            The transcript recording file if found
        """
        for rf in recording.recording_files:
            if rf.file_type in ("TRANSCRIPT", "VTT", "CC"):
                return rf
            if rf.recording_type == RecordingType.AUDIO_TRANSCRIPT:
                return rf
        return None

    async def download_transcript(
        self,
        meeting_id: str,
        download_token: Optional[str] = None,
    ) -> ZoomTranscript:
        """Download and parse a transcript for a recording.

        Args:
            meeting_id: The meeting ID
            download_token: Optional download token from webhook

        Returns:
            ZoomTranscript with content and parsed data
        """
        recording = await self.get_recording(meeting_id)
        transcript_file = await self.get_transcript_file(recording)

        if not transcript_file or not transcript_file.download_url:
            raise ZoomTranscriptNotFoundError(meeting_id)

        # Download the transcript content
        download_url = transcript_file.download_url
        if download_token:
            download_url = f"{download_url}?access_token={download_token}"
        else:
            await self.ensure_valid_token()
            download_url = f"{download_url}?access_token={self.tokens.access_token}"

        response = await self.http_client.get(download_url)

        if response.status_code != 200:
            raise ZoomAPIError(
                f"Failed to download transcript: {response.status_code}",
                status_code=response.status_code,
            )

        content = response.text

        # Parse the transcript
        parser = get_parser(transcript_file.file_type)
        parsed = parser.parse(content, meeting_id)
        parsed.meeting_topic = recording.topic

        return ZoomTranscript(
            recording_id=transcript_file.id,
            meeting_id=meeting_id,
            download_url=transcript_file.download_url,
            file_type=transcript_file.file_type,
            content=content,
            parsed=parsed,
        )

    async def download_transcript_from_url(
        self,
        download_url: str,
        meeting_id: str,
        file_type: str = "VTT",
        download_token: Optional[str] = None,
    ) -> ZoomTranscript:
        """Download transcript directly from a URL.

        Args:
            download_url: Direct download URL
            meeting_id: The meeting ID for reference
            file_type: The transcript file type (VTT, SRT)
            download_token: Optional download token

        Returns:
            ZoomTranscript with content and parsed data
        """
        url = download_url
        if download_token:
            url = f"{download_url}?access_token={download_token}"
        elif self.tokens:
            await self.ensure_valid_token()
            url = f"{download_url}?access_token={self.tokens.access_token}"

        response = await self.http_client.get(url)

        if response.status_code != 200:
            raise ZoomAPIError(
                f"Failed to download transcript: {response.status_code}",
                status_code=response.status_code,
            )

        content = response.text

        # Parse the transcript
        parser = get_parser(file_type)
        parsed = parser.parse(content, meeting_id)

        return ZoomTranscript(
            recording_id="",
            meeting_id=meeting_id,
            download_url=download_url,
            file_type=file_type,
            content=content,
            parsed=parsed,
        )

    # ==================== Meeting Metadata Methods ====================

    async def get_meeting(self, meeting_id: str) -> ZoomMeeting:
        """Get meeting details.

        Args:
            meeting_id: The meeting ID

        Returns:
            ZoomMeeting with meeting details
        """
        data = await self._make_request("GET", f"/meetings/{meeting_id}")

        return ZoomMeeting(
            uuid=data["uuid"],
            id=data["id"],
            host_id=data["host_id"],
            host_email=data.get("host_email"),
            topic=data["topic"],
            type=data["type"],
            status=data.get("status"),
            start_time=datetime.fromisoformat(
                data["start_time"].replace("Z", "+00:00")
            )
            if data.get("start_time")
            else None,
            duration=data.get("duration"),
            timezone=data.get("timezone"),
            agenda=data.get("agenda"),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            )
            if data.get("created_at")
            else None,
            join_url=data.get("join_url"),
            start_url=data.get("start_url"),
        )

    async def get_meeting_metadata(self, meeting_id: str) -> ZoomMeetingMetadata:
        """Extract comprehensive metadata from a meeting.

        Args:
            meeting_id: The meeting ID

        Returns:
            ZoomMeetingMetadata with extracted information
        """
        meeting = await self.get_meeting(meeting_id)

        # Try to get recording info
        has_recording = False
        has_transcript = False
        recording_url = None
        transcript_url = None

        try:
            recording = await self.get_recording(meeting_id)
            has_recording = len(recording.recording_files) > 0
            recording_url = recording.share_url

            transcript_file = await self.get_transcript_file(recording)
            if transcript_file:
                has_transcript = True
                transcript_url = transcript_file.download_url
        except ZoomRecordingNotFoundError:
            pass

        # Calculate end time from start time and duration
        end_time = None
        if meeting.start_time and meeting.duration:
            end_time = meeting.start_time + timedelta(minutes=meeting.duration)

        return ZoomMeetingMetadata(
            meeting_id=str(meeting.id),
            meeting_uuid=meeting.uuid,
            topic=meeting.topic,
            host_email=meeting.host_email,
            start_time=meeting.start_time or datetime.utcnow(),
            end_time=end_time,
            duration_minutes=meeting.duration or 0,
            participants=[],  # Would need to fetch participants separately
            has_recording=has_recording,
            has_transcript=has_transcript,
            recording_url=recording_url,
            transcript_url=transcript_url,
        )

    # ==================== Webhook Validation ====================

    @staticmethod
    def validate_webhook_signature(
        payload: bytes,
        signature: str,
        timestamp: str,
        secret: Optional[str] = None,
    ) -> bool:
        """Validate a Zoom webhook signature.

        Args:
            payload: Raw request body
            signature: Signature from x-zm-signature header
            timestamp: Timestamp from x-zm-request-timestamp header
            secret: Webhook secret token

        Returns:
            True if signature is valid
        """
        secret = secret or settings.zoom_webhook_secret

        message = f"v0:{timestamp}:{payload.decode('utf-8')}"
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        expected = f"v0={expected_signature}"
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def generate_webhook_response(plain_token: str, secret: Optional[str] = None) -> Dict[str, str]:
        """Generate response for Zoom webhook URL validation.

        Args:
            plain_token: The plainToken from validation request
            secret: Webhook secret token

        Returns:
            Dict with plainToken and encryptedToken
        """
        secret = secret or settings.zoom_webhook_secret

        encrypted_token = hmac.new(
            secret.encode("utf-8"),
            plain_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "plainToken": plain_token,
            "encryptedToken": encrypted_token,
        }
