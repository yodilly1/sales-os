"""
Meeting Prep Service

Main service class that orchestrates meeting preparation workflow.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.meetingprep import (
    Meeting,
    MeetingAttendee,
    MeetingPrepBrief,
    PrepStatus,
    DeliveryMethod,
    MeetingCreateRequest,
    MeetingSyncRequest,
    PrepBriefGenerateRequest,
    MeetingPrepBriefSchema,
    MeetingSchema,
)
from app.services.meetingprep.brief_generator import BriefGenerator
from app.services.meetingprep.calendar_integration import CalendarIntegration
from app.services.meetingprep.delivery import DeliveryService

logger = logging.getLogger(__name__)


class MeetingPrepService:
    """
    Service for managing meeting preparation workflows.

    Responsibilities:
    - Sync meetings from calendar providers
    - Trigger prep brief generation
    - Coordinate with enrichment, transcript, and content services
    - Manage delivery of prep briefs
    """

    def __init__(
        self,
        db: AsyncSession,
        brief_generator: BriefGenerator,
        calendar_integration: CalendarIntegration,
        delivery_service: DeliveryService,
    ):
        self.db = db
        self.brief_generator = brief_generator
        self.calendar = calendar_integration
        self.delivery = delivery_service

    # =========================================================================
    # Meeting Management
    # =========================================================================

    async def create_meeting(
        self,
        user_id: UUID,
        request: MeetingCreateRequest,
    ) -> Meeting:
        """Create a new meeting manually."""
        meeting = Meeting(
            user_id=user_id,
            title=request.title,
            scheduled_at=request.scheduled_at,
            duration_minutes=str(request.duration_minutes),
            meeting_type=request.meeting_type,
            description=request.description,
            location=request.location,
            meeting_link=request.meeting_link,
            deal_id=request.deal_id,
            company_id=request.company_id,
            calendar_event_id=request.calendar_event_id,
            calendar_provider=request.calendar_provider,
        )
        self.db.add(meeting)
        await self.db.flush()

        # Add attendees
        for email in request.attendee_emails:
            attendee = MeetingAttendee(
                meeting_id=meeting.id,
                email=email,
            )
            self.db.add(attendee)

        await self.db.commit()
        await self.db.refresh(meeting)

        logger.info(f"Created meeting {meeting.id} for user {user_id}")
        return meeting

    async def get_meeting(
        self,
        meeting_id: UUID,
        user_id: UUID,
    ) -> Optional[Meeting]:
        """Get a meeting by ID."""
        result = await self.db.execute(
            select(Meeting)
            .options(selectinload(Meeting.attendees), selectinload(Meeting.prep_brief))
            .where(and_(Meeting.id == meeting_id, Meeting.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def list_meetings(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_past: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Meeting], int]:
        """List meetings for a user with optional filters."""
        query = (
            select(Meeting)
            .options(selectinload(Meeting.attendees), selectinload(Meeting.prep_brief))
            .where(Meeting.user_id == user_id)
        )

        # Date filters
        if start_date:
            query = query.where(Meeting.scheduled_at >= start_date)
        elif not include_past:
            query = query.where(Meeting.scheduled_at >= datetime.utcnow())

        if end_date:
            query = query.where(Meeting.scheduled_at <= end_date)

        # Order by scheduled time
        query = query.order_by(Meeting.scheduled_at.asc())

        # Get total count
        count_result = await self.db.execute(
            select(Meeting.id).where(Meeting.user_id == user_id)
        )
        total = len(count_result.all())

        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        meetings = result.scalars().all()

        return list(meetings), total

    async def get_upcoming_meetings(
        self,
        user_id: UUID,
        days_ahead: int = 7,
    ) -> list[Meeting]:
        """Get upcoming meetings within the specified days."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        meetings, _ = await self.list_meetings(
            user_id=user_id,
            start_date=now,
            end_date=end_date,
            per_page=100,
        )
        return meetings

    async def sync_from_calendar(
        self,
        user_id: UUID,
        request: MeetingSyncRequest,
    ) -> list[Meeting]:
        """Sync meetings from a calendar provider."""
        logger.info(
            f"Syncing meetings for user {user_id} from {request.calendar_provider}"
        )

        # Fetch events from calendar provider
        calendar_events = await self.calendar.fetch_events(
            user_id=user_id,
            provider=request.calendar_provider,
            days_ahead=request.sync_days_ahead,
            include_past_days=request.include_past_days,
        )

        synced_meetings = []

        for event in calendar_events:
            # Check if meeting already exists
            existing = await self._get_meeting_by_calendar_id(
                event["id"], request.calendar_provider
            )

            if existing:
                # Update existing meeting
                await self._update_meeting_from_calendar(existing, event)
                synced_meetings.append(existing)
            else:
                # Create new meeting
                meeting = await self._create_meeting_from_calendar(
                    user_id, event, request.calendar_provider
                )
                synced_meetings.append(meeting)

        await self.db.commit()
        logger.info(f"Synced {len(synced_meetings)} meetings for user {user_id}")

        return synced_meetings

    async def _get_meeting_by_calendar_id(
        self,
        calendar_event_id: str,
        provider: str,
    ) -> Optional[Meeting]:
        """Get meeting by calendar event ID."""
        result = await self.db.execute(
            select(Meeting).where(
                and_(
                    Meeting.calendar_event_id == calendar_event_id,
                    Meeting.calendar_provider == provider,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _create_meeting_from_calendar(
        self,
        user_id: UUID,
        event: dict,
        provider: str,
    ) -> Meeting:
        """Create a meeting from a calendar event."""
        meeting = Meeting(
            user_id=user_id,
            calendar_event_id=event["id"],
            calendar_provider=provider,
            title=event.get("title", "Untitled Meeting"),
            description=event.get("description"),
            scheduled_at=event["start"],
            duration_minutes=str(event.get("duration_minutes", 30)),
            location=event.get("location"),
            meeting_link=event.get("meeting_link"),
        )
        self.db.add(meeting)
        await self.db.flush()

        # Add attendees from event
        for attendee_data in event.get("attendees", []):
            attendee = MeetingAttendee(
                meeting_id=meeting.id,
                email=attendee_data["email"],
                name=attendee_data.get("name"),
                response_status=attendee_data.get("response_status"),
                is_organizer=attendee_data.get("is_organizer", False),
            )
            self.db.add(attendee)

        return meeting

    async def _update_meeting_from_calendar(
        self,
        meeting: Meeting,
        event: dict,
    ) -> None:
        """Update an existing meeting from calendar event."""
        meeting.title = event.get("title", meeting.title)
        meeting.description = event.get("description", meeting.description)
        meeting.scheduled_at = event.get("start", meeting.scheduled_at)
        meeting.duration_minutes = str(event.get("duration_minutes", meeting.duration_minutes))
        meeting.location = event.get("location", meeting.location)
        meeting.meeting_link = event.get("meeting_link", meeting.meeting_link)
        meeting.updated_at = datetime.utcnow()

    # =========================================================================
    # Prep Brief Management
    # =========================================================================

    async def generate_prep_brief(
        self,
        user_id: UUID,
        request: PrepBriefGenerateRequest,
    ) -> MeetingPrepBrief:
        """Generate a prep brief for a meeting."""
        meeting = await self.get_meeting(request.meeting_id, user_id)
        if not meeting:
            raise ValueError(f"Meeting {request.meeting_id} not found")

        # Check for existing brief
        if meeting.prep_brief and not request.force_regenerate:
            if meeting.prep_brief.status == PrepStatus.COMPLETED:
                logger.info(f"Brief already exists for meeting {meeting.id}")
                return meeting.prep_brief
            elif meeting.prep_brief.status == PrepStatus.GENERATING:
                logger.info(f"Brief is currently generating for meeting {meeting.id}")
                return meeting.prep_brief

        # Create or update brief record
        if meeting.prep_brief:
            brief = meeting.prep_brief
            brief.status = PrepStatus.GENERATING
            brief.generation_error = None
        else:
            brief = MeetingPrepBrief(
                meeting_id=meeting.id,
                user_id=user_id,
                status=PrepStatus.GENERATING,
            )
            self.db.add(brief)

        await self.db.commit()
        await self.db.refresh(brief)

        try:
            # Generate the brief content
            brief_content = await self.brief_generator.generate(
                meeting=meeting,
                user_id=user_id,
                include_sections=request.include_sections,
            )

            # Update brief with generated content
            brief.attendee_profiles = brief_content.get("attendee_profiles")
            brief.company_research = brief_content.get("company_research")
            brief.call_history = brief_content.get("call_history")
            brief.spiced_context = brief_content.get("spiced_context")
            brief.suggested_agenda = brief_content.get("suggested_agenda")
            brief.suggested_questions = brief_content.get("suggested_questions")
            brief.content_recommendations = brief_content.get("content_recommendations")
            brief.executive_summary = brief_content.get("executive_summary")
            brief.status = PrepStatus.COMPLETED
            brief.generated_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"Generated prep brief {brief.id} for meeting {meeting.id}")

            # Handle delivery
            if request.delivery_methods:
                await self._deliver_brief(brief, request.delivery_methods)

        except Exception as e:
            logger.error(f"Failed to generate brief for meeting {meeting.id}: {e}")
            brief.status = PrepStatus.FAILED
            brief.generation_error = str(e)
            await self.db.commit()
            raise

        return brief

    async def get_prep_brief(
        self,
        meeting_id: UUID,
        user_id: UUID,
    ) -> Optional[MeetingPrepBrief]:
        """Get a prep brief for a meeting."""
        meeting = await self.get_meeting(meeting_id, user_id)
        if not meeting:
            return None

        brief = meeting.prep_brief
        if brief and not brief.viewed:
            brief.viewed = True
            brief.viewed_at = datetime.utcnow()
            await self.db.commit()

        return brief

    async def regenerate_prep_brief(
        self,
        meeting_id: UUID,
        user_id: UUID,
        delivery_methods: Optional[list[DeliveryMethod]] = None,
    ) -> MeetingPrepBrief:
        """Force regenerate a prep brief."""
        request = PrepBriefGenerateRequest(
            meeting_id=meeting_id,
            force_regenerate=True,
            delivery_methods=delivery_methods or [DeliveryMethod.IN_APP],
        )
        return await self.generate_prep_brief(user_id, request)

    async def _deliver_brief(
        self,
        brief: MeetingPrepBrief,
        delivery_methods: list[DeliveryMethod],
    ) -> None:
        """Deliver a prep brief via specified methods."""
        for method in delivery_methods:
            if method == DeliveryMethod.EMAIL or method == DeliveryMethod.ALL:
                await self.delivery.send_email(brief)
                brief.email_sent = True
                brief.email_sent_at = datetime.utcnow()

            if method == DeliveryMethod.CALENDAR or method == DeliveryMethod.ALL:
                await self.delivery.attach_to_calendar(brief)
                brief.calendar_attached = True

        await self.db.commit()

    # =========================================================================
    # Automated Prep Generation
    # =========================================================================

    async def schedule_auto_prep(
        self,
        user_id: UUID,
        hours_before_meeting: int = 24,
    ) -> list[MeetingPrepBrief]:
        """
        Generate prep briefs for upcoming meetings that don't have one.
        Should be called by a background job.
        """
        # Get meetings in the upcoming window
        now = datetime.utcnow()
        window_end = now + timedelta(hours=hours_before_meeting + 12)

        meetings, _ = await self.list_meetings(
            user_id=user_id,
            start_date=now + timedelta(hours=hours_before_meeting - 12),
            end_date=window_end,
            per_page=50,
        )

        generated_briefs = []

        for meeting in meetings:
            # Skip if brief already exists and is complete
            if meeting.prep_brief and meeting.prep_brief.status == PrepStatus.COMPLETED:
                continue

            try:
                brief = await self.generate_prep_brief(
                    user_id=user_id,
                    request=PrepBriefGenerateRequest(
                        meeting_id=meeting.id,
                        delivery_methods=[DeliveryMethod.ALL],
                    ),
                )
                generated_briefs.append(brief)
            except Exception as e:
                logger.error(
                    f"Failed auto-prep for meeting {meeting.id}: {e}"
                )

        return generated_briefs

    async def bulk_generate_preps(
        self,
        user_id: UUID,
        meeting_ids: Optional[list[UUID]] = None,
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None,
        delivery_methods: Optional[list[DeliveryMethod]] = None,
    ) -> list[MeetingPrepBrief]:
        """Bulk generate prep briefs for multiple meetings."""
        if meeting_ids:
            meetings = []
            for mid in meeting_ids:
                meeting = await self.get_meeting(mid, user_id)
                if meeting:
                    meetings.append(meeting)
        else:
            meetings, _ = await self.list_meetings(
                user_id=user_id,
                start_date=date_range_start or datetime.utcnow(),
                end_date=date_range_end,
                per_page=100,
            )

        generated_briefs = []
        delivery = delivery_methods or [DeliveryMethod.IN_APP]

        for meeting in meetings:
            try:
                brief = await self.generate_prep_brief(
                    user_id=user_id,
                    request=PrepBriefGenerateRequest(
                        meeting_id=meeting.id,
                        delivery_methods=delivery,
                    ),
                )
                generated_briefs.append(brief)
            except Exception as e:
                logger.error(f"Failed to generate brief for {meeting.id}: {e}")

        return generated_briefs

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def to_meeting_schema(self, meeting: Meeting) -> MeetingSchema:
        """Convert Meeting ORM model to response schema."""
        return MeetingSchema(
            id=meeting.id,
            title=meeting.title,
            meeting_type=meeting.meeting_type,
            scheduled_at=meeting.scheduled_at,
            duration_minutes=meeting.duration_minutes,
            description=meeting.description,
            location=meeting.location,
            meeting_link=meeting.meeting_link,
            attendees=[],  # Populated separately if needed
            has_prep_brief=meeting.prep_brief is not None,
            prep_brief_status=meeting.prep_brief.status if meeting.prep_brief else None,
            deal_id=meeting.deal_id,
            company_id=meeting.company_id,
        )

    def to_brief_schema(self, brief: MeetingPrepBrief) -> MeetingPrepBriefSchema:
        """Convert MeetingPrepBrief ORM model to response schema."""
        return MeetingPrepBriefSchema(
            id=brief.id,
            meeting_id=brief.meeting_id,
            status=brief.status,
            generated_at=brief.generated_at,
            executive_summary=brief.executive_summary,
            attendee_profiles=brief.attendee_profiles,
            company_research=brief.company_research,
            call_history=brief.call_history,
            spiced_context=brief.spiced_context,
            suggested_agenda=brief.suggested_agenda,
            suggested_questions=brief.suggested_questions,
            content_recommendations=brief.content_recommendations,
            email_sent=brief.email_sent,
            calendar_attached=brief.calendar_attached,
        )
