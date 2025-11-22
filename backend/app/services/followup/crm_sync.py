"""
CRM synchronization service for follow-ups.

Syncs follow-up tasks, notes, and activities to HubSpot and other CRM systems.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ...models.followup import (
    CRMSyncRecord,
    CRMTaskStatus,
    FollowUpBase,
    FollowUpEmail,
    FollowUpMeetingSuggestion,
    FollowUpTask,
    FollowUpType,
)

logger = logging.getLogger(__name__)


class CRMSyncService:
    """
    Synchronizes follow-ups with CRM systems.

    Supports:
    - Task creation in CRM
    - Activity/note logging
    - Contact timeline updates
    - Deal association
    - Retry logic for failed syncs
    """

    def __init__(
        self,
        hubspot_client=None,
        salesforce_client=None,
        max_retries: int = 3,
    ):
        """
        Initialize the CRM sync service.

        Args:
            hubspot_client: HubSpot API client
            salesforce_client: Salesforce API client (optional)
            max_retries: Maximum retry attempts for failed syncs
        """
        self.hubspot_client = hubspot_client
        self.salesforce_client = salesforce_client
        self.max_retries = max_retries

    async def sync_followup(
        self,
        followup: FollowUpBase,
        contact_id: Optional[str] = None,
        deal_id: Optional[str] = None,
    ) -> CRMSyncRecord:
        """
        Sync a follow-up to the CRM.

        Args:
            followup: The follow-up to sync
            contact_id: CRM contact ID to associate
            deal_id: CRM deal ID to associate

        Returns:
            CRMSyncRecord with sync status
        """
        record = CRMSyncRecord(
            followup_id=followup.id,
            followup_type=followup.type,
            crm_type="hubspot",
        )

        try:
            if isinstance(followup, FollowUpTask):
                record = await self._sync_task(followup, contact_id, deal_id, record)
            elif isinstance(followup, FollowUpEmail):
                record = await self._sync_email(followup, contact_id, deal_id, record)
            elif isinstance(followup, FollowUpMeetingSuggestion):
                record = await self._sync_meeting(followup, contact_id, deal_id, record)
            else:
                # Sync as generic activity
                record = await self._sync_activity(followup, contact_id, deal_id, record)

        except Exception as e:
            record.status = CRMTaskStatus.FAILED
            record.error_message = str(e)
            logger.error(
                f"Failed to sync follow-up {followup.id}: {e}",
                extra={"followup_id": str(followup.id)},
            )

        return record

    async def _sync_task(
        self,
        task: FollowUpTask,
        contact_id: Optional[str],
        deal_id: Optional[str],
        record: CRMSyncRecord,
    ) -> CRMSyncRecord:
        """Sync a task follow-up to CRM."""
        record.crm_object_type = "task"

        if not self.hubspot_client:
            logger.warning("No HubSpot client configured for task sync")
            record.status = CRMTaskStatus.SKIPPED
            return record

        # Build task payload
        payload = {
            "properties": {
                "hs_task_subject": task.title,
                "hs_task_body": task.description or "",
                "hs_task_status": "NOT_STARTED",
                "hs_task_priority": self._map_priority(task.priority.value),
                "hs_task_type": self._map_task_category(task.category.value),
            }
        }

        if task.due_at:
            payload["properties"]["hs_timestamp"] = int(task.due_at.timestamp() * 1000)

        record.request_payload = payload

        try:
            # Create task via HubSpot client
            result = await self.hubspot_client.create_task(
                subject=task.title,
                body=task.description,
                due_date=task.due_at,
                priority=task.priority.value,
            )

            record.crm_object_id = result.get("id")
            record.status = CRMTaskStatus.SYNCED
            record.synced_at = datetime.utcnow()
            record.response_payload = result

            # Associate with contact and deal
            if contact_id and record.crm_object_id:
                await self._associate_task_to_contact(record.crm_object_id, contact_id)
            if deal_id and record.crm_object_id:
                await self._associate_task_to_deal(record.crm_object_id, deal_id)

            # Update follow-up with CRM task ID
            task.crm_task_id = record.crm_object_id
            task.crm_synced_at = datetime.utcnow()

            logger.info(
                f"Synced task {task.id} to HubSpot task {record.crm_object_id}"
            )

        except Exception as e:
            record.status = CRMTaskStatus.FAILED
            record.error_message = str(e)
            raise

        return record

    async def _sync_email(
        self,
        email: FollowUpEmail,
        contact_id: Optional[str],
        deal_id: Optional[str],
        record: CRMSyncRecord,
    ) -> CRMSyncRecord:
        """Sync an email follow-up to CRM as an activity."""
        record.crm_object_type = "note"

        if not self.hubspot_client:
            logger.warning("No HubSpot client configured for email sync")
            record.status = CRMTaskStatus.SKIPPED
            return record

        # Log email as a note/activity in CRM
        note_body = f"""
**Follow-up Email**
**To:** {email.recipient.name} ({email.recipient.email})
**Subject:** {email.draft.subject}
**Status:** {email.status.value}

---
{email.draft.body_text}
"""

        try:
            # Create note via HubSpot client
            if contact_id:
                result = await self.hubspot_client.add_note_to_contact(
                    contact_id=contact_id,
                    note_body=note_body,
                )
                record.crm_object_id = result.get("id")
                record.status = CRMTaskStatus.SYNCED
                record.synced_at = datetime.utcnow()
                record.response_payload = result

                logger.info(
                    f"Synced email {email.id} to HubSpot note {record.crm_object_id}"
                )
            else:
                record.status = CRMTaskStatus.SKIPPED
                record.error_message = "No contact ID provided for email sync"

        except Exception as e:
            record.status = CRMTaskStatus.FAILED
            record.error_message = str(e)
            raise

        return record

    async def _sync_meeting(
        self,
        meeting: FollowUpMeetingSuggestion,
        contact_id: Optional[str],
        deal_id: Optional[str],
        record: CRMSyncRecord,
    ) -> CRMSyncRecord:
        """Sync a meeting suggestion to CRM."""
        record.crm_object_type = "meeting"

        if not self.hubspot_client:
            logger.warning("No HubSpot client configured for meeting sync")
            record.status = CRMTaskStatus.SKIPPED
            return record

        # Create meeting in HubSpot
        suggestion = meeting.suggestion

        try:
            # If meeting is booked, sync as completed meeting
            # Otherwise, sync as scheduled meeting
            if meeting.booked_at:
                result = await self.hubspot_client.create_meeting(
                    title=suggestion.title,
                    description=suggestion.description,
                    start_time=meeting.booked_at,
                    duration_minutes=suggestion.suggested_duration_minutes,
                )
            else:
                # Create as a task to schedule the meeting
                result = await self.hubspot_client.create_task(
                    subject=f"Schedule: {suggestion.title}",
                    body=f"""
Meeting suggestion generated from sales call.

**Type:** {suggestion.meeting_type.value}
**Suggested Duration:** {suggestion.suggested_duration_minutes} minutes

**Agenda:**
{chr(10).join(f'- {item}' for item in suggestion.agenda)}

**Reasoning:** {suggestion.reasoning}
""",
                    priority="HIGH",
                )

            record.crm_object_id = result.get("id")
            record.status = CRMTaskStatus.SYNCED
            record.synced_at = datetime.utcnow()
            record.response_payload = result

            logger.info(
                f"Synced meeting {meeting.id} to HubSpot {record.crm_object_id}"
            )

        except Exception as e:
            record.status = CRMTaskStatus.FAILED
            record.error_message = str(e)
            raise

        return record

    async def _sync_activity(
        self,
        followup: FollowUpBase,
        contact_id: Optional[str],
        deal_id: Optional[str],
        record: CRMSyncRecord,
    ) -> CRMSyncRecord:
        """Sync a generic follow-up as an activity note."""
        record.crm_object_type = "note"

        if not self.hubspot_client or not contact_id:
            record.status = CRMTaskStatus.SKIPPED
            return record

        note_body = f"""
**Follow-up Generated**
**Type:** {followup.type.value}
**Status:** {followup.status.value}
**Priority:** {followup.priority.value}
**Created:** {followup.created_at.isoformat()}
"""

        try:
            result = await self.hubspot_client.add_note_to_contact(
                contact_id=contact_id,
                note_body=note_body,
            )
            record.crm_object_id = result.get("id")
            record.status = CRMTaskStatus.SYNCED
            record.synced_at = datetime.utcnow()

        except Exception as e:
            record.status = CRMTaskStatus.FAILED
            record.error_message = str(e)
            raise

        return record

    async def _associate_task_to_contact(
        self,
        task_id: str,
        contact_id: str,
    ) -> None:
        """Associate a CRM task with a contact."""
        if self.hubspot_client:
            await self.hubspot_client.associate_task_to_contact(task_id, contact_id)

    async def _associate_task_to_deal(
        self,
        task_id: str,
        deal_id: str,
    ) -> None:
        """Associate a CRM task with a deal."""
        if self.hubspot_client:
            await self.hubspot_client.associate_task_to_deal(task_id, deal_id)

    def _map_priority(self, priority: str) -> str:
        """Map internal priority to HubSpot priority."""
        mapping = {
            "low": "LOW",
            "medium": "MEDIUM",
            "high": "HIGH",
            "urgent": "HIGH",
        }
        return mapping.get(priority, "MEDIUM")

    def _map_task_category(self, category: str) -> str:
        """Map internal category to HubSpot task type."""
        mapping = {
            "call": "CALL",
            "email": "EMAIL",
            "meeting": "MEETING",
            "todo": "TODO",
        }
        return mapping.get(category, "TODO")

    async def retry_failed_syncs(
        self,
        max_records: int = 100,
    ) -> dict[str, int]:
        """
        Retry failed sync operations.

        Args:
            max_records: Maximum records to retry

        Returns:
            Dictionary with retry statistics
        """
        results = {
            "retried": 0,
            "succeeded": 0,
            "failed": 0,
        }

        # This would query for failed sync records and retry them
        # Implementation depends on persistence layer

        logger.info("Retried failed syncs", extra=results)
        return results

    async def bulk_sync(
        self,
        followups: list[FollowUpBase],
        contact_id: Optional[str] = None,
        deal_id: Optional[str] = None,
    ) -> list[CRMSyncRecord]:
        """
        Bulk sync multiple follow-ups.

        Args:
            followups: List of follow-ups to sync
            contact_id: CRM contact ID
            deal_id: CRM deal ID

        Returns:
            List of sync records
        """
        records = []

        for followup in followups:
            record = await self.sync_followup(followup, contact_id, deal_id)
            records.append(record)

        synced_count = sum(1 for r in records if r.status == CRMTaskStatus.SYNCED)
        logger.info(f"Bulk synced {synced_count}/{len(followups)} follow-ups")

        return records

    async def update_crm_task_status(
        self,
        followup: FollowUpTask,
    ) -> tuple[bool, Optional[str]]:
        """
        Update CRM task status to match follow-up status.

        Args:
            followup: The follow-up task

        Returns:
            Tuple of (success, error_message)
        """
        if not followup.crm_task_id:
            return False, "No CRM task ID"

        if not self.hubspot_client:
            return False, "No HubSpot client configured"

        try:
            status_mapping = {
                "completed": "COMPLETED",
                "cancelled": "DEFERRED",
                "in_progress": "IN_PROGRESS",
                "pending": "NOT_STARTED",
            }

            crm_status = status_mapping.get(
                followup.status.value, "NOT_STARTED"
            )

            await self.hubspot_client.update_task(
                task_id=followup.crm_task_id,
                status=crm_status,
            )

            logger.info(
                f"Updated CRM task {followup.crm_task_id} status to {crm_status}"
            )
            return True, None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to update CRM task status: {error_msg}")
            return False, error_msg

    def get_sync_status(
        self,
        followup_id: UUID,
    ) -> Optional[CRMSyncRecord]:
        """
        Get the sync status for a follow-up.

        Args:
            followup_id: ID of the follow-up

        Returns:
            CRM sync record if found
        """
        # This would query the sync records table
        # Placeholder implementation
        return None


class CRMFieldMapper:
    """Maps follow-up fields to CRM fields."""

    def __init__(self, field_mappings: Optional[dict] = None):
        """
        Initialize the field mapper.

        Args:
            field_mappings: Custom field mappings
        """
        self.field_mappings = field_mappings or self._get_default_mappings()

    def _get_default_mappings(self) -> dict:
        """Get default HubSpot field mappings."""
        return {
            "task": {
                "title": "hs_task_subject",
                "description": "hs_task_body",
                "due_at": "hs_timestamp",
                "priority": "hs_task_priority",
                "status": "hs_task_status",
            },
            "note": {
                "body": "hs_note_body",
                "created_at": "hs_timestamp",
            },
            "meeting": {
                "title": "hs_meeting_title",
                "description": "hs_meeting_body",
                "start_time": "hs_meeting_start_time",
                "end_time": "hs_meeting_end_time",
            },
        }

    def map_to_crm(
        self,
        followup: FollowUpBase,
        crm_type: str = "hubspot",
    ) -> dict:
        """
        Map follow-up fields to CRM fields.

        Args:
            followup: The follow-up to map
            crm_type: Target CRM type

        Returns:
            Dictionary with mapped CRM fields
        """
        result = {}

        if isinstance(followup, FollowUpTask):
            mappings = self.field_mappings.get("task", {})
            for internal_field, crm_field in mappings.items():
                value = getattr(followup, internal_field, None)
                if value is not None:
                    result[crm_field] = self._format_value(value)

        return result

    def _format_value(self, value) -> any:
        """Format a value for CRM API."""
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)  # HubSpot uses milliseconds
        if hasattr(value, "value"):
            return value.value  # Enum
        return value
