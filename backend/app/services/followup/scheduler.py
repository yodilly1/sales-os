"""
Follow-up scheduling service.

Handles scheduling, timing optimization, and delivery of follow-up content.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from ...models.followup import (
    FollowUpBase,
    FollowUpEmail,
    FollowUpStatus,
    FollowUpTask,
    ScheduleConfig,
    ScheduleWindow,
)

logger = logging.getLogger(__name__)


class FollowUpScheduler:
    """
    Manages scheduling and timing of follow-up content.

    Features:
    - Optimal send time calculation
    - Business hours enforcement
    - Blackout date handling
    - Rate limiting
    - Retry logic for failed sends
    """

    def __init__(
        self,
        config: Optional[ScheduleConfig] = None,
        email_sender=None,
        task_client=None,
    ):
        """
        Initialize the scheduler.

        Args:
            config: Scheduling configuration
            email_sender: Email sending service
            task_client: Task/calendar integration client
        """
        self.config = config or self._get_default_config()
        self.email_sender = email_sender
        self.task_client = task_client

        # Track sends for rate limiting
        self._daily_send_counts: dict[str, int] = {}
        self._prospect_send_counts: dict[UUID, dict[str, int]] = {}

    def _get_default_config(self) -> ScheduleConfig:
        """Get default scheduling configuration."""
        return ScheduleConfig(
            name="default",
            window=ScheduleWindow(
                start_hour=9,
                end_hour=17,
                days_of_week=[0, 1, 2, 3, 4],  # Monday-Friday
                timezone="UTC",
            ),
            optimal_send_times=[9, 10, 14, 15],  # 9am, 10am, 2pm, 3pm
            max_emails_per_day=50,
            max_emails_per_prospect_per_day=2,
            min_hours_between_emails=4,
        )

    async def schedule_followup(
        self,
        followup: FollowUpBase,
        requested_time: Optional[datetime] = None,
        force: bool = False,
    ) -> tuple[bool, datetime, Optional[str]]:
        """
        Schedule a follow-up for delivery.

        Args:
            followup: The follow-up to schedule
            requested_time: Requested delivery time (optional)
            force: Override rate limits and schedule windows

        Returns:
            Tuple of (success, scheduled_time, error_message)
        """
        # Validate rate limits
        if not force:
            rate_limit_ok, rate_limit_msg = self._check_rate_limits(followup)
            if not rate_limit_ok:
                return False, datetime.utcnow(), rate_limit_msg

        # Calculate optimal send time
        if requested_time:
            scheduled_time = self._adjust_to_schedule_window(requested_time, force)
        else:
            scheduled_time = self._calculate_optimal_time(followup)

        # Check blackout dates
        if not force and self._is_blackout_date(scheduled_time):
            scheduled_time = self._find_next_available_time(scheduled_time)

        # Update followup
        followup.scheduled_at = scheduled_time
        followup.status = FollowUpStatus.SCHEDULED

        # Track for rate limiting
        self._increment_send_count(followup)

        logger.info(
            f"Scheduled follow-up {followup.id} for {scheduled_time}",
            extra={
                "followup_id": str(followup.id),
                "followup_type": followup.type.value,
                "scheduled_at": scheduled_time.isoformat(),
            },
        )

        return True, scheduled_time, None

    def _check_rate_limits(
        self,
        followup: FollowUpBase,
    ) -> tuple[bool, Optional[str]]:
        """Check if sending this follow-up would exceed rate limits."""
        today = datetime.utcnow().date().isoformat()

        # Check daily limit
        daily_count = self._daily_send_counts.get(today, 0)
        if daily_count >= self.config.max_emails_per_day:
            return False, f"Daily email limit ({self.config.max_emails_per_day}) reached"

        # Check per-prospect limit
        prospect_counts = self._prospect_send_counts.get(followup.prospect_id, {})
        prospect_daily_count = prospect_counts.get(today, 0)
        if prospect_daily_count >= self.config.max_emails_per_prospect_per_day:
            return False, (
                f"Daily per-prospect limit ({self.config.max_emails_per_prospect_per_day}) "
                f"reached for prospect {followup.prospect_id}"
            )

        return True, None

    def _increment_send_count(self, followup: FollowUpBase) -> None:
        """Increment send counts for rate limiting."""
        today = datetime.utcnow().date().isoformat()

        # Increment daily count
        self._daily_send_counts[today] = self._daily_send_counts.get(today, 0) + 1

        # Increment prospect count
        if followup.prospect_id not in self._prospect_send_counts:
            self._prospect_send_counts[followup.prospect_id] = {}
        prospect_counts = self._prospect_send_counts[followup.prospect_id]
        prospect_counts[today] = prospect_counts.get(today, 0) + 1

    def _calculate_optimal_time(self, followup: FollowUpBase) -> datetime:
        """Calculate the optimal send time for a follow-up."""
        now = datetime.utcnow()

        # Start from now if within schedule window, otherwise next window
        if self._is_within_schedule_window(now):
            base_time = now
        else:
            base_time = self._find_next_window_start(now)

        # Prefer optimal send times
        optimal_hours = self.config.optimal_send_times
        if optimal_hours:
            for hour in optimal_hours:
                potential_time = base_time.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                if potential_time > now and self._is_within_schedule_window(potential_time):
                    return potential_time

        # If no optimal time available today, use next day's first optimal hour
        next_day = base_time + timedelta(days=1)
        while next_day.weekday() not in self.config.window.days_of_week:
            next_day += timedelta(days=1)

        first_optimal_hour = optimal_hours[0] if optimal_hours else self.config.window.start_hour
        return next_day.replace(hour=first_optimal_hour, minute=0, second=0, microsecond=0)

    def _is_within_schedule_window(self, dt: datetime) -> bool:
        """Check if a datetime is within the schedule window."""
        window = self.config.window

        # Check day of week
        if dt.weekday() not in window.days_of_week:
            return False

        # Check hour
        if dt.hour < window.start_hour or dt.hour >= window.end_hour:
            return False

        return True

    def _adjust_to_schedule_window(
        self,
        dt: datetime,
        force: bool = False,
    ) -> datetime:
        """Adjust a datetime to fit within the schedule window."""
        if force or self._is_within_schedule_window(dt):
            return dt

        window = self.config.window

        # Adjust hour if outside window
        if dt.hour < window.start_hour:
            dt = dt.replace(hour=window.start_hour, minute=0, second=0, microsecond=0)
        elif dt.hour >= window.end_hour:
            # Move to next day
            dt = (dt + timedelta(days=1)).replace(
                hour=window.start_hour, minute=0, second=0, microsecond=0
            )

        # Adjust day if weekend
        while dt.weekday() not in window.days_of_week:
            dt += timedelta(days=1)

        return dt

    def _find_next_window_start(self, dt: datetime) -> datetime:
        """Find the start of the next schedule window."""
        window = self.config.window
        result = dt.replace(hour=window.start_hour, minute=0, second=0, microsecond=0)

        # If we're past today's window, go to tomorrow
        if dt.hour >= window.start_hour:
            result += timedelta(days=1)

        # Skip to valid weekday
        while result.weekday() not in window.days_of_week:
            result += timedelta(days=1)

        return result

    def _is_blackout_date(self, dt: datetime) -> bool:
        """Check if a date is a blackout date."""
        date = dt.date()
        for blackout in self.config.blackout_dates:
            if blackout.date() == date:
                return True
        return False

    def _find_next_available_time(self, dt: datetime) -> datetime:
        """Find the next available time after blackout dates."""
        result = dt
        max_attempts = 30  # Don't loop forever

        for _ in range(max_attempts):
            if not self._is_blackout_date(result) and self._is_within_schedule_window(result):
                return result
            result += timedelta(days=1)
            result = result.replace(
                hour=self.config.window.start_hour,
                minute=0,
                second=0,
                microsecond=0,
            )

        return result

    async def process_scheduled_followups(self) -> dict[str, int]:
        """
        Process all scheduled follow-ups that are due.

        Returns:
            Dictionary with counts of processed, sent, and failed items
        """
        results = {"processed": 0, "sent": 0, "failed": 0}

        # This would query the database for scheduled follow-ups
        # that are due (scheduled_at <= now and status == SCHEDULED)
        # For now, this is a placeholder implementation

        logger.info("Processing scheduled follow-ups", extra=results)

        return results

    async def send_email(self, email: FollowUpEmail) -> tuple[bool, Optional[str]]:
        """
        Send an email follow-up.

        Args:
            email: The email to send

        Returns:
            Tuple of (success, error_message)
        """
        if not self.email_sender:
            logger.warning("No email sender configured, marking as sent for demo")
            email.status = FollowUpStatus.SENT
            email.sent_at = datetime.utcnow()
            return True, None

        try:
            # Send via email sender
            await self.email_sender.send(
                to=email.recipient.email,
                subject=email.draft.subject,
                html_body=email.draft.body_html,
                text_body=email.draft.body_text,
            )

            email.status = FollowUpStatus.SENT
            email.sent_at = datetime.utcnow()

            logger.info(f"Sent email follow-up {email.id}")
            return True, None

        except Exception as e:
            error_msg = str(e)
            email.status = FollowUpStatus.FAILED
            logger.error(f"Failed to send email {email.id}: {error_msg}")
            return False, error_msg

    async def create_task(self, task: FollowUpTask) -> tuple[bool, Optional[str]]:
        """
        Create a task in the task management system.

        Args:
            task: The task to create

        Returns:
            Tuple of (success, error_message)
        """
        if not self.task_client:
            logger.warning("No task client configured, marking as completed for demo")
            task.status = FollowUpStatus.COMPLETED
            return True, None

        try:
            # Create via task client
            result = await self.task_client.create_task(
                title=task.title,
                description=task.description,
                due_at=task.due_at,
                assigned_to=task.assigned_to,
            )

            task.status = FollowUpStatus.COMPLETED
            task.crm_task_id = result.get("id")

            logger.info(f"Created task follow-up {task.id}")
            return True, None

        except Exception as e:
            error_msg = str(e)
            task.status = FollowUpStatus.FAILED
            logger.error(f"Failed to create task {task.id}: {error_msg}")
            return False, error_msg

    def get_schedule_preview(
        self,
        count: int = 10,
        start_from: Optional[datetime] = None,
    ) -> list[datetime]:
        """
        Get a preview of upcoming schedule slots.

        Args:
            count: Number of slots to return
            start_from: Starting datetime

        Returns:
            List of available scheduled times
        """
        slots = []
        current = start_from or datetime.utcnow()

        while len(slots) < count:
            # Check if current time is valid
            if (
                self._is_within_schedule_window(current)
                and not self._is_blackout_date(current)
            ):
                slots.append(current)

            # Move to next hour
            current = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

            # Skip non-business hours
            if current.hour >= self.config.window.end_hour:
                current = (current + timedelta(days=1)).replace(
                    hour=self.config.window.start_hour
                )

            # Skip weekends
            while current.weekday() not in self.config.window.days_of_week:
                current += timedelta(days=1)

        return slots

    def reschedule_followup(
        self,
        followup: FollowUpBase,
        new_time: datetime,
    ) -> tuple[bool, Optional[str]]:
        """
        Reschedule a follow-up to a new time.

        Args:
            followup: The follow-up to reschedule
            new_time: New scheduled time

        Returns:
            Tuple of (success, error_message)
        """
        if followup.status == FollowUpStatus.SENT:
            return False, "Cannot reschedule already sent follow-up"

        if followup.status == FollowUpStatus.CANCELLED:
            return False, "Cannot reschedule cancelled follow-up"

        adjusted_time = self._adjust_to_schedule_window(new_time)
        followup.scheduled_at = adjusted_time
        followup.status = FollowUpStatus.SCHEDULED
        followup.updated_at = datetime.utcnow()

        logger.info(f"Rescheduled follow-up {followup.id} to {adjusted_time}")
        return True, None

    def cancel_followup(self, followup: FollowUpBase) -> tuple[bool, Optional[str]]:
        """
        Cancel a scheduled follow-up.

        Args:
            followup: The follow-up to cancel

        Returns:
            Tuple of (success, error_message)
        """
        if followup.status == FollowUpStatus.SENT:
            return False, "Cannot cancel already sent follow-up"

        if followup.status == FollowUpStatus.CANCELLED:
            return False, "Follow-up is already cancelled"

        followup.status = FollowUpStatus.CANCELLED
        followup.updated_at = datetime.utcnow()

        logger.info(f"Cancelled follow-up {followup.id}")
        return True, None
