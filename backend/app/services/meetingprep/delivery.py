"""
Delivery Service

Handles delivery of meeting prep briefs via multiple channels:
- Email before meeting
- In-app prep view
- Calendar event attachment
"""

import base64
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.models.meetingprep import MeetingPrepBrief, Meeting

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Manages delivery of meeting prep briefs to users.

    Supports multiple delivery channels:
    - Email: Send HTML-formatted brief to user's email
    - In-app: Make available in the application
    - Calendar: Attach brief to calendar event
    """

    def __init__(
        self,
        email_client: Any,  # Email service client
        calendar_integration: Any,  # CalendarIntegration instance
        app_base_url: str = "https://app.sales-os.com",
    ):
        self.email = email_client
        self.calendar = calendar_integration
        self.app_base_url = app_base_url

    async def send_email(
        self,
        brief: MeetingPrepBrief,
        recipient_email: Optional[str] = None,
    ) -> bool:
        """
        Send prep brief via email.

        Args:
            brief: The prep brief to deliver
            recipient_email: Override recipient (defaults to user's email)

        Returns:
            True if email was sent successfully
        """
        try:
            meeting = brief.meeting
            html_content = self._render_email_html(brief, meeting)

            # Build email
            subject = f"Meeting Prep: {meeting.title}"
            prep_link = f"{self.app_base_url}/prep/{brief.id}"

            await self.email.send(
                to=recipient_email,  # Will be resolved from user_id if None
                subject=subject,
                html_body=html_content,
                metadata={
                    "type": "meeting_prep",
                    "brief_id": str(brief.id),
                    "meeting_id": str(meeting.id),
                    "prep_link": prep_link,
                },
            )

            logger.info(f"Sent prep brief email for meeting {meeting.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send prep brief email: {e}")
            return False

    async def attach_to_calendar(
        self,
        brief: MeetingPrepBrief,
    ) -> bool:
        """
        Attach prep brief to the calendar event.

        Args:
            brief: The prep brief to attach

        Returns:
            True if attachment was successful
        """
        try:
            meeting = brief.meeting

            if not meeting.calendar_event_id or not meeting.calendar_provider:
                logger.warning(
                    f"Cannot attach to calendar: meeting {meeting.id} has no calendar link"
                )
                return False

            prep_link = f"{self.app_base_url}/prep/{brief.id}"

            # Generate HTML content for attachment
            html_content = self._render_attachment_html(brief, meeting)

            success = await self.calendar.attach_prep_brief(
                user_id=meeting.user_id,
                provider=meeting.calendar_provider,
                event_id=meeting.calendar_event_id,
                brief_url=prep_link,
                brief_content=html_content,
            )

            if success:
                logger.info(
                    f"Attached prep brief to calendar event {meeting.calendar_event_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to attach prep brief to calendar: {e}")
            return False

    def get_in_app_url(self, brief: MeetingPrepBrief) -> str:
        """Get the in-app URL for viewing a prep brief."""
        return f"{self.app_base_url}/prep/{brief.id}"

    def _render_email_html(
        self,
        brief: MeetingPrepBrief,
        meeting: Meeting,
    ) -> str:
        """Render prep brief as HTML email content."""
        sections = []

        # Header
        sections.append(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="color: #1a1a2e; margin: 0 0 10px 0;">{meeting.title}</h1>
            <p style="color: #666; margin: 0;">
                {meeting.scheduled_at.strftime('%A, %B %d, %Y at %I:%M %p')} |
                {meeting.duration_minutes} minutes
            </p>
        </div>
        """)

        # Executive Summary
        if brief.executive_summary:
            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Executive Summary
                </h2>
                <p style="color: #333; line-height: 1.6;">{brief.executive_summary}</p>
            </div>
            """)

        # Attendee Profiles
        if brief.attendee_profiles:
            attendee_html = ""
            for profile in brief.attendee_profiles:
                name = profile.get("name", profile.get("email", "Unknown"))
                title = profile.get("title", "")
                background = profile.get("background", "")

                attendee_html += f"""
                <div style="background-color: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                    <h4 style="margin: 0 0 8px 0; color: #1a1a2e;">{name}</h4>
                    <p style="margin: 0 0 8px 0; color: #666; font-size: 14px;">{title}</p>
                    {f'<p style="margin: 0; color: #333; font-size: 14px;">{background}</p>' if background else ''}
                </div>
                """

            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Attendees
                </h2>
                {attendee_html}
            </div>
            """)

        # Company Research
        if brief.company_research:
            company = brief.company_research
            company_html = f"""
            <p><strong>Industry:</strong> {company.get('industry', 'N/A')}</p>
            <p><strong>Size:</strong> {company.get('size', 'N/A')}</p>
            """
            if company.get("description"):
                company_html += f"<p>{company['description']}</p>"

            if company.get("recent_news"):
                news_items = "".join(
                    f"<li>{news}</li>" for news in company["recent_news"][:3]
                )
                company_html += f"<p><strong>Recent News:</strong></p><ul>{news_items}</ul>"

            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Company: {company.get('name', 'Unknown')}
                </h2>
                {company_html}
            </div>
            """)

        # SPICED Context
        if brief.spiced_context:
            spiced = brief.spiced_context
            spiced_html = ""

            if spiced.get("situation"):
                spiced_html += f"<p><strong>Situation:</strong> {spiced['situation']}</p>"
            if spiced.get("pain"):
                pain_items = ", ".join(spiced["pain"])
                spiced_html += f"<p><strong>Pain Points:</strong> {pain_items}</p>"
            if spiced.get("impact"):
                spiced_html += f"<p><strong>Impact:</strong> {spiced['impact']}</p>"
            if spiced.get("critical_event"):
                spiced_html += f"<p><strong>Critical Event:</strong> {spiced['critical_event']}</p>"

            if spiced_html:
                sections.append(f"""
                <div style="margin-bottom: 24px; background-color: #f0f7ff; padding: 16px; border-radius: 8px;">
                    <h2 style="color: #1a1a2e; margin-top: 0;">SPICED Context</h2>
                    {spiced_html}
                </div>
                """)

        # Suggested Agenda
        if brief.suggested_agenda:
            agenda_items = ""
            for item in brief.suggested_agenda:
                agenda_items += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                        {item.get('duration_minutes', '?')} min
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                        <strong>{item.get('topic', 'Untitled')}</strong>
                        {f"<br><span style='color: #666; font-size: 13px;'>{item.get('description', '')}</span>" if item.get('description') else ''}
                    </td>
                </tr>
                """

            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Suggested Agenda
                </h2>
                <table style="width: 100%; border-collapse: collapse;">
                    {agenda_items}
                </table>
            </div>
            """)

        # Suggested Questions
        if brief.suggested_questions:
            questions_html = ""
            for q in brief.suggested_questions:
                questions_html += f"""
                <div style="margin-bottom: 12px; padding-left: 16px; border-left: 3px solid #4a90d9;">
                    <p style="margin: 0 0 4px 0; font-weight: 500;">{q.get('question', '')}</p>
                    <p style="margin: 0; color: #666; font-size: 13px;">
                        Category: {q.get('category', 'general')}
                    </p>
                </div>
                """

            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Questions to Ask
                </h2>
                {questions_html}
            </div>
            """)

        # Content Recommendations
        if brief.content_recommendations:
            content_html = ""
            for rec in brief.content_recommendations:
                content_html += f"""
                <div style="background-color: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                    <strong>{rec.get('title', 'Untitled')}</strong>
                    <span style="color: #666; font-size: 13px;"> - {rec.get('content_type', 'content')}</span>
                    <p style="margin: 8px 0 0 0; color: #666; font-size: 13px;">{rec.get('relevance', '')}</p>
                </div>
                """

            sections.append(f"""
            <div style="margin-bottom: 24px;">
                <h2 style="color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px;">
                    Content to Share
                </h2>
                {content_html}
            </div>
            """)

        # Call to action
        prep_link = f"{self.app_base_url}/prep/{brief.id}"
        sections.append(f"""
        <div style="text-align: center; margin-top: 32px; padding: 24px; background-color: #1a1a2e; border-radius: 8px;">
            <a href="{prep_link}" style="display: inline-block; background-color: #4a90d9; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 500;">
                View Full Prep Brief
            </a>
        </div>
        """)

        # Wrap in email template
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Meeting Prep: {meeting.title}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: white; padding: 32px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                {''.join(sections)}
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>Generated by Sales OS | <a href="{self.app_base_url}" style="color: #666;">Manage preferences</a></p>
            </div>
        </body>
        </html>
        """

    def _render_attachment_html(
        self,
        brief: MeetingPrepBrief,
        meeting: Meeting,
    ) -> str:
        """Render a compact version of the brief for calendar attachment."""
        sections = []

        sections.append(f"<h1>Meeting Prep: {meeting.title}</h1>")

        if brief.executive_summary:
            sections.append(f"<h2>Summary</h2><p>{brief.executive_summary}</p>")

        if brief.attendee_profiles:
            attendee_list = "<ul>"
            for p in brief.attendee_profiles:
                name = p.get("name", p.get("email", "Unknown"))
                title = p.get("title", "")
                attendee_list += f"<li><strong>{name}</strong> - {title}</li>"
            attendee_list += "</ul>"
            sections.append(f"<h2>Attendees</h2>{attendee_list}")

        if brief.suggested_agenda:
            agenda_list = "<ol>"
            for item in brief.suggested_agenda:
                agenda_list += f"<li>{item.get('topic')} ({item.get('duration_minutes')} min)</li>"
            agenda_list += "</ol>"
            sections.append(f"<h2>Agenda</h2>{agenda_list}")

        if brief.suggested_questions:
            questions_list = "<ul>"
            for q in brief.suggested_questions[:5]:
                questions_list += f"<li>{q.get('question')}</li>"
            questions_list += "</ul>"
            sections.append(f"<h2>Key Questions</h2>{questions_list}")

        prep_link = f"{self.app_base_url}/prep/{brief.id}"
        sections.append(f"<p><a href='{prep_link}'>View full prep brief</a></p>")

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Meeting Prep</title></head>
        <body style="font-family: Arial, sans-serif; padding: 16px;">
            {''.join(sections)}
        </body>
        </html>
        """


class ScheduledDeliveryManager:
    """
    Manages scheduled delivery of prep briefs.

    Handles timing logic to deliver briefs at the right time before meetings.
    """

    def __init__(
        self,
        delivery_service: DeliveryService,
        default_hours_before: int = 24,
    ):
        self.delivery = delivery_service
        self.default_hours_before = default_hours_before

    async def schedule_delivery(
        self,
        brief: MeetingPrepBrief,
        hours_before: Optional[int] = None,
    ) -> datetime:
        """
        Schedule delivery of a prep brief.

        Args:
            brief: The brief to schedule
            hours_before: Hours before meeting to deliver (defaults to 24)

        Returns:
            Scheduled delivery time
        """
        hours = hours_before or self.default_hours_before
        meeting_time = brief.meeting.scheduled_at
        delivery_time = meeting_time - timedelta(hours=hours)

        # If delivery time is in the past, deliver now
        if delivery_time <= datetime.utcnow():
            await self.deliver_now(brief)
            return datetime.utcnow()

        # Schedule for future delivery (implementation depends on task queue)
        # This would integrate with Celery, Redis Queue, etc.
        logger.info(
            f"Scheduled brief {brief.id} delivery for {delivery_time}"
        )

        return delivery_time

    async def deliver_now(self, brief: MeetingPrepBrief) -> bool:
        """Immediately deliver a prep brief via all configured methods."""
        email_success = await self.delivery.send_email(brief)
        calendar_success = await self.delivery.attach_to_calendar(brief)

        return email_success or calendar_success
