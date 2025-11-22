"""
Calendar Integration Module for Sales OS

Provides calendar integration services for Google Calendar and Microsoft Outlook/365.
Supports OAuth2 authentication, event syncing, and meeting-transcript linking.
"""

from .client import (
    CalendarClient,
    GoogleCalendarClient,
    OutlookCalendarClient,
    get_calendar_client,
)
from .handlers import (
    CalendarOAuthHandler,
    GoogleOAuthHandler,
    OutlookOAuthHandler,
    CalendarSyncHandler,
)
from .models import (
    CalendarConfig,
    GoogleCalendarConfig,
    OutlookCalendarConfig,
)

__all__ = [
    # Clients
    "CalendarClient",
    "GoogleCalendarClient",
    "OutlookCalendarClient",
    "get_calendar_client",
    # Handlers
    "CalendarOAuthHandler",
    "GoogleOAuthHandler",
    "OutlookOAuthHandler",
    "CalendarSyncHandler",
    # Config
    "CalendarConfig",
    "GoogleCalendarConfig",
    "OutlookCalendarConfig",
]
