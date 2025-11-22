"""
Email notification service for Sales OS.

This module provides email delivery functionality for notifications,
including instant emails and digest emails.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr

from ...models.notification import (
    NotificationResponse,
    NotificationType,
    EmailNotificationRequest,
    EmailDigestRequest,
)

logger = logging.getLogger(__name__)


class EmailConfig(BaseModel):
    """Configuration for email service."""

    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = "notifications@sales-os.com"
    from_name: str = "Sales OS"


class EmailTemplate(BaseModel):
    """Email template data."""

    subject: str
    html_body: str
    text_body: str


class EmailNotificationService:
    """
    Service for sending email notifications.

    Handles both instant notifications and digest emails, with support
    for templating and SMTP delivery.
    """

    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize the email notification service.

        Args:
            config: Email configuration. If None, uses defaults.
        """
        self.config = config or EmailConfig()
        self._templates: Dict[str, EmailTemplate] = self._load_templates()

    def _load_templates(self) -> Dict[str, EmailTemplate]:
        """Load email templates for different notification types."""
        return {
            "notification": EmailTemplate(
                subject="{title}",
                html_body="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                        .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 8px 8px; }}
                        .button {{ display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin: 0; font-size: 20px;">Sales OS</h1>
                        </div>
                        <div class="content">
                            <h2 style="margin-top: 0;">{title}</h2>
                            <p>{body}</p>
                            {action_button}
                        </div>
                        <div class="footer">
                            <p>You received this email because you have notifications enabled for this type of activity.</p>
                            <p><a href="{preferences_url}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_body="""
{title}

{body}

---
You received this email because you have notifications enabled for this type of activity.
To manage your notification preferences, visit: {preferences_url}
                """,
            ),
            "digest": EmailTemplate(
                subject="Your {digest_period} Sales OS Digest - {notification_count} Updates",
                html_body="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                        .notification-item {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid #4F46E5; }}
                        .notification-title {{ font-weight: 600; margin-bottom: 5px; }}
                        .notification-body {{ color: #6b7280; font-size: 14px; }}
                        .notification-time {{ color: #9ca3af; font-size: 12px; margin-top: 5px; }}
                        .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 8px 8px; }}
                        .section-header {{ font-size: 14px; font-weight: 600; color: #6b7280; margin: 20px 0 10px 0; text-transform: uppercase; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin: 0; font-size: 20px;">Sales OS {digest_period} Digest</h1>
                            <p style="margin: 5px 0 0 0; opacity: 0.8;">{period_start} - {period_end}</p>
                        </div>
                        <div class="content">
                            <p>Here's a summary of your recent activity:</p>
                            {notifications_html}
                        </div>
                        <div class="footer">
                            <p>You received this digest based on your notification preferences.</p>
                            <p><a href="{preferences_url}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_body="""
Sales OS {digest_period} Digest
{period_start} - {period_end}

Here's a summary of your recent activity:

{notifications_text}

---
You received this digest based on your notification preferences.
To manage your preferences, visit: {preferences_url}
                """,
            ),
        }

    async def send_instant_notification(
        self,
        notification: NotificationResponse,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> bool:
        """
        Send an instant email notification.

        Args:
            notification: The notification to send
            recipient_email: Override recipient email (default: fetch from user)
            recipient_name: Override recipient name (default: fetch from user)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # In production, fetch user email from database if not provided
            if not recipient_email:
                # TODO: Fetch from user service
                recipient_email = "user@example.com"
                recipient_name = "User"

            template = self._templates["notification"]

            # Build action button HTML
            action_url = self._get_notification_action_url(notification)
            action_button = ""
            if action_url:
                action_button = f'<a href="{action_url}" class="button">View Details</a>'

            # Format template
            html_body = template.html_body.format(
                title=notification.title,
                body=notification.body,
                action_button=action_button,
                preferences_url=self._get_preferences_url(),
            )

            text_body = template.text_body.format(
                title=notification.title,
                body=notification.body,
                preferences_url=self._get_preferences_url(),
            )

            subject = template.subject.format(title=notification.title)

            # Send email
            await self._send_email(
                to_email=recipient_email,
                to_name=recipient_name or "",
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            logger.info(f"Instant notification email sent to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send instant notification email: {e}")
            return False

    async def send_digest(
        self,
        notifications: List[NotificationResponse],
        recipient_email: str,
        recipient_name: str,
        digest_period: str,
        period_start: datetime,
        period_end: datetime,
    ) -> bool:
        """
        Send a digest email containing multiple notifications.

        Args:
            notifications: List of notifications to include
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            digest_period: Period type ("daily", "weekly", "monthly")
            period_start: Start of the digest period
            period_end: End of the digest period

        Returns:
            True if sent successfully, False otherwise
        """
        if not notifications:
            logger.info(f"No notifications for digest email to {recipient_email}")
            return True

        try:
            template = self._templates["digest"]

            # Group notifications by type
            grouped = self._group_notifications_by_type(notifications)

            # Build notifications HTML
            notifications_html = self._build_notifications_html(grouped)
            notifications_text = self._build_notifications_text(grouped)

            # Format template
            html_body = template.html_body.format(
                digest_period=digest_period.capitalize(),
                period_start=period_start.strftime("%B %d, %Y"),
                period_end=period_end.strftime("%B %d, %Y"),
                notifications_html=notifications_html,
                preferences_url=self._get_preferences_url(),
            )

            text_body = template.text_body.format(
                digest_period=digest_period.capitalize(),
                period_start=period_start.strftime("%B %d, %Y"),
                period_end=period_end.strftime("%B %d, %Y"),
                notifications_text=notifications_text,
                preferences_url=self._get_preferences_url(),
            )

            subject = template.subject.format(
                digest_period=digest_period.capitalize(),
                notification_count=len(notifications),
            )

            # Send email
            await self._send_email(
                to_email=recipient_email,
                to_name=recipient_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            logger.info(
                f"Digest email sent to {recipient_email} with {len(notifications)} notifications"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send digest email: {e}")
            return False

    def _group_notifications_by_type(
        self, notifications: List[NotificationResponse]
    ) -> Dict[NotificationType, List[NotificationResponse]]:
        """Group notifications by their type."""
        grouped: Dict[NotificationType, List[NotificationResponse]] = {}
        for notification in notifications:
            if notification.type not in grouped:
                grouped[notification.type] = []
            grouped[notification.type].append(notification)
        return grouped

    def _build_notifications_html(
        self, grouped: Dict[NotificationType, List[NotificationResponse]]
    ) -> str:
        """Build HTML for grouped notifications."""
        html_parts = []

        type_labels = {
            NotificationType.TRANSCRIPT_PROCESSED: "Transcripts Processed",
            NotificationType.CONTENT_GENERATED: "Content Generated",
            NotificationType.ENRICHMENT_COMPLETE: "Enrichments Complete",
            NotificationType.COACHING_FEEDBACK_READY: "Coaching Feedback",
            NotificationType.INTEGRATION_SYNC_STATUS: "Integration Updates",
            NotificationType.SYSTEM_ALERT: "System Alerts",
            NotificationType.TEAM_UPDATE: "Team Updates",
        }

        for ntype, notifications in grouped.items():
            label = type_labels.get(ntype, ntype.value.replace("_", " ").title())
            html_parts.append(f'<div class="section-header">{label} ({len(notifications)})</div>')

            for notification in notifications[:5]:  # Limit to 5 per type
                html_parts.append(f"""
                <div class="notification-item">
                    <div class="notification-title">{notification.title}</div>
                    <div class="notification-body">{notification.body}</div>
                    <div class="notification-time">{notification.created_at.strftime("%b %d, %H:%M")}</div>
                </div>
                """)

            if len(notifications) > 5:
                html_parts.append(
                    f'<p style="color: #6b7280; font-size: 14px;">...and {len(notifications) - 5} more</p>'
                )

        return "".join(html_parts)

    def _build_notifications_text(
        self, grouped: Dict[NotificationType, List[NotificationResponse]]
    ) -> str:
        """Build plain text for grouped notifications."""
        text_parts = []

        type_labels = {
            NotificationType.TRANSCRIPT_PROCESSED: "Transcripts Processed",
            NotificationType.CONTENT_GENERATED: "Content Generated",
            NotificationType.ENRICHMENT_COMPLETE: "Enrichments Complete",
            NotificationType.COACHING_FEEDBACK_READY: "Coaching Feedback",
            NotificationType.INTEGRATION_SYNC_STATUS: "Integration Updates",
            NotificationType.SYSTEM_ALERT: "System Alerts",
            NotificationType.TEAM_UPDATE: "Team Updates",
        }

        for ntype, notifications in grouped.items():
            label = type_labels.get(ntype, ntype.value.replace("_", " ").title())
            text_parts.append(f"\n## {label} ({len(notifications)})\n")

            for notification in notifications[:5]:
                text_parts.append(f"- {notification.title}")
                text_parts.append(f"  {notification.body}")
                text_parts.append(f"  ({notification.created_at.strftime('%b %d, %H:%M')})\n")

            if len(notifications) > 5:
                text_parts.append(f"  ...and {len(notifications) - 5} more\n")

        return "\n".join(text_parts)

    def _get_notification_action_url(self, notification: NotificationResponse) -> Optional[str]:
        """Get the action URL for a notification based on its type and entity."""
        base_url = "https://app.sales-os.com"

        if notification.entity_type and notification.entity_id:
            return f"{base_url}/{notification.entity_type}s/{notification.entity_id}"

        return None

    def _get_preferences_url(self) -> str:
        """Get the URL for notification preferences."""
        return "https://app.sales-os.com/settings/notifications"

    async def _send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> None:
        """
        Send an email using SMTP.

        In production, this should use a proper email service like
        SendGrid, SES, or similar.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content
        """
        # TODO: Implement actual SMTP sending or integrate with email service
        # For now, we'll log the email details

        logger.info(f"Email would be sent to: {to_name} <{to_email}>")
        logger.info(f"Subject: {subject}")
        logger.debug(f"HTML Body length: {len(html_body)}")
        logger.debug(f"Text Body length: {len(text_body)}")

        # In production, use aiosmtplib or httpx for async email sending:
        #
        # import aiosmtplib
        # from email.mime.multipart import MIMEMultipart
        # from email.mime.text import MIMEText
        #
        # msg = MIMEMultipart("alternative")
        # msg["Subject"] = subject
        # msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        # msg["To"] = f"{to_name} <{to_email}>"
        #
        # msg.attach(MIMEText(text_body, "plain"))
        # msg.attach(MIMEText(html_body, "html"))
        #
        # await aiosmtplib.send(
        #     msg,
        #     hostname=self.config.smtp_host,
        #     port=self.config.smtp_port,
        #     username=self.config.smtp_username,
        #     password=self.config.smtp_password,
        #     use_tls=self.config.smtp_use_tls,
        # )


class DigestScheduler:
    """
    Scheduler for sending digest emails.

    This class manages the scheduling and sending of digest emails
    based on user preferences.
    """

    def __init__(
        self,
        email_service: EmailNotificationService,
        db_session_factory,
    ):
        """
        Initialize the digest scheduler.

        Args:
            email_service: Email notification service instance
            db_session_factory: Factory for creating database sessions
        """
        self.email_service = email_service
        self.db_session_factory = db_session_factory

    async def process_pending_digests(self) -> int:
        """
        Process all pending digest emails.

        This should be called periodically (e.g., every minute) by a
        background task or cron job.

        Returns:
            Number of digest emails sent
        """
        # TODO: Implement digest processing
        # 1. Query notification_digest_queue for entries where
        #    scheduled_for <= now and sent = False
        # 2. Group by user_id and digest_frequency
        # 3. For each group, fetch the notifications and user info
        # 4. Send digest email
        # 5. Mark queue entries as sent

        logger.info("Processing pending digests...")
        return 0

    async def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Clean up old digest queue entries.

        Args:
            days: Delete entries older than this many days

        Returns:
            Number of entries deleted
        """
        # TODO: Implement cleanup
        logger.info(f"Cleaning up digest queue entries older than {days} days")
        return 0
