"""
Calendar OAuth and Sync Handlers

Handles OAuth2 flows for Google Calendar and Microsoft Outlook/365,
and synchronization of calendar events.
"""

import logging
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import httpx

from .models import (
    GoogleCalendarConfig,
    OutlookCalendarConfig,
    NormalizedEvent,
)
from .client import (
    CalendarClient,
    GoogleCalendarClient,
    OutlookCalendarClient,
    get_calendar_client,
    CalendarClientError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """OAuth flow error."""
    pass


class CalendarOAuthHandler(ABC):
    """Abstract base class for calendar OAuth handlers."""

    @abstractmethod
    def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
    ) -> str:
        """Generate the OAuth authorization URL."""
        pass

    @abstractmethod
    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke an access or refresh token."""
        pass

    @staticmethod
    def generate_state() -> str:
        """Generate a secure random state parameter for CSRF protection."""
        return secrets.token_urlsafe(32)


class GoogleOAuthHandler(CalendarOAuthHandler):
    """Google Calendar OAuth2 handler."""

    def __init__(self, config: GoogleCalendarConfig):
        self.config = config

    def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
    ) -> str:
        """Generate Google OAuth authorization URL."""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.auth_uri}?{query_string}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchange Google authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_uri,
                data={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Token exchange failed: {response.text}")

            token_data = response.json()

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "scope": token_data.get("scope"),
                "expires_at": datetime.utcnow() + timedelta(
                    seconds=token_data.get("expires_in", 3600)
                ),
            }

    async def revoke_token(self, token: str) -> bool:
        """Revoke a Google token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.revoke_uri,
                params={"token": token},
            )
            return response.status_code == 200


class OutlookOAuthHandler(CalendarOAuthHandler):
    """Microsoft Outlook/365 OAuth2 handler."""

    def __init__(self, config: OutlookCalendarConfig):
        self.config = config

    def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
    ) -> str:
        """Generate Microsoft OAuth authorization URL."""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "response_mode": "query",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.auth_uri}?{query_string}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchange Microsoft authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_uri,
                data={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(self.config.scopes),
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Token exchange failed: {response.text}")

            token_data = response.json()

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "scope": token_data.get("scope"),
                "expires_at": datetime.utcnow() + timedelta(
                    seconds=token_data.get("expires_in", 3600)
                ),
            }

    async def revoke_token(self, token: str) -> bool:
        """
        Microsoft doesn't have a simple token revocation endpoint.
        Users must revoke access through their Microsoft account settings.
        """
        logger.info("Microsoft tokens cannot be directly revoked via API")
        return True


class CalendarSyncHandler:
    """Handles calendar event synchronization."""

    def __init__(
        self,
        client: CalendarClient,
        org_id: UUID,
        integration_id: UUID,
    ):
        self.client = client
        self.org_id = org_id
        self.integration_id = integration_id

    async def sync_events(
        self,
        calendar_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        full_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronize calendar events.

        Args:
            calendar_id: Specific calendar to sync (default: primary)
            start_time: Start of sync range (default: 7 days ago)
            end_time: End of sync range (default: 30 days from now)
            full_sync: If True, fetch all events; if False, only updates

        Returns:
            Sync result with event counts and any errors
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.utcnow() + timedelta(days=30)

        result = {
            "integration_id": str(self.integration_id),
            "events_synced": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "errors": [],
            "synced_at": datetime.utcnow().isoformat(),
        }

        try:
            # Check and refresh token if needed
            if self.client.is_token_expired():
                await self.client.refresh_access_token()

            # Fetch events from calendar
            events = await self.client.list_events(
                calendar_id=calendar_id,
                start_time=start_time,
                end_time=end_time,
            )

            result["events_synced"] = len(events)

            # TODO: Implement actual database sync logic
            # This would involve:
            # 1. Fetching existing events from database
            # 2. Comparing with fetched events
            # 3. Creating new events
            # 4. Updating changed events
            # 5. Marking deleted events
            # For now, we just count all as "created" for demonstration

            result["events_created"] = len(events)

            logger.info(
                f"Synced {len(events)} events for integration {self.integration_id}"
            )

        except AuthenticationError as e:
            result["errors"].append(f"Authentication error: {str(e)}")
            logger.error(f"Auth error during sync: {e}")
        except CalendarClientError as e:
            result["errors"].append(f"Calendar API error: {str(e)}")
            logger.error(f"Calendar API error during sync: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            logger.exception(f"Unexpected error during sync: {e}")

        return result

    async def get_upcoming_events(
        self,
        calendar_id: Optional[str] = None,
        days: int = 7,
        limit: int = 10,
    ) -> List[NormalizedEvent]:
        """Get upcoming events for the next N days."""
        now = datetime.utcnow()
        end_time = now + timedelta(days=days)

        # Refresh token if needed
        if self.client.is_token_expired():
            await self.client.refresh_access_token()

        events = await self.client.list_events(
            calendar_id=calendar_id,
            start_time=now,
            end_time=end_time,
            max_results=limit,
        )

        return events

    async def get_event_details(
        self,
        event_id: str,
        calendar_id: Optional[str] = None,
    ) -> NormalizedEvent:
        """Get detailed information about a specific event."""
        if self.client.is_token_expired():
            await self.client.refresh_access_token()

        return await self.client.get_event(event_id, calendar_id)


class MeetingTranscriptLinker:
    """Handles linking meetings to transcripts."""

    def __init__(self, org_id: UUID):
        self.org_id = org_id

    async def find_matching_transcript(
        self,
        event: NormalizedEvent,
        transcripts: List[Dict[str, Any]],
    ) -> Tuple[Optional[UUID], float]:
        """
        Find a transcript that matches the given calendar event.

        Uses multiple heuristics:
        1. Time proximity (event time vs transcript recording time)
        2. Attendee matching (event attendees vs transcript participants)
        3. Title matching (event title vs transcript title/topic)

        Returns:
            Tuple of (transcript_id, confidence_score)
        """
        best_match: Optional[UUID] = None
        best_score: float = 0.0

        for transcript in transcripts:
            score = self._calculate_match_score(event, transcript)
            if score > best_score:
                best_score = score
                best_match = transcript.get("id")

        # Only return matches above threshold
        if best_score >= 0.5:
            return best_match, best_score
        return None, 0.0

    def _calculate_match_score(
        self,
        event: NormalizedEvent,
        transcript: Dict[str, Any],
    ) -> float:
        """Calculate matching score between event and transcript."""
        score = 0.0
        weights = {
            "time": 0.5,
            "attendees": 0.3,
            "title": 0.2,
        }

        # Time proximity score
        transcript_time = transcript.get("recorded_at")
        if transcript_time:
            if isinstance(transcript_time, str):
                transcript_time = datetime.fromisoformat(transcript_time)

            time_diff = abs((event.start_time - transcript_time).total_seconds())

            # Within 15 minutes = perfect match
            # Within 1 hour = good match
            # Within 2 hours = partial match
            if time_diff <= 900:  # 15 minutes
                score += weights["time"]
            elif time_diff <= 3600:  # 1 hour
                score += weights["time"] * 0.7
            elif time_diff <= 7200:  # 2 hours
                score += weights["time"] * 0.3

        # Attendee matching score
        transcript_participants = set(
            p.get("email", "").lower()
            for p in transcript.get("participants", [])
        )
        event_attendees = set(
            a.email.lower() for a in event.attendees
        )

        if transcript_participants and event_attendees:
            overlap = transcript_participants & event_attendees
            if overlap:
                match_ratio = len(overlap) / max(
                    len(transcript_participants), len(event_attendees)
                )
                score += weights["attendees"] * match_ratio

        # Title matching score
        event_title = event.title.lower()
        transcript_title = transcript.get("title", "").lower()

        if event_title and transcript_title:
            # Simple word overlap matching
            event_words = set(event_title.split())
            transcript_words = set(transcript_title.split())

            if event_words & transcript_words:
                word_overlap = len(event_words & transcript_words) / max(
                    len(event_words), len(transcript_words)
                )
                score += weights["title"] * word_overlap

        return score

    async def link_meeting_to_transcript(
        self,
        event_id: UUID,
        transcript_id: UUID,
        confidence_score: float = 1.0,
        link_type: str = "manual",
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Create a link between a meeting and a transcript.

        Args:
            event_id: Calendar event ID
            transcript_id: Transcript ID
            confidence_score: How confident the match is (0.0-1.0)
            link_type: "automatic" or "manual"
            created_by: User ID who created the link (for manual links)

        Returns:
            Created link record
        """
        link = {
            "event_id": str(event_id),
            "transcript_id": str(transcript_id),
            "org_id": str(self.org_id),
            "confidence_score": confidence_score,
            "link_type": link_type,
            "created_by": str(created_by) if created_by else None,
            "created_at": datetime.utcnow().isoformat(),
        }

        # TODO: Persist to database
        logger.info(
            f"Created meeting-transcript link: event={event_id}, "
            f"transcript={transcript_id}, confidence={confidence_score}"
        )

        return link

    async def unlink_meeting_from_transcript(
        self,
        event_id: UUID,
        transcript_id: UUID,
    ) -> bool:
        """Remove a meeting-transcript link."""
        # TODO: Implement database deletion
        logger.info(
            f"Removed meeting-transcript link: event={event_id}, "
            f"transcript={transcript_id}"
        )
        return True
