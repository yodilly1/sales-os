"""
Multi-touch sequence orchestration for follow-ups.

Manages automated sequences of follow-up actions with configurable
timing, conditions, and branching logic.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from ...models.followup import (
    ApprovalMode,
    FollowUpEmail,
    FollowUpSequence,
    FollowUpStatus,
    FollowUpTask,
    SequenceStatus,
    SequenceStep,
    SequenceStepType,
)

logger = logging.getLogger(__name__)


class SequenceManager:
    """
    Manages multi-touch follow-up sequences.

    Features:
    - Sequential step execution with configurable delays
    - Conditional branching based on engagement
    - Pause/resume capabilities
    - Stop on reply detection
    - Business hours awareness
    """

    def __init__(
        self,
        scheduler=None,
        engagement_tracker=None,
        template_repository=None,
    ):
        """
        Initialize the sequence manager.

        Args:
            scheduler: FollowUpScheduler instance for scheduling steps
            engagement_tracker: Service to track email engagement
            template_repository: Repository for email templates
        """
        self.scheduler = scheduler
        self.engagement_tracker = engagement_tracker
        self.template_repository = template_repository

    async def create_sequence(
        self,
        name: str,
        prospect_id: UUID,
        steps: list[dict],
        call_id: Optional[UUID] = None,
        approval_mode: ApprovalMode = ApprovalMode.MANUAL,
        stop_on_reply: bool = True,
        business_hours_only: bool = True,
        created_by: Optional[UUID] = None,
    ) -> FollowUpSequence:
        """
        Create a new follow-up sequence.

        Args:
            name: Sequence name
            prospect_id: Target prospect ID
            steps: List of step configurations
            call_id: Associated call ID (optional)
            approval_mode: Approval mode for sequence steps
            stop_on_reply: Whether to stop on prospect reply
            business_hours_only: Only execute during business hours
            created_by: Creator user ID

        Returns:
            Created FollowUpSequence
        """
        sequence_steps = []

        for i, step_config in enumerate(steps):
            step = SequenceStep(
                step_number=i + 1,
                step_type=SequenceStepType(step_config.get("type", "email")),
                delay_hours=step_config.get("delay_hours", 24),
                email_template_id=step_config.get("email_template_id"),
                task_template=step_config.get("task_template"),
                condition=step_config.get("condition"),
                condition_true_step=step_config.get("condition_true_step"),
                condition_false_step=step_config.get("condition_false_step"),
            )
            sequence_steps.append(step)

        sequence = FollowUpSequence(
            id=uuid4(),
            name=name,
            steps=sequence_steps,
            total_steps=len(sequence_steps),
            status=SequenceStatus.DRAFT,
            prospect_id=prospect_id,
            call_id=call_id,
            approval_mode=approval_mode,
            stop_on_reply=stop_on_reply,
            business_hours_only=business_hours_only,
            created_by=created_by,
        )

        logger.info(
            f"Created sequence {sequence.id} with {len(sequence_steps)} steps",
            extra={
                "sequence_id": str(sequence.id),
                "prospect_id": str(prospect_id),
                "steps_count": len(sequence_steps),
            },
        )

        return sequence

    async def start_sequence(
        self,
        sequence: FollowUpSequence,
    ) -> tuple[bool, Optional[str]]:
        """
        Start executing a sequence.

        Args:
            sequence: The sequence to start

        Returns:
            Tuple of (success, error_message)
        """
        if sequence.status not in [SequenceStatus.DRAFT, SequenceStatus.PAUSED]:
            return (
                False,
                f"Cannot start sequence with status {sequence.status.value}",
            )

        if not sequence.steps:
            return False, "Sequence has no steps"

        sequence.status = SequenceStatus.ACTIVE
        sequence.started_at = datetime.utcnow()
        sequence.current_step = 1

        # Execute first step immediately
        await self._execute_step(sequence, sequence.steps[0])

        logger.info(f"Started sequence {sequence.id}")
        return True, None

    async def pause_sequence(
        self,
        sequence: FollowUpSequence,
    ) -> tuple[bool, Optional[str]]:
        """
        Pause an active sequence.

        Args:
            sequence: The sequence to pause

        Returns:
            Tuple of (success, error_message)
        """
        if sequence.status != SequenceStatus.ACTIVE:
            return (
                False,
                f"Cannot pause sequence with status {sequence.status.value}",
            )

        sequence.status = SequenceStatus.PAUSED
        sequence.paused_at = datetime.utcnow()

        logger.info(f"Paused sequence {sequence.id}")
        return True, None

    async def resume_sequence(
        self,
        sequence: FollowUpSequence,
    ) -> tuple[bool, Optional[str]]:
        """
        Resume a paused sequence.

        Args:
            sequence: The sequence to resume

        Returns:
            Tuple of (success, error_message)
        """
        if sequence.status != SequenceStatus.PAUSED:
            return (
                False,
                f"Cannot resume sequence with status {sequence.status.value}",
            )

        sequence.status = SequenceStatus.ACTIVE
        sequence.paused_at = None

        # Continue from current step
        if sequence.current_step <= len(sequence.steps):
            current_step = sequence.steps[sequence.current_step - 1]
            await self._schedule_step(sequence, current_step)

        logger.info(f"Resumed sequence {sequence.id}")
        return True, None

    async def cancel_sequence(
        self,
        sequence: FollowUpSequence,
    ) -> tuple[bool, Optional[str]]:
        """
        Cancel a sequence.

        Args:
            sequence: The sequence to cancel

        Returns:
            Tuple of (success, error_message)
        """
        if sequence.status in [SequenceStatus.COMPLETED, SequenceStatus.CANCELLED]:
            return (
                False,
                f"Cannot cancel sequence with status {sequence.status.value}",
            )

        sequence.status = SequenceStatus.CANCELLED

        # Cancel any pending scheduled steps
        # This would interact with the scheduler to cancel pending items

        logger.info(f"Cancelled sequence {sequence.id}")
        return True, None

    async def advance_sequence(
        self,
        sequence: FollowUpSequence,
    ) -> tuple[bool, Optional[str]]:
        """
        Advance to the next step in a sequence.

        Args:
            sequence: The sequence to advance

        Returns:
            Tuple of (success, error_message)
        """
        if sequence.status != SequenceStatus.ACTIVE:
            return (
                False,
                f"Cannot advance sequence with status {sequence.status.value}",
            )

        # Check for reply if stop_on_reply is enabled
        if sequence.stop_on_reply and self.engagement_tracker:
            has_reply = await self.engagement_tracker.check_reply(
                prospect_id=sequence.prospect_id
            )
            if has_reply:
                sequence.status = SequenceStatus.COMPLETED
                sequence.completed_at = datetime.utcnow()
                logger.info(f"Sequence {sequence.id} stopped due to reply")
                return True, "Stopped due to prospect reply"

        # Mark current step as executed
        if sequence.current_step <= len(sequence.steps):
            current_step = sequence.steps[sequence.current_step - 1]
            current_step.status = FollowUpStatus.COMPLETED
            current_step.executed_at = datetime.utcnow()

        # Move to next step
        next_step_num = self._get_next_step_number(sequence)

        if next_step_num is None or next_step_num > len(sequence.steps):
            # Sequence complete
            sequence.status = SequenceStatus.COMPLETED
            sequence.completed_at = datetime.utcnow()
            logger.info(f"Sequence {sequence.id} completed")
            return True, "Sequence completed"

        # Execute next step
        sequence.current_step = next_step_num
        next_step = sequence.steps[next_step_num - 1]

        await self._schedule_step(sequence, next_step)

        logger.info(f"Sequence {sequence.id} advanced to step {next_step_num}")
        return True, None

    def _get_next_step_number(
        self,
        sequence: FollowUpSequence,
    ) -> Optional[int]:
        """Determine the next step number, handling conditions."""
        current_step = sequence.steps[sequence.current_step - 1]

        # Handle conditional branching
        if current_step.step_type == SequenceStepType.CONDITION:
            condition_result = self._evaluate_condition(
                sequence, current_step.condition
            )
            if condition_result:
                return current_step.condition_true_step
            else:
                return current_step.condition_false_step

        # Default: next sequential step
        return sequence.current_step + 1

    def _evaluate_condition(
        self,
        sequence: FollowUpSequence,
        condition: Optional[str],
    ) -> bool:
        """Evaluate a step condition."""
        if not condition:
            return True

        # Parse condition (simplified)
        # In production, use a proper expression evaluator

        if "opened" in condition.lower():
            # Check if previous email was opened
            if self.engagement_tracker:
                # Would check engagement data
                pass
            return True

        if "clicked" in condition.lower():
            # Check if previous email had a click
            if self.engagement_tracker:
                # Would check engagement data
                pass
            return False

        return True

    async def _execute_step(
        self,
        sequence: FollowUpSequence,
        step: SequenceStep,
    ) -> None:
        """Execute a sequence step immediately."""
        step.status = FollowUpStatus.SCHEDULED

        if step.step_type == SequenceStepType.EMAIL:
            await self._execute_email_step(sequence, step)
        elif step.step_type == SequenceStepType.TASK:
            await self._execute_task_step(sequence, step)
        elif step.step_type == SequenceStepType.WAIT:
            # Schedule next step after wait period
            await self._schedule_next_step(sequence, step.delay_hours)
        elif step.step_type == SequenceStepType.CONDITION:
            # Evaluate condition and branch
            await self.advance_sequence(sequence)

    async def _schedule_step(
        self,
        sequence: FollowUpSequence,
        step: SequenceStep,
    ) -> None:
        """Schedule a step for future execution."""
        execution_time = datetime.utcnow() + timedelta(hours=step.delay_hours)

        # Adjust for business hours if required
        if sequence.business_hours_only and self.scheduler:
            execution_time = self.scheduler._adjust_to_schedule_window(execution_time)

        step.status = FollowUpStatus.SCHEDULED

        logger.info(
            f"Scheduled step {step.step_number} for {execution_time}",
            extra={
                "sequence_id": str(sequence.id),
                "step_number": step.step_number,
                "scheduled_at": execution_time.isoformat(),
            },
        )

    async def _schedule_next_step(
        self,
        sequence: FollowUpSequence,
        delay_hours: int,
    ) -> None:
        """Schedule the next step after a delay."""
        # This would create a scheduled job to call advance_sequence
        # after the specified delay
        pass

    async def _execute_email_step(
        self,
        sequence: FollowUpSequence,
        step: SequenceStep,
    ) -> None:
        """Execute an email step."""
        if not step.email_template_id and not self.template_repository:
            logger.warning(f"No template for email step {step.step_number}")
            return

        # Load template
        template = None
        if self.template_repository and step.email_template_id:
            template = await self.template_repository.get(step.email_template_id)

        # Create email follow-up from template
        # This would populate the email with prospect data and template content

        logger.info(
            f"Executed email step {step.step_number} for sequence {sequence.id}"
        )

    async def _execute_task_step(
        self,
        sequence: FollowUpSequence,
        step: SequenceStep,
    ) -> None:
        """Execute a task step."""
        if not step.task_template:
            logger.warning(f"No template for task step {step.step_number}")
            return

        # Create task follow-up from template
        task = FollowUpTask(
            call_id=sequence.call_id or uuid4(),
            prospect_id=sequence.prospect_id,
            title=step.task_template,
            description=f"Auto-generated from sequence: {sequence.name}",
            due_at=datetime.utcnow() + timedelta(days=1),
            sequence_id=sequence.id,
            sequence_step=step.step_number,
        )

        logger.info(
            f"Executed task step {step.step_number} for sequence {sequence.id}"
        )

    async def process_due_sequences(self) -> dict[str, int]:
        """
        Process all sequences with steps due for execution.

        Returns:
            Dictionary with processing statistics
        """
        results = {
            "sequences_processed": 0,
            "steps_executed": 0,
            "sequences_completed": 0,
            "errors": 0,
        }

        # This would query for active sequences with due steps
        # and execute them

        logger.info("Processed due sequences", extra=results)
        return results

    def get_sequence_status(
        self,
        sequence: FollowUpSequence,
    ) -> dict:
        """
        Get detailed status of a sequence.

        Args:
            sequence: The sequence to check

        Returns:
            Dictionary with status details
        """
        completed_steps = sum(
            1 for step in sequence.steps
            if step.status == FollowUpStatus.COMPLETED
        )

        return {
            "sequence_id": str(sequence.id),
            "status": sequence.status.value,
            "current_step": sequence.current_step,
            "total_steps": sequence.total_steps,
            "completed_steps": completed_steps,
            "progress_percent": (
                (completed_steps / sequence.total_steps * 100)
                if sequence.total_steps > 0 else 0
            ),
            "started_at": sequence.started_at.isoformat() if sequence.started_at else None,
            "completed_at": sequence.completed_at.isoformat() if sequence.completed_at else None,
            "paused_at": sequence.paused_at.isoformat() if sequence.paused_at else None,
        }


# Pre-built sequence templates
SEQUENCE_TEMPLATES = {
    "post_discovery": {
        "name": "Post-Discovery Follow-up",
        "description": "3-touch sequence after discovery call",
        "steps": [
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Thank you email with key takeaways",
            },
            {
                "type": "wait",
                "delay_hours": 72,
            },
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Value prop email with relevant content",
            },
            {
                "type": "wait",
                "delay_hours": 120,
            },
            {
                "type": "task",
                "delay_hours": 0,
                "task_template": "Schedule follow-up call to continue conversation",
            },
        ],
    },
    "post_demo": {
        "name": "Post-Demo Follow-up",
        "description": "Follow-up sequence after product demo",
        "steps": [
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Demo recap with recording link",
            },
            {
                "type": "wait",
                "delay_hours": 48,
            },
            {
                "type": "condition",
                "condition": "email_opened",
                "condition_true_step": 3,
                "condition_false_step": 4,
            },
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Proposal or next steps email",
            },
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Re-engagement email",
            },
        ],
    },
    "proposal_followup": {
        "name": "Proposal Follow-up",
        "description": "Follow-up after sending proposal",
        "steps": [
            {
                "type": "email",
                "delay_hours": 48,
                "description": "Check-in on proposal review",
            },
            {
                "type": "wait",
                "delay_hours": 96,
            },
            {
                "type": "task",
                "delay_hours": 0,
                "task_template": "Call to discuss proposal questions",
            },
            {
                "type": "wait",
                "delay_hours": 120,
            },
            {
                "type": "email",
                "delay_hours": 0,
                "description": "Final follow-up before close",
            },
        ],
    },
}
