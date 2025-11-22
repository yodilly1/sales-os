"""
Email Workflow Integrations for Sales OS

Provides workflow integrations for:
- Post-call follow-up emails
- Content delivery emails
- Prospect outreach sequences
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from ...models.email import (
    EmailMessageCreate,
    EmailTemplate,
    EmailTemplateType,
    EmailRecipient,
    OutreachSequence,
    OutreachSequenceStep,
)
from .service import EmailService
from .template_renderer import DefaultTemplates, TemplateRenderer


logger = logging.getLogger(__name__)


# Workflow Models
class FollowUpType(str, Enum):
    """Types of follow-up emails."""
    POST_CALL = "post_call"
    POST_DEMO = "post_demo"
    POST_MEETING = "post_meeting"
    CHECK_IN = "check_in"


class ContentType(str, Enum):
    """Types of content for delivery."""
    DECK = "deck"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"


class SequenceStatus(str, Enum):
    """Status of a prospect in a sequence."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class FollowUpRequest(BaseModel):
    """Request for sending a follow-up email."""
    recipient_email: EmailStr
    recipient_name: str
    follow_up_type: FollowUpType = FollowUpType.POST_CALL

    # Meeting details
    meeting_date: Optional[str] = None
    topic: Optional[str] = None

    # SPICED data from call analysis
    key_points: Optional[List[str]] = None
    action_items: Optional[List[str]] = None

    # CTA
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None

    # Custom message
    custom_message: Optional[str] = None

    # Sender info
    sender_name: str
    sender_email: EmailStr
    sender_title: Optional[str] = None
    sender_phone: Optional[str] = None

    # Metadata
    call_id: Optional[UUID] = None
    hubspot_contact_id: Optional[str] = None


class ContentDeliveryRequest(BaseModel):
    """Request for sending a content delivery email."""
    recipient_email: EmailStr
    recipient_name: str
    recipient_company: Optional[str] = None

    # Content details
    content_type: ContentType
    content_title: str
    content_description: Optional[str] = None
    content_url: str

    # Additional content
    key_takeaways: Optional[List[str]] = None
    related_content: Optional[List[Dict[str, str]]] = None

    # Custom messaging
    custom_intro: Optional[str] = None
    cta_message: Optional[str] = None
    download_text: Optional[str] = None

    # Sender info
    sender_name: str
    sender_email: EmailStr
    sender_title: Optional[str] = None

    # Metadata
    content_id: Optional[UUID] = None
    hubspot_contact_id: Optional[str] = None


class ProspectForSequence(BaseModel):
    """Prospect to add to an outreach sequence."""
    email: EmailStr
    name: str
    company: Optional[str] = None

    # Personalization data
    personalized_opener: Optional[str] = None
    company_highlight: Optional[str] = None
    pain_point: Optional[str] = None
    industry: Optional[str] = None
    value_proposition: Optional[str] = None
    social_proof: Optional[str] = None

    # Contact info
    hubspot_contact_id: Optional[str] = None
    linkedin_url: Optional[str] = None


class SequenceProspectStatus(BaseModel):
    """Status of a prospect in a sequence."""
    prospect_email: str
    sequence_id: UUID
    status: SequenceStatus
    current_step: int
    next_send_at: Optional[datetime] = None
    last_sent_at: Optional[datetime] = None
    opened: bool = False
    clicked: bool = False
    replied: bool = False


# Workflow Classes
class PostCallFollowUpWorkflow:
    """
    Workflow for sending post-call follow-up emails.

    Integrates with:
    - Transcript analysis (SPICED extraction)
    - HubSpot CRM for contact tracking
    - Email tracking for engagement
    """

    def __init__(self, email_service: EmailService):
        """Initialize the workflow."""
        self.email_service = email_service
        self.template_renderer = TemplateRenderer()
        self.default_template = DefaultTemplates.follow_up_template()

    async def send_follow_up(
        self,
        request: FollowUpRequest,
        template: Optional[EmailTemplate] = None,
    ) -> Dict[str, Any]:
        """
        Send a post-call follow-up email.

        Args:
            request: Follow-up request details
            template: Optional custom template

        Returns:
            Result with message ID and status
        """
        template = template or self.default_template

        # Build template variables from request
        variables = {
            "recipient_name": request.recipient_name,
            "meeting_date": request.meeting_date,
            "topic": request.topic,
            "key_points": request.key_points or [],
            "action_items": request.action_items or [],
            "cta_text": request.cta_text,
            "cta_url": request.cta_url,
            "custom_message": request.custom_message,
            "sender_name": request.sender_name,
            "sender_email": request.sender_email,
            "sender_title": request.sender_title,
            "sender_phone": request.sender_phone,
        }

        # Render template
        rendered = self.template_renderer.render(template, variables)

        # Create email message
        message = EmailMessageCreate(
            subject=rendered["subject"],
            from_email=request.sender_email,
            from_name=request.sender_name,
            html_content=rendered["html"],
            text_content=rendered["text"],
            to_recipients=[
                EmailRecipient(
                    email=request.recipient_email,
                    name=request.recipient_name,
                )
            ],
            tags=["follow-up", request.follow_up_type.value],
            metadata={
                "follow_up_type": request.follow_up_type.value,
                "call_id": str(request.call_id) if request.call_id else None,
                "hubspot_contact_id": request.hubspot_contact_id,
            },
        )

        # Send email
        response = await self.email_service.send_email(message, template)

        logger.info(
            f"Sent {request.follow_up_type.value} follow-up to "
            f"{request.recipient_email}: {response.status.value}"
        )

        return {
            "success": response.success,
            "message_id": str(response.message_id),
            "status": response.status.value,
            "follow_up_type": request.follow_up_type.value,
            "recipient": request.recipient_email,
        }

    async def send_batch_follow_ups(
        self,
        requests: List[FollowUpRequest],
        template: Optional[EmailTemplate] = None,
    ) -> List[Dict[str, Any]]:
        """Send follow-ups to multiple recipients."""
        results = []
        for request in requests:
            result = await self.send_follow_up(request, template)
            results.append(result)
        return results


class ContentDeliveryWorkflow:
    """
    Workflow for delivering content (decks, proposals, etc.) via email.

    Integrates with:
    - Content generation service
    - PDF/Deck rendering
    - HubSpot for tracking
    """

    def __init__(self, email_service: EmailService):
        """Initialize the workflow."""
        self.email_service = email_service
        self.template_renderer = TemplateRenderer()
        self.default_template = DefaultTemplates.content_delivery_template()

    async def deliver_content(
        self,
        request: ContentDeliveryRequest,
        template: Optional[EmailTemplate] = None,
    ) -> Dict[str, Any]:
        """
        Deliver content via email.

        Args:
            request: Content delivery request
            template: Optional custom template

        Returns:
            Result with message ID and status
        """
        template = template or self.default_template

        # Map content type to display name
        content_type_display = {
            ContentType.DECK: "Presentation",
            ContentType.PROPOSAL: "Proposal",
            ContentType.ONE_PAGER: "One-Pager",
            ContentType.BATTLECARD: "Battlecard",
            ContentType.CASE_STUDY: "Case Study",
            ContentType.WHITEPAPER: "Whitepaper",
        }

        # Build template variables
        variables = {
            "recipient_name": request.recipient_name,
            "recipient_company": request.recipient_company,
            "content_type": content_type_display.get(
                request.content_type, "Resource"
            ),
            "content_title": request.content_title,
            "content_description": request.content_description,
            "content_url": request.content_url,
            "key_takeaways": request.key_takeaways or [],
            "related_content": request.related_content or [],
            "custom_intro": request.custom_intro,
            "cta_message": request.cta_message,
            "download_text": request.download_text,
            "sender_name": request.sender_name,
            "sender_email": request.sender_email,
            "sender_title": request.sender_title,
        }

        # Render template
        rendered = self.template_renderer.render(template, variables)

        # Create email message
        message = EmailMessageCreate(
            subject=rendered["subject"],
            from_email=request.sender_email,
            from_name=request.sender_name,
            html_content=rendered["html"],
            text_content=rendered["text"],
            to_recipients=[
                EmailRecipient(
                    email=request.recipient_email,
                    name=request.recipient_name,
                )
            ],
            tags=["content-delivery", request.content_type.value],
            metadata={
                "content_type": request.content_type.value,
                "content_id": str(request.content_id) if request.content_id else None,
                "hubspot_contact_id": request.hubspot_contact_id,
            },
        )

        # Send email
        response = await self.email_service.send_email(message, template)

        logger.info(
            f"Delivered {request.content_type.value} to "
            f"{request.recipient_email}: {response.status.value}"
        )

        return {
            "success": response.success,
            "message_id": str(response.message_id),
            "status": response.status.value,
            "content_type": request.content_type.value,
            "recipient": request.recipient_email,
        }


class OutreachSequenceWorkflow:
    """
    Workflow for managing prospect outreach sequences.

    Provides:
    - Multi-step email sequences
    - Automated follow-ups with delays
    - Stop conditions (reply, bounce, unsubscribe)
    - Personalization support
    """

    def __init__(self, email_service: EmailService):
        """Initialize the workflow."""
        self.email_service = email_service
        self.template_renderer = TemplateRenderer()

        # In-memory storage (replace with database in production)
        self._sequences: Dict[UUID, OutreachSequence] = {}
        self._prospect_status: Dict[str, SequenceProspectStatus] = {}
        self._pending_sends: List[Dict[str, Any]] = []

    async def create_sequence(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        from_email: str,
        from_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> OutreachSequence:
        """
        Create a new outreach sequence.

        Args:
            name: Sequence name
            steps: List of step definitions
            from_email: Sender email
            from_name: Sender name
            description: Sequence description

        Returns:
            Created OutreachSequence
        """
        sequence_steps = []
        for i, step in enumerate(steps):
            sequence_steps.append(OutreachSequenceStep(
                step_number=i + 1,
                template_id=step.get("template_id"),
                delay_days=step.get("delay_days", 0),
                delay_hours=step.get("delay_hours", 0),
                skip_if_replied=step.get("skip_if_replied", True),
                skip_if_opened=step.get("skip_if_opened", False),
                skip_if_clicked=step.get("skip_if_clicked", False),
            ))

        sequence = OutreachSequence(
            name=name,
            description=description,
            steps=sequence_steps,
            from_email=from_email,
            from_name=from_name,
        )

        self._sequences[sequence.id] = sequence

        logger.info(f"Created sequence '{name}' with {len(steps)} steps")

        return sequence

    async def add_prospect_to_sequence(
        self,
        sequence_id: UUID,
        prospect: ProspectForSequence,
        start_immediately: bool = True,
    ) -> SequenceProspectStatus:
        """
        Add a prospect to an outreach sequence.

        Args:
            sequence_id: Sequence to add to
            prospect: Prospect details
            start_immediately: Send first email immediately

        Returns:
            Prospect status in sequence
        """
        sequence = self._sequences.get(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")

        # Check if already in sequence
        key = f"{prospect.email}:{sequence_id}"
        if key in self._prospect_status:
            existing = self._prospect_status[key]
            if existing.status == SequenceStatus.ACTIVE:
                logger.info(f"{prospect.email} already active in sequence")
                return existing

        # Create status
        now = datetime.utcnow()
        status = SequenceProspectStatus(
            prospect_email=prospect.email,
            sequence_id=sequence_id,
            status=SequenceStatus.ACTIVE,
            current_step=0,
            next_send_at=now if start_immediately else None,
        )

        self._prospect_status[key] = status

        # Schedule first email
        if start_immediately:
            await self._send_sequence_step(sequence, prospect, 1)
            status.current_step = 1
            status.last_sent_at = now

            # Schedule next step
            if len(sequence.steps) > 1:
                next_step = sequence.steps[1]
                delay = timedelta(
                    days=next_step.delay_days,
                    hours=next_step.delay_hours
                )
                status.next_send_at = now + delay

        sequence.total_prospects += 1

        logger.info(f"Added {prospect.email} to sequence '{sequence.name}'")

        return status

    async def _send_sequence_step(
        self,
        sequence: OutreachSequence,
        prospect: ProspectForSequence,
        step_number: int,
    ) -> bool:
        """Send a specific step in the sequence."""
        if step_number > len(sequence.steps):
            return False

        step = sequence.steps[step_number - 1]

        # Get template for this step
        # In production, fetch from database by template_id
        if step_number == 1:
            template = DefaultTemplates.intro_template()
        else:
            template = DefaultTemplates.follow_up_template()

        # Build variables
        variables = {
            "recipient_name": prospect.name,
            "recipient_company": prospect.company,
            "personalized_opener": prospect.personalized_opener,
            "company_highlight": prospect.company_highlight,
            "pain_point": prospect.pain_point,
            "industry": prospect.industry,
            "value_proposition": prospect.value_proposition,
            "social_proof": prospect.social_proof,
            "sender_name": sequence.from_name or "Sales Team",
            "company_name": "Our Company",  # From config
        }

        # Render template
        rendered = self.template_renderer.render(template, variables)

        # Create and send email
        message = EmailMessageCreate(
            subject=rendered["subject"],
            from_email=sequence.from_email,
            from_name=sequence.from_name,
            html_content=rendered["html"],
            text_content=rendered["text"],
            to_recipients=[
                EmailRecipient(email=prospect.email, name=prospect.name)
            ],
            sequence_id=sequence.id,
            sequence_step=step_number,
            tags=["outreach", f"sequence-{sequence.id}", f"step-{step_number}"],
            metadata={
                "sequence_name": sequence.name,
                "step_number": step_number,
                "hubspot_contact_id": prospect.hubspot_contact_id,
            },
        )

        response = await self.email_service.send_email(message, template)

        logger.info(
            f"Sent step {step_number} to {prospect.email}: {response.status.value}"
        )

        return response.success

    async def process_reply(
        self,
        prospect_email: str,
        sequence_id: UUID,
    ) -> None:
        """
        Process a reply from a prospect, stopping the sequence.

        Args:
            prospect_email: Email that replied
            sequence_id: Sequence they're in
        """
        key = f"{prospect_email}:{sequence_id}"
        status = self._prospect_status.get(key)

        if status:
            status.status = SequenceStatus.REPLIED
            status.replied = True
            status.next_send_at = None

            sequence = self._sequences.get(sequence_id)
            if sequence:
                sequence.total_replied += 1

            logger.info(f"{prospect_email} replied, stopping sequence")

    async def pause_prospect(
        self,
        prospect_email: str,
        sequence_id: UUID,
    ) -> bool:
        """Pause a prospect in a sequence."""
        key = f"{prospect_email}:{sequence_id}"
        status = self._prospect_status.get(key)

        if status and status.status == SequenceStatus.ACTIVE:
            status.status = SequenceStatus.PAUSED
            status.next_send_at = None
            logger.info(f"Paused {prospect_email} in sequence")
            return True

        return False

    async def resume_prospect(
        self,
        prospect_email: str,
        sequence_id: UUID,
    ) -> bool:
        """Resume a paused prospect."""
        key = f"{prospect_email}:{sequence_id}"
        status = self._prospect_status.get(key)

        if status and status.status == SequenceStatus.PAUSED:
            status.status = SequenceStatus.ACTIVE

            # Calculate next send time
            sequence = self._sequences.get(sequence_id)
            if sequence and status.current_step < len(sequence.steps):
                next_step = sequence.steps[status.current_step]
                delay = timedelta(
                    days=next_step.delay_days,
                    hours=next_step.delay_hours
                )
                status.next_send_at = datetime.utcnow() + delay

            logger.info(f"Resumed {prospect_email} in sequence")
            return True

        return False

    async def remove_prospect(
        self,
        prospect_email: str,
        sequence_id: UUID,
    ) -> bool:
        """Remove a prospect from a sequence."""
        key = f"{prospect_email}:{sequence_id}"

        if key in self._prospect_status:
            del self._prospect_status[key]
            logger.info(f"Removed {prospect_email} from sequence")
            return True

        return False

    async def get_prospect_status(
        self,
        prospect_email: str,
        sequence_id: Optional[UUID] = None,
    ) -> List[SequenceProspectStatus]:
        """Get status of a prospect in sequences."""
        results = []

        for key, status in self._prospect_status.items():
            if prospect_email in key:
                if sequence_id is None or status.sequence_id == sequence_id:
                    results.append(status)

        return results

    async def get_sequence_stats(
        self,
        sequence_id: UUID,
    ) -> Dict[str, Any]:
        """Get statistics for a sequence."""
        sequence = self._sequences.get(sequence_id)
        if not sequence:
            return {}

        # Count statuses
        statuses = [
            s for s in self._prospect_status.values()
            if s.sequence_id == sequence_id
        ]

        active = sum(1 for s in statuses if s.status == SequenceStatus.ACTIVE)
        paused = sum(1 for s in statuses if s.status == SequenceStatus.PAUSED)
        completed = sum(1 for s in statuses if s.status == SequenceStatus.COMPLETED)
        replied = sum(1 for s in statuses if s.status == SequenceStatus.REPLIED)
        bounced = sum(1 for s in statuses if s.status == SequenceStatus.BOUNCED)

        return {
            "sequence_id": str(sequence_id),
            "sequence_name": sequence.name,
            "total_prospects": len(statuses),
            "active": active,
            "paused": paused,
            "completed": completed,
            "replied": replied,
            "bounced": bounced,
            "reply_rate": (replied / len(statuses) * 100) if statuses else 0,
        }

    async def process_due_sends(self) -> int:
        """
        Process all due sequence sends.

        This should be called periodically (e.g., every 5 minutes).

        Returns:
            Number of emails sent
        """
        now = datetime.utcnow()
        sent_count = 0

        for key, status in self._prospect_status.items():
            if status.status != SequenceStatus.ACTIVE:
                continue

            if status.next_send_at and status.next_send_at <= now:
                sequence = self._sequences.get(status.sequence_id)
                if not sequence:
                    continue

                next_step = status.current_step + 1
                if next_step > len(sequence.steps):
                    status.status = SequenceStatus.COMPLETED
                    sequence.total_completed += 1
                    continue

                # Check skip conditions
                step = sequence.steps[next_step - 1]
                if step.skip_if_replied and status.replied:
                    continue
                if step.skip_if_opened and status.opened:
                    continue
                if step.skip_if_clicked and status.clicked:
                    continue

                # Create prospect object (in production, fetch from DB)
                prospect = ProspectForSequence(
                    email=status.prospect_email,
                    name="",  # Would be fetched from DB
                )

                # Send the email
                success = await self._send_sequence_step(
                    sequence, prospect, next_step
                )

                if success:
                    status.current_step = next_step
                    status.last_sent_at = now
                    sent_count += 1

                    # Schedule next step
                    if next_step < len(sequence.steps):
                        next_next_step = sequence.steps[next_step]
                        delay = timedelta(
                            days=next_next_step.delay_days,
                            hours=next_next_step.delay_hours
                        )
                        status.next_send_at = now + delay
                    else:
                        status.next_send_at = None

        logger.info(f"Processed {sent_count} sequence sends")
        return sent_count


# Convenience function to create all workflows
def create_email_workflows(
    email_service: EmailService,
) -> Dict[str, Any]:
    """
    Create all email workflow instances.

    Args:
        email_service: The email service to use

    Returns:
        Dictionary with workflow instances
    """
    return {
        "follow_up": PostCallFollowUpWorkflow(email_service),
        "content_delivery": ContentDeliveryWorkflow(email_service),
        "outreach_sequence": OutreachSequenceWorkflow(email_service),
    }
