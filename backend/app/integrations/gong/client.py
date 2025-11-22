"""
Gong API Client

Handles authentication and API communication with Gong's REST API.
Gong uses Basic Auth with Access Key and Access Key Secret.
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx

from .models import (
    GongAuthConfig,
    GongCall,
    GongCallListResponse,
    GongTranscript,
    GongParticipant,
    GongCallInsights,
)

logger = logging.getLogger(__name__)


class GongClientError(Exception):
    """Base exception for Gong client errors."""
    pass


class GongAuthenticationError(GongClientError):
    """Raised when authentication fails."""
    pass


class GongRateLimitError(GongClientError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class GongClient:
    """
    Client for interacting with Gong API.

    Gong API uses Basic Auth with Access Key (username) and
    Access Key Secret (password).

    API Documentation: https://gong.app.gong.io/settings/api/documentation
    """

    BASE_URL = "https://api.gong.io/v2/"

    def __init__(
        self,
        access_key: str,
        access_key_secret: str,
        timeout: float = 30.0,
    ):
        """
        Initialize Gong client.

        Args:
            access_key: Gong API access key
            access_key_secret: Gong API access key secret
            timeout: Request timeout in seconds
        """
        self.access_key = access_key
        self.access_key_secret = access_key_secret
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self.access_key}:{self.access_key_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make an API request to Gong.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data

        Returns:
            Response JSON data

        Raises:
            GongAuthenticationError: If authentication fails
            GongRateLimitError: If rate limit is exceeded
            GongClientError: For other API errors
        """
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
            )

            if response.status_code == 401:
                raise GongAuthenticationError(
                    "Authentication failed. Check your access key and secret."
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise GongRateLimitError(
                    "Rate limit exceeded.",
                    retry_after=int(retry_after) if retry_after else None,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Gong API error: {e.response.status_code} - {e.response.text}")
            raise GongClientError(f"API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Gong request error: {e}")
            raise GongClientError(f"Request failed: {e}") from e

    async def verify_credentials(self) -> bool:
        """
        Verify that the credentials are valid.

        Returns:
            True if credentials are valid

        Raises:
            GongAuthenticationError: If credentials are invalid
        """
        try:
            # Use a lightweight endpoint to verify credentials
            await self._request("GET", "users")
            return True
        except GongAuthenticationError:
            raise
        except GongClientError:
            # Other errors don't necessarily mean invalid credentials
            return True

    async def get_calls(
        self,
        from_datetime: Optional[datetime] = None,
        to_datetime: Optional[datetime] = None,
        cursor: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> GongCallListResponse:
        """
        Get list of calls from Gong.

        Args:
            from_datetime: Filter calls from this datetime
            to_datetime: Filter calls until this datetime
            cursor: Pagination cursor for next page
            workspace_id: Filter by workspace ID

        Returns:
            GongCallListResponse with calls and pagination info
        """
        body: dict = {}

        if from_datetime:
            body["filter"] = body.get("filter", {})
            body["filter"]["fromDateTime"] = from_datetime.isoformat() + "Z"

        if to_datetime:
            body["filter"] = body.get("filter", {})
            body["filter"]["toDateTime"] = to_datetime.isoformat() + "Z"

        if workspace_id:
            body["filter"] = body.get("filter", {})
            body["filter"]["workspaceId"] = workspace_id

        if cursor:
            body["cursor"] = cursor

        data = await self._request("POST", "calls", json_data=body)

        calls = [
            GongCall(
                id=call["id"],
                title=call.get("title"),
                scheduled=datetime.fromisoformat(call["scheduled"].rstrip("Z")) if call.get("scheduled") else None,
                started=datetime.fromisoformat(call["started"].rstrip("Z")) if call.get("started") else None,
                duration=call.get("duration"),
                direction=call.get("direction"),
                system=call.get("system"),
                scope=call.get("scope"),
                media=call.get("media"),
                language=call.get("language"),
                workspace_id=call.get("workspaceId"),
                sdr_disposition=call.get("sdrDisposition"),
                client_unique_id=call.get("clientUniqueId"),
                custom_data=call.get("customData"),
                url=call.get("url"),
            )
            for call in data.get("calls", [])
        ]

        return GongCallListResponse(
            calls=calls,
            cursor=data.get("records", {}).get("cursor"),
            total_records=data.get("records", {}).get("totalRecords"),
        )

    async def get_call_transcript(self, call_id: str) -> GongTranscript:
        """
        Get transcript for a specific call.

        Args:
            call_id: Gong call ID

        Returns:
            GongTranscript with full transcript data
        """
        body = {"filter": {"callIds": [call_id]}}
        data = await self._request("POST", "calls/transcript", json_data=body)

        transcripts = data.get("callTranscripts", [])
        if not transcripts:
            return GongTranscript(call_id=call_id, segments=[])

        transcript_data = transcripts[0]
        segments = []

        for segment in transcript_data.get("transcript", []):
            segments.append({
                "speaker_id": segment.get("speakerId"),
                "speaker_name": segment.get("speakerName"),
                "start_time": segment.get("start"),
                "end_time": segment.get("end"),
                "text": segment.get("text", ""),
            })

        return GongTranscript(
            call_id=call_id,
            segments=segments,
        )

    async def get_call_participants(self, call_id: str) -> list[GongParticipant]:
        """
        Get participants for a specific call.

        Args:
            call_id: Gong call ID

        Returns:
            List of GongParticipant objects
        """
        body = {"filter": {"callIds": [call_id]}}
        data = await self._request("POST", "calls/extensive", json_data=body)

        calls = data.get("calls", [])
        if not calls:
            return []

        call_data = calls[0]
        parties = call_data.get("parties", [])

        participants = []
        for party in parties:
            participants.append(
                GongParticipant(
                    id=party.get("id"),
                    email=party.get("emailAddress"),
                    name=party.get("name"),
                    title=party.get("title"),
                    phone=party.get("phoneNumber"),
                    speaker_id=party.get("speakerId"),
                    user_id=party.get("userId"),
                    affiliation=party.get("affiliation"),  # "internal" or "external"
                    context=party.get("context", []),
                )
            )

        return participants

    async def get_call_insights(self, call_id: str) -> Optional[GongCallInsights]:
        """
        Get Gong's AI-generated insights for a call (optional feature).

        Args:
            call_id: Gong call ID

        Returns:
            GongCallInsights if available, None otherwise
        """
        try:
            body = {"filter": {"callIds": [call_id]}}
            data = await self._request("POST", "calls/extensive", json_data=body)

            calls = data.get("calls", [])
            if not calls:
                return None

            call_data = calls[0]

            return GongCallInsights(
                call_id=call_id,
                topics=call_data.get("content", {}).get("topics", []),
                trackers=call_data.get("content", {}).get("trackers", []),
                action_items=call_data.get("interaction", {}).get("actionItems", []),
                questions_asked=call_data.get("interaction", {}).get("questionsAsked"),
                talk_ratio=call_data.get("collaboration", {}).get("talkRatio"),
                interactivity=call_data.get("collaboration", {}).get("interactivity"),
                patience=call_data.get("collaboration", {}).get("patience"),
            )
        except GongClientError:
            logger.warning(f"Could not fetch insights for call {call_id}")
            return None

    async def get_call_with_details(self, call_id: str) -> dict:
        """
        Get full call details including transcript and participants.

        Args:
            call_id: Gong call ID

        Returns:
            Dictionary with call, transcript, participants, and insights
        """
        # Fetch all details in parallel for efficiency
        import asyncio

        # First get basic call info
        calls_response = await self.get_calls()
        call = next((c for c in calls_response.calls if c.id == call_id), None)

        # Then fetch details
        transcript, participants, insights = await asyncio.gather(
            self.get_call_transcript(call_id),
            self.get_call_participants(call_id),
            self.get_call_insights(call_id),
        )

        return {
            "call": call,
            "transcript": transcript,
            "participants": participants,
            "insights": insights,
        }
