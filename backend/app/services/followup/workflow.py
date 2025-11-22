"""
Approval workflow management for follow-ups.

Handles the approval process for follow-up content before sending.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...models.followup import (
    ApprovalMode,
    FollowUpApprovalRequest,
    FollowUpBase,
    FollowUpEmail,
    FollowUpStatus,
    FollowUpTask,
)

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """
    Manages the approval workflow for follow-ups.

    Supports:
    - Auto-approval mode (immediate scheduling)
    - Manual approval (requires user review)
    - Modification before approval
    - Audit trail of approvals
    """

    def __init__(
        self,
        default_mode: ApprovalMode = ApprovalMode.MANUAL,
        auto_approve_low_risk: bool = False,
        notification_service=None,
    ):
        """
        Initialize the approval workflow.

        Args:
            default_mode: Default approval mode for new follow-ups
            auto_approve_low_risk: Auto-approve low-risk content
            notification_service: Service for sending approval notifications
        """
        self.default_mode = default_mode
        self.auto_approve_low_risk = auto_approve_low_risk
        self.notification_service = notification_service

    async def submit_for_approval(
        self,
        followup: FollowUpBase,
        submitted_by: Optional[UUID] = None,
    ) -> tuple[bool, FollowUpStatus, Optional[str]]:
        """
        Submit a follow-up for approval.

        Args:
            followup: The follow-up to submit
            submitted_by: ID of user submitting

        Returns:
            Tuple of (success, new_status, message)
        """
        if followup.status not in [FollowUpStatus.DRAFT, FollowUpStatus.PENDING_APPROVAL]:
            return (
                False,
                followup.status,
                f"Cannot submit follow-up with status {followup.status.value}",
            )

        # Check approval mode
        if followup.approval_mode == ApprovalMode.AUTO:
            # Auto-approve immediately
            return await self._auto_approve(followup, submitted_by)

        if self.auto_approve_low_risk and self._is_low_risk(followup):
            # Auto-approve low-risk content
            return await self._auto_approve(followup, submitted_by)

        # Submit for manual approval
        followup.status = FollowUpStatus.PENDING_APPROVAL
        followup.updated_at = datetime.utcnow()

        # Send notification
        await self._notify_approvers(followup)

        logger.info(
            f"Follow-up {followup.id} submitted for approval",
            extra={
                "followup_id": str(followup.id),
                "submitted_by": str(submitted_by) if submitted_by else None,
            },
        )

        return True, FollowUpStatus.PENDING_APPROVAL, "Submitted for approval"

    async def _auto_approve(
        self,
        followup: FollowUpBase,
        approved_by: Optional[UUID] = None,
    ) -> tuple[bool, FollowUpStatus, Optional[str]]:
        """Auto-approve a follow-up."""
        followup.status = FollowUpStatus.APPROVED
        followup.approved_at = datetime.utcnow()
        followup.approved_by = approved_by
        followup.updated_at = datetime.utcnow()

        logger.info(
            f"Follow-up {followup.id} auto-approved",
            extra={
                "followup_id": str(followup.id),
                "approval_mode": "auto",
            },
        )

        return True, FollowUpStatus.APPROVED, "Auto-approved"

    def _is_low_risk(self, followup: FollowUpBase) -> bool:
        """
        Determine if a follow-up is low-risk for auto-approval.

        Low-risk criteria:
        - Internal tasks (not external communications)
        - Follow-up to existing thread
        - Template-based content with minimal customization
        """
        # Tasks are generally lower risk than emails
        if isinstance(followup, FollowUpTask):
            return True

        # Emails with replies are lower risk (ongoing conversation)
        if isinstance(followup, FollowUpEmail):
            if followup.reply_to_message_id:
                return True

        return False

    async def _notify_approvers(self, followup: FollowUpBase) -> None:
        """Send notification to approvers."""
        if not self.notification_service:
            logger.debug("No notification service configured")
            return

        try:
            await self.notification_service.send(
                event="followup.pending_approval",
                data={
                    "followup_id": str(followup.id),
                    "followup_type": followup.type.value,
                    "priority": followup.priority.value,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to send approval notification: {e}")

    async def approve(
        self,
        request: FollowUpApprovalRequest,
        followup: FollowUpBase,
        approver_id: UUID,
    ) -> tuple[bool, Optional[str]]:
        """
        Approve or reject a follow-up.

        Args:
            request: Approval request with decision and modifications
            followup: The follow-up being approved
            approver_id: ID of the approving user

        Returns:
            Tuple of (success, error_message)
        """
        if followup.status != FollowUpStatus.PENDING_APPROVAL:
            return (
                False,
                f"Follow-up is not pending approval (status: {followup.status.value})",
            )

        if not request.approved:
            # Rejected - return to draft
            followup.status = FollowUpStatus.DRAFT
            followup.updated_at = datetime.utcnow()
            logger.info(f"Follow-up {followup.id} rejected by {approver_id}")
            return True, None

        # Apply modifications if provided
        if request.modifications:
            self._apply_modifications(followup, request.modifications)

        # Approve
        followup.status = FollowUpStatus.APPROVED
        followup.approved_by = approver_id
        followup.approved_at = datetime.utcnow()
        followup.updated_at = datetime.utcnow()

        # Set schedule if provided
        if request.schedule_at:
            followup.scheduled_at = request.schedule_at
            followup.status = FollowUpStatus.SCHEDULED

        logger.info(
            f"Follow-up {followup.id} approved by {approver_id}",
            extra={
                "followup_id": str(followup.id),
                "approver_id": str(approver_id),
                "scheduled_at": followup.scheduled_at.isoformat() if followup.scheduled_at else None,
            },
        )

        return True, None

    def _apply_modifications(
        self,
        followup: FollowUpBase,
        modifications: dict,
    ) -> None:
        """Apply modifications to a follow-up before approval."""
        if isinstance(followup, FollowUpEmail):
            self._apply_email_modifications(followup, modifications)
        elif isinstance(followup, FollowUpTask):
            self._apply_task_modifications(followup, modifications)

    def _apply_email_modifications(
        self,
        email: FollowUpEmail,
        modifications: dict,
    ) -> None:
        """Apply modifications to an email follow-up."""
        if "subject" in modifications:
            email.draft.subject = modifications["subject"]
        if "body_html" in modifications:
            email.draft.body_html = modifications["body_html"]
        if "body_text" in modifications:
            email.draft.body_text = modifications["body_text"]

    def _apply_task_modifications(
        self,
        task: FollowUpTask,
        modifications: dict,
    ) -> None:
        """Apply modifications to a task follow-up."""
        if "title" in modifications:
            task.title = modifications["title"]
        if "description" in modifications:
            task.description = modifications["description"]
        if "due_at" in modifications:
            task.due_at = datetime.fromisoformat(modifications["due_at"])

    async def bulk_approve(
        self,
        followups: list[FollowUpBase],
        approver_id: UUID,
    ) -> dict[UUID, tuple[bool, Optional[str]]]:
        """
        Bulk approve multiple follow-ups.

        Args:
            followups: List of follow-ups to approve
            approver_id: ID of the approving user

        Returns:
            Dictionary mapping follow-up IDs to (success, error) tuples
        """
        results = {}

        for followup in followups:
            if followup.status != FollowUpStatus.PENDING_APPROVAL:
                results[followup.id] = (
                    False,
                    f"Not pending approval (status: {followup.status.value})",
                )
                continue

            # Approve
            followup.status = FollowUpStatus.APPROVED
            followup.approved_by = approver_id
            followup.approved_at = datetime.utcnow()
            followup.updated_at = datetime.utcnow()

            results[followup.id] = (True, None)

        approved_count = sum(1 for success, _ in results.values() if success)
        logger.info(f"Bulk approved {approved_count}/{len(followups)} follow-ups")

        return results

    async def get_pending_approvals(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> list[FollowUpBase]:
        """
        Get follow-ups pending approval.

        Args:
            user_id: Filter by created_by user (optional)
            limit: Maximum number to return

        Returns:
            List of pending follow-ups
        """
        # This would query the database
        # Placeholder implementation
        return []

    def get_approval_history(
        self,
        followup_id: UUID,
    ) -> list[dict]:
        """
        Get the approval history for a follow-up.

        Args:
            followup_id: ID of the follow-up

        Returns:
            List of approval history entries
        """
        # This would query the audit log
        # Placeholder implementation
        return []

    async def request_changes(
        self,
        followup: FollowUpBase,
        reviewer_id: UUID,
        feedback: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Request changes to a pending follow-up.

        Args:
            followup: The follow-up to request changes on
            reviewer_id: ID of the reviewer
            feedback: Feedback explaining requested changes

        Returns:
            Tuple of (success, error_message)
        """
        if followup.status != FollowUpStatus.PENDING_APPROVAL:
            return (
                False,
                f"Follow-up is not pending approval (status: {followup.status.value})",
            )

        # Return to draft with feedback
        followup.status = FollowUpStatus.DRAFT
        followup.updated_at = datetime.utcnow()

        # Notify creator of requested changes
        if self.notification_service and followup.created_by:
            await self.notification_service.send(
                event="followup.changes_requested",
                data={
                    "followup_id": str(followup.id),
                    "reviewer_id": str(reviewer_id),
                    "feedback": feedback,
                },
                user_id=followup.created_by,
            )

        logger.info(
            f"Changes requested for follow-up {followup.id}",
            extra={
                "followup_id": str(followup.id),
                "reviewer_id": str(reviewer_id),
            },
        )

        return True, None


class ApprovalRule:
    """Configurable approval rule."""

    def __init__(
        self,
        name: str,
        condition: str,  # e.g., "priority == 'urgent'"
        require_approval: bool = True,
        approvers: Optional[list[UUID]] = None,
    ):
        self.name = name
        self.condition = condition
        self.require_approval = require_approval
        self.approvers = approvers or []

    def evaluate(self, followup: FollowUpBase) -> bool:
        """Evaluate if this rule applies to a follow-up."""
        # Simple rule evaluation
        # In production, use a proper rule engine
        if "priority" in self.condition:
            if "urgent" in self.condition and followup.priority.value == "urgent":
                return True
            if "high" in self.condition and followup.priority.value == "high":
                return True
        return False


class ApprovalRuleEngine:
    """Engine for evaluating approval rules."""

    def __init__(self, rules: Optional[list[ApprovalRule]] = None):
        self.rules = rules or []

    def add_rule(self, rule: ApprovalRule) -> None:
        """Add an approval rule."""
        self.rules.append(rule)

    def evaluate(self, followup: FollowUpBase) -> tuple[bool, list[UUID]]:
        """
        Evaluate all rules for a follow-up.

        Returns:
            Tuple of (requires_approval, list_of_approvers)
        """
        requires_approval = False
        approvers = set()

        for rule in self.rules:
            if rule.evaluate(followup):
                if rule.require_approval:
                    requires_approval = True
                    approvers.update(rule.approvers)

        return requires_approval, list(approvers)
