"""
Avoma API client for transcript ingestion.

Provides methods to interact with the Avoma API:
- list_recordings(): List available recordings with pagination
- get_transcript(): Retrieve transcript for a recording
- get_meeting_metadata(): Get full meeting metadata
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from app.models.avoma import (
    AvomaAttendee,
    AvomaMeetingMetadata,
    AvomaRecording,
    AvomaRecordingListRequest,
    AvomaRecordingListResponse,
    AvomaRecordingStatus,
    AvomaTranscript,
    AvomaUtterance,
)

from .auth import AvomaAuthError, AvomaAuthManager

logger = logging.getLogger(__name__)


class AvomaAPIError(Exception):
    """Exception raised for Avoma API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        super().__init__(self.message)


class AvomaClient:
    """
    Client for interacting with the Avoma API.

    Handles all API requests with automatic token refresh,
    rate limiting, and error handling.
    """

    BASE_URL = "https://api.avoma.com/v1"
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2

    def __init__(self, auth_manager: AvomaAuthManager):
        """
        Initialize the Avoma client.

        Args:
            auth_manager: AvomaAuthManager instance for authentication
        """
        self.auth_manager = auth_manager
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.DEFAULT_TIMEOUT,
                base_url=self.BASE_URL,
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client and auth manager."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        await self.auth_manager.close()

    async def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests including authentication."""
        access_token = await self.auth_manager.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        retry_count: int = 0,
    ) -> dict:
        """
        Make an API request with error handling and retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary

        Raises:
            AvomaAPIError: If request fails after retries
        """
        client = await self._get_http_client()
        headers = await self._get_headers()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers,
            )

            # Extract request ID for debugging
            request_id = response.headers.get("X-Request-Id")

            # Handle rate limiting
            if response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = retry_after * (self.RETRY_BACKOFF_FACTOR**retry_count)
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry {retry_count + 1}"
                    )
                    import asyncio
                    await asyncio.sleep(wait_time)
                    return await self._request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                raise AvomaAPIError(
                    "Rate limit exceeded after max retries",
                    status_code=429,
                    error_code="rate_limit_exceeded",
                    request_id=request_id,
                )

            # Handle auth errors - try token refresh
            if response.status_code == 401:
                if retry_count == 0:
                    logger.info("Token expired, attempting refresh")
                    try:
                        await self.auth_manager.refresh_access_token()
                        return await self._request(
                            method, endpoint, params, json_data, retry_count + 1
                        )
                    except AvomaAuthError:
                        pass
                raise AvomaAPIError(
                    "Authentication failed",
                    status_code=401,
                    error_code="unauthorized",
                    request_id=request_id,
                )

            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise AvomaAPIError(
                    error_data.get("message", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    error_code=error_data.get("error"),
                    request_id=request_id,
                )

            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.RequestError as e:
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_BACKOFF_FACTOR ** retry_count
                logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                import asyncio
                await asyncio.sleep(wait_time)
                return await self._request(
                    method, endpoint, params, json_data, retry_count + 1
                )
            raise AvomaAPIError(
                f"Network error: {str(e)}",
                error_code="network_error",
            )

    async def list_recordings(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[AvomaRecordingStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        cursor: Optional[str] = None,
    ) -> AvomaRecordingListResponse:
        """
        List available recordings with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of recordings per page (max 100)
            status: Filter by recording status
            start_date: Filter by start date (recordings after this date)
            end_date: Filter by end date (recordings before this date)
            cursor: Pagination cursor for next page

        Returns:
            AvomaRecordingListResponse with recordings and pagination info

        Raises:
            AvomaAPIError: If request fails
        """
        params: dict = {
            "page": page,
            "page_size": min(page_size, 100),
        }

        if status:
            params["status"] = status.value
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if cursor:
            params["cursor"] = cursor

        logger.info(f"Fetching recordings: page={page}, page_size={page_size}")
        data = await self._request("GET", "/recordings", params=params)

        # Parse recordings
        recordings = []
        for rec_data in data.get("recordings", []):
            recordings.append(
                AvomaRecording(
                    id=rec_data["id"],
                    title=rec_data.get("title"),
                    duration_seconds=rec_data.get("duration_seconds", 0),
                    status=AvomaRecordingStatus(rec_data.get("status", "pending")),
                    recording_url=rec_data.get("recording_url"),
                    created_at=datetime.fromisoformat(rec_data["created_at"].replace("Z", "+00:00")),
                    updated_at=(
                        datetime.fromisoformat(rec_data["updated_at"].replace("Z", "+00:00"))
                        if rec_data.get("updated_at")
                        else None
                    ),
                    has_transcript=rec_data.get("has_transcript", False),
                    attendee_count=rec_data.get("attendee_count", 0),
                )
            )

        return AvomaRecordingListResponse(
            recordings=recordings,
            total_count=data.get("total_count", len(recordings)),
            page=data.get("page", page),
            page_size=data.get("page_size", page_size),
            has_more=data.get("has_more", False),
            next_cursor=data.get("next_cursor"),
        )

    async def get_transcript(self, recording_id: str) -> AvomaTranscript:
        """
        Retrieve the transcript for a recording.

        Args:
            recording_id: The ID of the recording

        Returns:
            AvomaTranscript with full transcript data

        Raises:
            AvomaAPIError: If request fails or transcript not available
        """
        logger.info(f"Fetching transcript for recording: {recording_id}")
        data = await self._request("GET", f"/recordings/{recording_id}/transcript")

        # Parse utterances
        utterances = []
        for utt_data in data.get("utterances", []):
            utterances.append(
                AvomaUtterance(
                    id=utt_data["id"],
                    speaker_id=utt_data["speaker_id"],
                    speaker_name=utt_data.get("speaker_name"),
                    text=utt_data["text"],
                    start_time=utt_data["start_time"],
                    end_time=utt_data["end_time"],
                    confidence=utt_data.get("confidence"),
                )
            )

        return AvomaTranscript(
            id=data["id"],
            recording_id=recording_id,
            utterances=utterances,
            full_text=data.get("full_text"),
            language=data.get("language", "en"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
        )

    async def get_meeting_metadata(self, recording_id: str) -> AvomaMeetingMetadata:
        """
        Get full meeting metadata for a recording.

        Args:
            recording_id: The ID of the recording

        Returns:
            AvomaMeetingMetadata with full meeting details

        Raises:
            AvomaAPIError: If request fails
        """
        logger.info(f"Fetching meeting metadata for recording: {recording_id}")
        data = await self._request("GET", f"/recordings/{recording_id}/metadata")

        # Parse attendees
        attendees = []
        for att_data in data.get("attendees", []):
            attendees.append(
                AvomaAttendee(
                    id=att_data["id"],
                    name=att_data["name"],
                    email=att_data.get("email"),
                    role=att_data.get("role"),
                    is_internal=att_data.get("is_internal", False),
                    speaker_id=att_data.get("speaker_id"),
                )
            )

        # Parse host
        host_data = data.get("host")
        host = None
        if host_data:
            host = AvomaAttendee(
                id=host_data["id"],
                name=host_data["name"],
                email=host_data.get("email"),
                role="host",
                is_internal=host_data.get("is_internal", True),
                speaker_id=host_data.get("speaker_id"),
            )

        return AvomaMeetingMetadata(
            id=data["id"],
            recording_id=recording_id,
            title=data["title"],
            description=data.get("description"),
            meeting_type=data.get("meeting_type"),
            duration_seconds=data.get("duration_seconds", 0),
            scheduled_start=(
                datetime.fromisoformat(data["scheduled_start"].replace("Z", "+00:00"))
                if data.get("scheduled_start")
                else None
            ),
            actual_start=datetime.fromisoformat(data["actual_start"].replace("Z", "+00:00")),
            actual_end=datetime.fromisoformat(data["actual_end"].replace("Z", "+00:00")),
            attendees=attendees,
            host=host,
            calendar_event_id=data.get("calendar_event_id"),
            crm_opportunity_id=data.get("crm_opportunity_id"),
            crm_contact_ids=data.get("crm_contact_ids", []),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            action_items=data.get("action_items", []),
            topics_discussed=data.get("topics_discussed", []),
            sentiment_score=data.get("sentiment_score"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=(
                datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at")
                else None
            ),
        )

    async def get_recording(self, recording_id: str) -> AvomaRecording:
        """
        Get a single recording by ID.

        Args:
            recording_id: The ID of the recording

        Returns:
            AvomaRecording with recording details

        Raises:
            AvomaAPIError: If request fails or recording not found
        """
        logger.info(f"Fetching recording: {recording_id}")
        data = await self._request("GET", f"/recordings/{recording_id}")

        return AvomaRecording(
            id=data["id"],
            title=data.get("title"),
            duration_seconds=data.get("duration_seconds", 0),
            status=AvomaRecordingStatus(data.get("status", "pending")),
            recording_url=data.get("recording_url"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=(
                datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at")
                else None
            ),
            has_transcript=data.get("has_transcript", False),
            attendee_count=data.get("attendee_count", 0),
        )

    async def get_recordings_with_transcripts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_recordings: int = 100,
    ) -> list[tuple[AvomaRecording, Optional[AvomaTranscript]]]:
        """
        Fetch recordings and their transcripts in one operation.

        This is a convenience method that fetches recordings and their
        transcripts, handling pagination automatically.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            max_recordings: Maximum number of recordings to fetch

        Returns:
            List of tuples (AvomaRecording, AvomaTranscript or None)
        """
        results: list[tuple[AvomaRecording, Optional[AvomaTranscript]]] = []
        cursor = None
        fetched = 0

        while fetched < max_recordings:
            page_size = min(20, max_recordings - fetched)
            response = await self.list_recordings(
                page_size=page_size,
                status=AvomaRecordingStatus.COMPLETED,
                start_date=start_date,
                end_date=end_date,
                cursor=cursor,
            )

            for recording in response.recordings:
                if fetched >= max_recordings:
                    break

                transcript = None
                if recording.has_transcript:
                    try:
                        transcript = await self.get_transcript(recording.id)
                    except AvomaAPIError as e:
                        logger.warning(
                            f"Failed to fetch transcript for {recording.id}: {e.message}"
                        )

                results.append((recording, transcript))
                fetched += 1

            if not response.has_more:
                break
            cursor = response.next_cursor

        return results

    async def health_check(self) -> bool:
        """
        Check if the Avoma API is accessible and authentication works.

        Returns:
            True if API is accessible and authenticated
        """
        try:
            await self._request("GET", "/health")
            return True
        except AvomaAPIError:
            return False
