"""
Calendar Integration Configuration Models

Provider-specific configuration and data transformation models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CalendarConfig(BaseModel):
    """Base configuration for calendar integrations."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]


class GoogleCalendarConfig(CalendarConfig):
    """Google Calendar specific configuration."""
    scopes: List[str] = Field(default=[
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events.readonly",
    ])
    auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    revoke_uri: str = "https://oauth2.googleapis.com/revoke"
    api_base_url: str = "https://www.googleapis.com/calendar/v3"


class OutlookCalendarConfig(CalendarConfig):
    """Microsoft Outlook/365 specific configuration."""
    tenant_id: str = "common"  # Use 'common' for multi-tenant apps
    scopes: List[str] = Field(default=[
        "https://graph.microsoft.com/Calendars.Read",
        "https://graph.microsoft.com/User.Read",
        "offline_access",
    ])

    @property
    def auth_uri(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"

    @property
    def token_uri(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

    @property
    def api_base_url(self) -> str:
        return "https://graph.microsoft.com/v1.0"


# Data transformation models for normalizing provider responses

class NormalizedAttendee(BaseModel):
    """Normalized attendee across providers."""
    email: str
    name: Optional[str] = None
    response_status: str = "needsAction"
    is_organizer: bool = False
    is_optional: bool = False

    @classmethod
    def from_google(cls, attendee: Dict[str, Any]) -> "NormalizedAttendee":
        """Create from Google Calendar attendee."""
        return cls(
            email=attendee.get("email", ""),
            name=attendee.get("displayName"),
            response_status=attendee.get("responseStatus", "needsAction"),
            is_organizer=attendee.get("organizer", False),
            is_optional=attendee.get("optional", False),
        )

    @classmethod
    def from_outlook(cls, attendee: Dict[str, Any]) -> "NormalizedAttendee":
        """Create from Outlook attendee."""
        email_address = attendee.get("emailAddress", {})
        status = attendee.get("status", {})
        return cls(
            email=email_address.get("address", ""),
            name=email_address.get("name"),
            response_status=cls._map_outlook_status(status.get("response", "none")),
            is_organizer=False,  # Outlook handles organizer separately
            is_optional=attendee.get("type") == "optional",
        )

    @staticmethod
    def _map_outlook_status(outlook_status: str) -> str:
        """Map Outlook response status to normalized status."""
        status_map = {
            "none": "needsAction",
            "organizer": "accepted",
            "tentativelyAccepted": "tentative",
            "accepted": "accepted",
            "declined": "declined",
            "notResponded": "needsAction",
        }
        return status_map.get(outlook_status, "needsAction")


class NormalizedEvent(BaseModel):
    """Normalized calendar event across providers."""
    id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    location: Optional[str] = None
    is_all_day: bool = False
    attendees: List[NormalizedAttendee] = Field(default_factory=list)
    meeting_url: Optional[str] = None
    meeting_provider: Optional[str] = None
    html_link: Optional[str] = None
    status: str = "confirmed"
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    recurrence: Optional[List[str]] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_google(cls, event: Dict[str, Any]) -> "NormalizedEvent":
        """Create from Google Calendar event."""
        start = event.get("start", {})
        end = event.get("end", {})

        # Handle all-day events vs timed events
        is_all_day = "date" in start
        if is_all_day:
            start_time = datetime.fromisoformat(start["date"])
            end_time = datetime.fromisoformat(end["date"])
            timezone = "UTC"
        else:
            start_time = datetime.fromisoformat(
                start.get("dateTime", "").replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                end.get("dateTime", "").replace("Z", "+00:00")
            )
            timezone = start.get("timeZone", "UTC")

        # Extract meeting link
        meeting_url = None
        meeting_provider = None
        conference_data = event.get("conferenceData", {})
        if conference_data:
            entry_points = conference_data.get("entryPoints", [])
            for entry in entry_points:
                if entry.get("entryPointType") == "video":
                    meeting_url = entry.get("uri")
                    meeting_provider = conference_data.get("conferenceSolution", {}).get(
                        "name", "Unknown"
                    )
                    break

        # Parse attendees
        attendees = [
            NormalizedAttendee.from_google(a)
            for a in event.get("attendees", [])
        ]

        return cls(
            id=event["id"],
            title=event.get("summary", "Untitled"),
            description=event.get("description"),
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            location=event.get("location"),
            is_all_day=is_all_day,
            attendees=attendees,
            meeting_url=meeting_url,
            meeting_provider=meeting_provider,
            html_link=event.get("htmlLink"),
            status=event.get("status", "confirmed"),
            created=datetime.fromisoformat(
                event["created"].replace("Z", "+00:00")
            ) if event.get("created") else None,
            updated=datetime.fromisoformat(
                event["updated"].replace("Z", "+00:00")
            ) if event.get("updated") else None,
            recurrence=event.get("recurrence"),
            raw_data=event,
        )

    @classmethod
    def from_outlook(cls, event: Dict[str, Any]) -> "NormalizedEvent":
        """Create from Outlook event."""
        start = event.get("start", {})
        end = event.get("end", {})

        is_all_day = event.get("isAllDay", False)
        start_time = datetime.fromisoformat(
            start.get("dateTime", "").replace("Z", "+00:00")
        )
        end_time = datetime.fromisoformat(
            end.get("dateTime", "").replace("Z", "+00:00")
        )
        timezone = start.get("timeZone", "UTC")

        # Extract meeting link
        meeting_url = None
        meeting_provider = None
        online_meeting = event.get("onlineMeeting")
        if online_meeting:
            meeting_url = online_meeting.get("joinUrl")
            meeting_provider = event.get("onlineMeetingProvider", "Unknown")

        # Parse attendees
        attendees = [
            NormalizedAttendee.from_outlook(a)
            for a in event.get("attendees", [])
        ]

        # Add organizer as attendee if present
        organizer = event.get("organizer", {}).get("emailAddress", {})
        if organizer.get("address"):
            attendees.insert(0, NormalizedAttendee(
                email=organizer.get("address", ""),
                name=organizer.get("name"),
                response_status="accepted",
                is_organizer=True,
            ))

        # Map Outlook status to normalized status
        status_map = {
            "notResponded": "tentative",
            "organizer": "confirmed",
            "tentativelyAccepted": "tentative",
            "accepted": "confirmed",
            "declined": "cancelled",
        }

        return cls(
            id=event["id"],
            title=event.get("subject", "Untitled"),
            description=event.get("bodyPreview"),
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            location=event.get("location", {}).get("displayName"),
            is_all_day=is_all_day,
            attendees=attendees,
            meeting_url=meeting_url,
            meeting_provider=meeting_provider,
            html_link=event.get("webLink"),
            status=status_map.get(
                event.get("responseStatus", {}).get("response", ""),
                "confirmed"
            ),
            created=datetime.fromisoformat(
                event["createdDateTime"].replace("Z", "+00:00")
            ) if event.get("createdDateTime") else None,
            updated=datetime.fromisoformat(
                event["lastModifiedDateTime"].replace("Z", "+00:00")
            ) if event.get("lastModifiedDateTime") else None,
            raw_data=event,
        )


class CalendarList(BaseModel):
    """List of calendars available in user's account."""
    calendars: List["CalendarInfo"]


class CalendarInfo(BaseModel):
    """Information about a single calendar."""
    id: str
    name: str
    is_primary: bool = False
    is_selected: bool = False
    color: Optional[str] = None
    access_role: Optional[str] = None

    @classmethod
    def from_google(cls, calendar: Dict[str, Any]) -> "CalendarInfo":
        """Create from Google Calendar list entry."""
        return cls(
            id=calendar["id"],
            name=calendar.get("summary", "Untitled"),
            is_primary=calendar.get("primary", False),
            is_selected=calendar.get("selected", False),
            color=calendar.get("backgroundColor"),
            access_role=calendar.get("accessRole"),
        )

    @classmethod
    def from_outlook(cls, calendar: Dict[str, Any]) -> "CalendarInfo":
        """Create from Outlook calendar entry."""
        return cls(
            id=calendar["id"],
            name=calendar.get("name", "Untitled"),
            is_primary=calendar.get("isDefaultCalendar", False),
            is_selected=True,  # Outlook doesn't have this concept
            color=calendar.get("hexColor"),
            access_role="owner" if calendar.get("canEdit") else "reader",
        )
