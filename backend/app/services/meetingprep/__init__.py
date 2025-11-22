"""
Meeting Prep Service

Auto-generates preparation briefs for sales meetings including:
- Attendee profiles from enrichment
- Company research summary
- Previous call history and SPICED context
- Suggested agenda and questions
- Relevant content recommendations

Delivery methods:
- Email brief before meeting
- In-app prep view
- Calendar event attachment
"""

from app.services.meetingprep.service import MeetingPrepService
from app.services.meetingprep.brief_generator import BriefGenerator
from app.services.meetingprep.calendar_integration import CalendarIntegration
from app.services.meetingprep.delivery import DeliveryService

__all__ = [
    "MeetingPrepService",
    "BriefGenerator",
    "CalendarIntegration",
    "DeliveryService",
]
