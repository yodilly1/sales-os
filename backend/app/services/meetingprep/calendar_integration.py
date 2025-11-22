"""
Calendar Integration

Handles integration with calendar providers (Google Calendar, Microsoft Outlook)
for syncing meeting data and attaching prep briefs to calendar events.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID

logger = logging.getLogger(__name__)


class CalendarProvider(ABC):
    """Abstract base class for calendar providers."""

    @abstractmethod
    async def authenticate(self, user_id: UUID, credentials: dict) -> bool:
        """Authenticate with the calendar provider."""
        pass

    @abstractmethod
    async def fetch_events(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Fetch calendar events within date range."""
        pass

    @abstractmethod
    async def update_event(
        self,
        user_id: UUID,
        event_id: str,
        updates: dict,
    ) -> bool:
        """Update a calendar event."""
        pass

    @abstractmethod
    async def add_attachment(
        self,
        user_id: UUID,
        event_id: str,
        attachment: dict,
    ) -> bool:
        """Add an attachment to a calendar event."""
        pass


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar integration."""

    def __init__(self, oauth_client: Any):
        self.oauth = oauth_client
        self.api_base = "https://www.googleapis.com/calendar/v3"

    async def authenticate(self, user_id: UUID, credentials: dict) -> bool:
        """Authenticate with Google OAuth."""
        try:
            # Verify and refresh tokens if needed
            token_info = await self.oauth.get_valid_token(
                user_id=user_id,
                provider="google",
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            )
            return token_info is not None
        except Exception as e:
            logger.error(f"Google Calendar auth failed for user {user_id}: {e}")
            return False

    async def fetch_events(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Fetch events from Google Calendar."""
        try:
            token = await self.oauth.get_valid_token(user_id, "google")
            if not token:
                raise ValueError("No valid Google token")

            # Build API request
            params = {
                "timeMin": start_date.isoformat() + "Z",
                "timeMax": end_date.isoformat() + "Z",
                "singleEvents": True,
                "orderBy": "startTime",
            }

            # Make API call (using httpx or aiohttp)
            # This is a placeholder for the actual API call
            events_data = await self._api_request(
                token=token,
                endpoint="/calendars/primary/events",
                params=params,
            )

            return self._parse_google_events(events_data.get("items", []))

        except Exception as e:
            logger.error(f"Failed to fetch Google Calendar events: {e}")
            return []

    async def update_event(
        self,
        user_id: UUID,
        event_id: str,
        updates: dict,
    ) -> bool:
        """Update a Google Calendar event."""
        try:
            token = await self.oauth.get_valid_token(user_id, "google")
            if not token:
                return False

            await self._api_request(
                token=token,
                endpoint=f"/calendars/primary/events/{event_id}",
                method="PATCH",
                data=updates,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return False

    async def add_attachment(
        self,
        user_id: UUID,
        event_id: str,
        attachment: dict,
    ) -> bool:
        """Add attachment to Google Calendar event (via description update)."""
        try:
            # Google Calendar doesn't support direct attachments via API
            # We add a link to the prep brief in the event description
            token = await self.oauth.get_valid_token(user_id, "google")
            if not token:
                return False

            # Get current event
            event = await self._api_request(
                token=token,
                endpoint=f"/calendars/primary/events/{event_id}",
            )

            # Update description with prep brief link
            current_desc = event.get("description", "")
            prep_link = attachment.get("url", "")
            prep_section = f"\n\n---\nMeeting Prep Brief: {prep_link}"

            if "Meeting Prep Brief:" not in current_desc:
                updated_desc = current_desc + prep_section
                await self.update_event(
                    user_id=user_id,
                    event_id=event_id,
                    updates={"description": updated_desc},
                )

            return True

        except Exception as e:
            logger.error(f"Failed to add attachment to Google Calendar: {e}")
            return False

    def _parse_google_events(self, items: list[dict]) -> list[dict]:
        """Parse Google Calendar event format to internal format."""
        events = []

        for item in items:
            start = item.get("start", {})
            end = item.get("end", {})

            # Handle all-day events vs timed events
            start_dt = start.get("dateTime") or start.get("date")
            end_dt = end.get("dateTime") or end.get("date")

            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
            if isinstance(end_dt, str):
                end_dt = datetime.fromisoformat(end_dt.replace("Z", "+00:00"))

            duration = int((end_dt - start_dt).total_seconds() / 60) if start_dt and end_dt else 30

            # Extract attendees
            attendees = []
            for attendee in item.get("attendees", []):
                attendees.append({
                    "email": attendee.get("email"),
                    "name": attendee.get("displayName"),
                    "response_status": attendee.get("responseStatus"),
                    "is_organizer": attendee.get("organizer", False),
                })

            # Extract meeting link
            meeting_link = None
            if item.get("hangoutLink"):
                meeting_link = item["hangoutLink"]
            elif item.get("conferenceData", {}).get("entryPoints"):
                for entry in item["conferenceData"]["entryPoints"]:
                    if entry.get("entryPointType") == "video":
                        meeting_link = entry.get("uri")
                        break

            events.append({
                "id": item.get("id"),
                "title": item.get("summary", "Untitled"),
                "description": item.get("description"),
                "start": start_dt,
                "end": end_dt,
                "duration_minutes": duration,
                "location": item.get("location"),
                "meeting_link": meeting_link,
                "attendees": attendees,
                "status": item.get("status"),
            })

        return events

    async def _api_request(
        self,
        token: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """Make an API request to Google Calendar."""
        # Placeholder for actual HTTP client implementation
        # In production, use httpx or aiohttp
        import httpx

        url = f"{self.api_base}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()


class OutlookCalendarProvider(CalendarProvider):
    """Microsoft Outlook/Office 365 Calendar integration."""

    def __init__(self, oauth_client: Any):
        self.oauth = oauth_client
        self.api_base = "https://graph.microsoft.com/v1.0"

    async def authenticate(self, user_id: UUID, credentials: dict) -> bool:
        """Authenticate with Microsoft OAuth."""
        try:
            token_info = await self.oauth.get_valid_token(
                user_id=user_id,
                provider="microsoft",
                scopes=["Calendars.Read", "Calendars.ReadWrite"],
            )
            return token_info is not None
        except Exception as e:
            logger.error(f"Outlook Calendar auth failed for user {user_id}: {e}")
            return False

    async def fetch_events(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Fetch events from Outlook Calendar."""
        try:
            token = await self.oauth.get_valid_token(user_id, "microsoft")
            if not token:
                raise ValueError("No valid Microsoft token")

            params = {
                "$filter": f"start/dateTime ge '{start_date.isoformat()}' and end/dateTime le '{end_date.isoformat()}'",
                "$orderby": "start/dateTime",
                "$top": 100,
            }

            events_data = await self._api_request(
                token=token,
                endpoint="/me/calendar/events",
                params=params,
            )

            return self._parse_outlook_events(events_data.get("value", []))

        except Exception as e:
            logger.error(f"Failed to fetch Outlook Calendar events: {e}")
            return []

    async def update_event(
        self,
        user_id: UUID,
        event_id: str,
        updates: dict,
    ) -> bool:
        """Update an Outlook Calendar event."""
        try:
            token = await self.oauth.get_valid_token(user_id, "microsoft")
            if not token:
                return False

            await self._api_request(
                token=token,
                endpoint=f"/me/calendar/events/{event_id}",
                method="PATCH",
                data=updates,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update Outlook Calendar event: {e}")
            return False

    async def add_attachment(
        self,
        user_id: UUID,
        event_id: str,
        attachment: dict,
    ) -> bool:
        """Add attachment to Outlook Calendar event."""
        try:
            token = await self.oauth.get_valid_token(user_id, "microsoft")
            if not token:
                return False

            # Outlook supports actual file attachments
            attachment_data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment.get("name", "Meeting Prep Brief.html"),
                "contentType": attachment.get("content_type", "text/html"),
                "contentBytes": attachment.get("content_base64", ""),
            }

            await self._api_request(
                token=token,
                endpoint=f"/me/calendar/events/{event_id}/attachments",
                method="POST",
                data=attachment_data,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add attachment to Outlook Calendar: {e}")
            return False

    def _parse_outlook_events(self, items: list[dict]) -> list[dict]:
        """Parse Outlook event format to internal format."""
        events = []

        for item in items:
            start = item.get("start", {})
            end = item.get("end", {})

            start_dt = datetime.fromisoformat(start.get("dateTime", "").replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.get("dateTime", "").replace("Z", "+00:00"))
            duration = int((end_dt - start_dt).total_seconds() / 60)

            # Extract attendees
            attendees = []
            for attendee in item.get("attendees", []):
                email_addr = attendee.get("emailAddress", {})
                attendees.append({
                    "email": email_addr.get("address"),
                    "name": email_addr.get("name"),
                    "response_status": attendee.get("status", {}).get("response"),
                    "is_organizer": attendee.get("type") == "required" and item.get("organizer", {}).get("emailAddress", {}).get("address") == email_addr.get("address"),
                })

            # Extract meeting link
            meeting_link = item.get("onlineMeeting", {}).get("joinUrl")

            events.append({
                "id": item.get("id"),
                "title": item.get("subject", "Untitled"),
                "description": item.get("bodyPreview"),
                "start": start_dt,
                "end": end_dt,
                "duration_minutes": duration,
                "location": item.get("location", {}).get("displayName"),
                "meeting_link": meeting_link,
                "attendees": attendees,
                "status": "confirmed" if not item.get("isCancelled") else "cancelled",
            })

        return events

    async def _api_request(
        self,
        token: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """Make an API request to Microsoft Graph."""
        import httpx

        url = f"{self.api_base}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()


class CalendarIntegration:
    """
    Unified calendar integration manager.

    Provides a single interface for working with multiple calendar providers.
    """

    def __init__(self, oauth_client: Any):
        self.oauth = oauth_client
        self.providers: dict[str, CalendarProvider] = {
            "google": GoogleCalendarProvider(oauth_client),
            "outlook": OutlookCalendarProvider(oauth_client),
            "microsoft": OutlookCalendarProvider(oauth_client),  # Alias
        }

    def get_provider(self, provider_name: str) -> CalendarProvider:
        """Get a calendar provider by name."""
        provider = self.providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported calendar provider: {provider_name}")
        return provider

    async def fetch_events(
        self,
        user_id: UUID,
        provider: str,
        days_ahead: int = 7,
        include_past_days: int = 0,
    ) -> list[dict]:
        """Fetch events from the specified calendar provider."""
        calendar_provider = self.get_provider(provider)

        now = datetime.utcnow()
        start_date = now - timedelta(days=include_past_days)
        end_date = now + timedelta(days=days_ahead)

        events = await calendar_provider.fetch_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            f"Fetched {len(events)} events from {provider} for user {user_id}"
        )

        return events

    async def attach_prep_brief(
        self,
        user_id: UUID,
        provider: str,
        event_id: str,
        brief_url: str,
        brief_content: Optional[str] = None,
    ) -> bool:
        """Attach a prep brief to a calendar event."""
        calendar_provider = self.get_provider(provider)

        attachment = {
            "url": brief_url,
            "name": "Meeting Prep Brief.html",
            "content_type": "text/html",
        }

        if brief_content:
            import base64
            attachment["content_base64"] = base64.b64encode(
                brief_content.encode()
            ).decode()

        return await calendar_provider.add_attachment(
            user_id=user_id,
            event_id=event_id,
            attachment=attachment,
        )

    async def update_event_description(
        self,
        user_id: UUID,
        provider: str,
        event_id: str,
        prep_brief_link: str,
    ) -> bool:
        """Update event description with prep brief link."""
        calendar_provider = self.get_provider(provider)

        return await calendar_provider.add_attachment(
            user_id=user_id,
            event_id=event_id,
            attachment={"url": prep_brief_link},
        )
