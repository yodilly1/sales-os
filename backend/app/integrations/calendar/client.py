"""
Calendar Client Implementation

Provides unified interface for Google Calendar and Microsoft Outlook/365 APIs.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import httpx

from .models import (
    CalendarConfig,
    GoogleCalendarConfig,
    OutlookCalendarConfig,
    NormalizedEvent,
    NormalizedAttendee,
    CalendarInfo,
)
from ..calendar import models as calendar_models

logger = logging.getLogger(__name__)


class CalendarClientError(Exception):
    """Base exception for calendar client errors."""
    pass


class AuthenticationError(CalendarClientError):
    """Authentication or token error."""
    pass


class RateLimitError(CalendarClientError):
    """Rate limit exceeded."""
    pass


class CalendarClient(ABC):
    """Abstract base class for calendar clients."""

    def __init__(
        self,
        config: CalendarConfig,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
    ):
        self.config = config
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers=self._get_headers(),
            )
        return self._http_client

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def close(self):
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def is_token_expired(self) -> bool:
        """Check if access token is expired or will expire soon."""
        buffer = timedelta(minutes=5)
        return datetime.utcnow() + buffer >= self.token_expires_at

    @abstractmethod
    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        pass

    @abstractmethod
    async def list_calendars(self) -> List[CalendarInfo]:
        """List all calendars available to the user."""
        pass

    @abstractmethod
    async def list_events(
        self,
        calendar_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 250,
    ) -> List[NormalizedEvent]:
        """List calendar events within a time range."""
        pass

    @abstractmethod
    async def get_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None,
    ) -> NormalizedEvent:
        """Get a single calendar event by ID."""
        pass

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        if response.status_code == 401:
            raise AuthenticationError("Access token expired or invalid")
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        if response.status_code >= 400:
            raise CalendarClientError(
                f"API error: {response.status_code} - {response.text}"
            )
        return response.json()


class GoogleCalendarClient(CalendarClient):
    """Google Calendar API client."""

    def __init__(
        self,
        config: GoogleCalendarConfig,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
    ):
        super().__init__(config, access_token, refresh_token, token_expires_at)
        self.config: GoogleCalendarConfig = config

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh Google access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_uri,
                data={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            if response.status_code != 200:
                raise AuthenticationError(
                    f"Failed to refresh token: {response.text}"
                )

            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )
            # Update HTTP client headers
            self._http_client = None

            return token_data

    async def list_calendars(self) -> List[CalendarInfo]:
        """List all Google calendars."""
        client = await self._get_client()
        response = await client.get(
            f"{self.config.api_base_url}/users/me/calendarList"
        )
        data = await self._handle_response(response)

        return [
            CalendarInfo.from_google(cal)
            for cal in data.get("items", [])
        ]

    async def list_events(
        self,
        calendar_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 250,
    ) -> List[NormalizedEvent]:
        """List Google Calendar events."""
        calendar_id = calendar_id or "primary"
        client = await self._get_client()

        params: Dict[str, Any] = {
            "maxResults": min(max_results, 2500),
            "singleEvents": True,
            "orderBy": "startTime",
        }

        if start_time:
            params["timeMin"] = start_time.isoformat() + "Z"
        if end_time:
            params["timeMax"] = end_time.isoformat() + "Z"

        events: List[NormalizedEvent] = []
        page_token = None

        while True:
            if page_token:
                params["pageToken"] = page_token

            response = await client.get(
                f"{self.config.api_base_url}/calendars/{calendar_id}/events",
                params=params,
            )
            data = await self._handle_response(response)

            for event_data in data.get("items", []):
                try:
                    events.append(NormalizedEvent.from_google(event_data))
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")

            page_token = data.get("nextPageToken")
            if not page_token or len(events) >= max_results:
                break

        return events[:max_results]

    async def get_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None,
    ) -> NormalizedEvent:
        """Get a single Google Calendar event."""
        calendar_id = calendar_id or "primary"
        client = await self._get_client()

        response = await client.get(
            f"{self.config.api_base_url}/calendars/{calendar_id}/events/{event_id}"
        )
        data = await self._handle_response(response)

        return NormalizedEvent.from_google(data)


class OutlookCalendarClient(CalendarClient):
    """Microsoft Outlook/365 Calendar API client (Microsoft Graph)."""

    def __init__(
        self,
        config: OutlookCalendarConfig,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
    ):
        super().__init__(config, access_token, refresh_token, token_expires_at)
        self.config: OutlookCalendarConfig = config

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh Microsoft access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_uri,
                data={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                    "scope": " ".join(self.config.scopes),
                },
            )
            if response.status_code != 200:
                raise AuthenticationError(
                    f"Failed to refresh token: {response.text}"
                )

            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )
            # Update HTTP client headers
            self._http_client = None

            return token_data

    async def list_calendars(self) -> List[CalendarInfo]:
        """List all Outlook calendars."""
        client = await self._get_client()
        response = await client.get(
            f"{self.config.api_base_url}/me/calendars"
        )
        data = await self._handle_response(response)

        return [
            CalendarInfo.from_outlook(cal)
            for cal in data.get("value", [])
        ]

    async def list_events(
        self,
        calendar_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 250,
    ) -> List[NormalizedEvent]:
        """List Outlook Calendar events."""
        client = await self._get_client()

        # Build the endpoint URL
        if calendar_id:
            base_url = f"{self.config.api_base_url}/me/calendars/{calendar_id}/events"
        else:
            base_url = f"{self.config.api_base_url}/me/events"

        params: Dict[str, Any] = {
            "$top": min(max_results, 1000),
            "$orderby": "start/dateTime",
            "$select": (
                "id,subject,bodyPreview,start,end,location,attendees,"
                "organizer,isAllDay,onlineMeeting,onlineMeetingProvider,"
                "webLink,createdDateTime,lastModifiedDateTime,responseStatus"
            ),
        }

        # Build filter for time range
        filters = []
        if start_time:
            filters.append(f"start/dateTime ge '{start_time.isoformat()}'")
        if end_time:
            filters.append(f"end/dateTime le '{end_time.isoformat()}'")
        if filters:
            params["$filter"] = " and ".join(filters)

        events: List[NormalizedEvent] = []
        next_link = None

        while True:
            if next_link:
                response = await client.get(next_link)
            else:
                response = await client.get(base_url, params=params)

            data = await self._handle_response(response)

            for event_data in data.get("value", []):
                try:
                    events.append(NormalizedEvent.from_outlook(event_data))
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")

            next_link = data.get("@odata.nextLink")
            if not next_link or len(events) >= max_results:
                break

        return events[:max_results]

    async def get_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None,
    ) -> NormalizedEvent:
        """Get a single Outlook Calendar event."""
        client = await self._get_client()

        if calendar_id:
            url = f"{self.config.api_base_url}/me/calendars/{calendar_id}/events/{event_id}"
        else:
            url = f"{self.config.api_base_url}/me/events/{event_id}"

        response = await client.get(url)
        data = await self._handle_response(response)

        return NormalizedEvent.from_outlook(data)


def get_calendar_client(
    provider: str,
    config: CalendarConfig,
    access_token: str,
    refresh_token: str,
    token_expires_at: datetime,
) -> CalendarClient:
    """Factory function to create the appropriate calendar client."""
    if provider == "google":
        if not isinstance(config, GoogleCalendarConfig):
            raise ValueError("GoogleCalendarConfig required for Google provider")
        return GoogleCalendarClient(config, access_token, refresh_token, token_expires_at)
    elif provider == "outlook":
        if not isinstance(config, OutlookCalendarConfig):
            raise ValueError("OutlookCalendarConfig required for Outlook provider")
        return OutlookCalendarClient(config, access_token, refresh_token, token_expires_at)
    else:
        raise ValueError(f"Unsupported calendar provider: {provider}")
