"""
Follow-up generation service.

Uses Claude AI to generate personalized follow-up content based on
SPICED analysis from sales calls.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from ...models.followup import (
    ApprovalMode,
    ContentRecommendation,
    ContentType,
    EmailDraft,
    EmailRecipient,
    FollowUpContentRecommendation,
    FollowUpEmail,
    FollowUpGenerationRequest,
    FollowUpGenerationResponse,
    FollowUpMeetingSuggestion,
    FollowUpTask,
    FollowUpType,
    MeetingSuggestion,
    MeetingType,
    Priority,
    ProspectContext,
    SPICEDContext,
    TaskCategory,
)

logger = logging.getLogger(__name__)


class FollowUpGenerator:
    """
    Generates follow-up content using Claude AI.

    Analyzes SPICED context from sales calls to create:
    - Personalized follow-up emails
    - Tasks and reminders
    - Content recommendations
    - Meeting suggestions
    """

    def __init__(
        self,
        claude_client=None,
        prompt_path: Optional[Path] = None,
    ):
        """
        Initialize the follow-up generator.

        Args:
            claude_client: Claude API client instance
            prompt_path: Path to the follow-up generation prompt template
        """
        self.claude_client = claude_client
        self.prompt_path = prompt_path or Path("claude/prompts/followup_generation.md")
        self._prompt_template: Optional[str] = None

    @property
    def prompt_template(self) -> str:
        """Load and cache the prompt template."""
        if self._prompt_template is None:
            try:
                self._prompt_template = self.prompt_path.read_text()
            except FileNotFoundError:
                logger.warning(f"Prompt template not found at {self.prompt_path}")
                self._prompt_template = self._get_default_prompt()
        return self._prompt_template

    async def generate_followups(
        self,
        request: FollowUpGenerationRequest,
    ) -> FollowUpGenerationResponse:
        """
        Generate all follow-up content from a call.

        Args:
            request: Generation request with context and preferences

        Returns:
            Response containing all generated follow-ups
        """
        start_time = time.time()

        response = FollowUpGenerationResponse(
            call_id=request.call_id,
        )

        # Generate each type of follow-up based on request
        if request.generate_email:
            emails = await self._generate_emails(request)
            response.emails = emails

        if request.generate_tasks:
            tasks = await self._generate_tasks(request)
            response.tasks = tasks

        if request.generate_content_recommendations:
            recommendations = await self._generate_content_recommendations(request)
            response.content_recommendations = recommendations

        if request.generate_meeting_suggestions:
            suggestions = await self._generate_meeting_suggestions(request)
            response.meeting_suggestions = suggestions

        # Calculate generation time
        response.generation_time_ms = int((time.time() - start_time) * 1000)
        response.model_used = "claude-sonnet-4-5-20250929"

        return response

    async def _generate_emails(
        self,
        request: FollowUpGenerationRequest,
    ) -> list[FollowUpEmail]:
        """Generate follow-up email drafts."""
        emails = []

        # Build the prompt for email generation
        prompt = self._build_email_prompt(request)

        # Call Claude API (placeholder - integrate with actual client)
        if self.claude_client:
            response = await self.claude_client.generate(
                prompt=prompt,
                max_tokens=2000,
            )
            emails = self._parse_email_response(response, request)
        else:
            # Generate default email based on SPICED context
            emails = [self._generate_default_email(request)]

        return emails

    def _build_email_prompt(self, request: FollowUpGenerationRequest) -> str:
        """Build the prompt for email generation."""
        spiced = request.spiced_context
        prospect = request.prospect_context

        prompt = f"""Generate a personalized follow-up email based on this sales call context:

## Prospect Information
- Name: {prospect.name}
- Title: {prospect.title or 'Unknown'}
- Company: {prospect.company}
- Industry: {prospect.industry or 'Unknown'}

## SPICED Analysis
- Situation: {spiced.situation or 'Not captured'}
- Pain: {spiced.pain or 'Not captured'}
- Impact: {spiced.impact or 'Not captured'}
- Critical Event: {spiced.critical_event or 'Not captured'}
- Expected Decision: {spiced.expected_decision or 'Not captured'}
- Decision Criteria: {spiced.decision_criteria or 'Not captured'}

## Key Quotes from Call
{chr(10).join(f'- "{q}"' for q in spiced.key_quotes) or 'None captured'}

## Action Items Discussed
{chr(10).join(f'- {item}' for item in spiced.action_items) or 'None captured'}

## Objections Raised
{chr(10).join(f'- {obj}' for obj in spiced.objections_raised) or 'None raised'}

## Sender Information
- Name: {request.sender_name}
- Title: {request.sender_title or ''}
- Company: {request.sender_company}

## Requirements
- Tone: {request.tone}
- Urgency: {request.urgency_level.value}

Generate a professional follow-up email that:
1. References specific points from the conversation
2. Addresses any pain points or objections raised
3. Provides clear next steps
4. Maintains the appropriate tone and urgency level

Return the email in JSON format with 'subject', 'body_html', and 'body_text' fields.
"""
        return prompt

    def _generate_default_email(
        self,
        request: FollowUpGenerationRequest,
    ) -> FollowUpEmail:
        """Generate a default email when Claude client is not available."""
        spiced = request.spiced_context
        prospect = request.prospect_context

        # Build subject line
        subject = f"Great speaking with you, {prospect.name.split()[0]}"
        if spiced.critical_event:
            subject = f"Following up on our conversation - {spiced.critical_event[:30]}"

        # Build email body
        body_parts = [
            f"Hi {prospect.name.split()[0]},",
            "",
            "Thank you for taking the time to speak with me today. I really enjoyed learning more about your situation and challenges.",
            "",
        ]

        # Add SPICED-specific content
        if spiced.pain:
            body_parts.extend([
                f"I understand that {spiced.pain} is a key challenge you're facing.",
                "",
            ])

        if spiced.impact:
            body_parts.extend([
                f"The impact you mentioned - {spiced.impact} - is something we've helped many organizations address successfully.",
                "",
            ])

        # Add action items
        if spiced.action_items:
            body_parts.extend([
                "As discussed, here are the next steps:",
                "",
            ])
            for item in spiced.action_items:
                body_parts.append(f"- {item}")
            body_parts.append("")

        # Add closing
        body_parts.extend([
            "Please let me know if you have any questions or would like to schedule a follow-up call.",
            "",
            "Best regards,",
            request.sender_name,
            request.sender_title or "",
            request.sender_company,
        ])

        body_text = "\n".join(body_parts)
        body_html = body_text.replace("\n", "<br>")

        return FollowUpEmail(
            call_id=request.call_id,
            prospect_id=uuid4(),  # Would come from prospect lookup
            recipient=EmailRecipient(
                email=prospect.email,
                name=prospect.name,
                role=prospect.title,
                company=prospect.company,
            ),
            draft=EmailDraft(
                subject=subject,
                body_html=f"<html><body>{body_html}</body></html>",
                body_text=body_text,
                tokens_used=["prospect_name", "pain_point", "action_items"],
            ),
            approval_mode=request.approval_mode,
            priority=request.urgency_level,
        )

    def _parse_email_response(
        self,
        response: str,
        request: FollowUpGenerationRequest,
    ) -> list[FollowUpEmail]:
        """Parse Claude's response into email models."""
        emails = []
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                data = [data]

            for email_data in data:
                email = FollowUpEmail(
                    call_id=request.call_id,
                    prospect_id=uuid4(),
                    recipient=EmailRecipient(
                        email=request.prospect_context.email,
                        name=request.prospect_context.name,
                        role=request.prospect_context.title,
                        company=request.prospect_context.company,
                    ),
                    draft=EmailDraft(
                        subject=email_data.get("subject", "Follow-up from our call"),
                        body_html=email_data.get("body_html", ""),
                        body_text=email_data.get("body_text", ""),
                    ),
                    approval_mode=request.approval_mode,
                    priority=request.urgency_level,
                )
                emails.append(email)
        except json.JSONDecodeError:
            logger.error("Failed to parse email response from Claude")
            emails = [self._generate_default_email(request)]

        return emails

    async def _generate_tasks(
        self,
        request: FollowUpGenerationRequest,
    ) -> list[FollowUpTask]:
        """Generate follow-up tasks based on SPICED analysis."""
        tasks = []
        spiced = request.spiced_context
        prospect = request.prospect_context

        # Task from action items
        for i, action_item in enumerate(spiced.action_items):
            task = FollowUpTask(
                call_id=request.call_id,
                prospect_id=uuid4(),
                title=action_item,
                description=f"Action item from call with {prospect.name} at {prospect.company}",
                category=self._categorize_action_item(action_item),
                priority=request.urgency_level,
                due_at=datetime.utcnow() + timedelta(days=3 + i),  # Stagger due dates
                approval_mode=request.approval_mode,
            )
            tasks.append(task)

        # Task for critical event follow-up
        if spiced.critical_event:
            task = FollowUpTask(
                call_id=request.call_id,
                prospect_id=uuid4(),
                title=f"Follow up on: {spiced.critical_event[:50]}",
                description=(
                    f"Critical event mentioned by {prospect.name}: {spiced.critical_event}. "
                    "Ensure timely follow-up to address their timeline."
                ),
                category=TaskCategory.CALL,
                priority=Priority.HIGH,
                due_at=datetime.utcnow() + timedelta(days=1),
                approval_mode=request.approval_mode,
            )
            tasks.append(task)

        # Task for objection handling
        for objection in spiced.objections_raised:
            task = FollowUpTask(
                call_id=request.call_id,
                prospect_id=uuid4(),
                title=f"Address objection: {objection[:40]}...",
                description=(
                    f"Objection raised by {prospect.name}: {objection}. "
                    "Prepare materials or responses to address this concern."
                ),
                category=TaskCategory.RESEARCH,
                priority=Priority.MEDIUM,
                due_at=datetime.utcnow() + timedelta(days=2),
                approval_mode=request.approval_mode,
            )
            tasks.append(task)

        # Default follow-up task if no specific items
        if not tasks:
            task = FollowUpTask(
                call_id=request.call_id,
                prospect_id=uuid4(),
                title=f"Follow up with {prospect.name} at {prospect.company}",
                description="Schedule next touchpoint to continue the conversation.",
                category=TaskCategory.CALL,
                priority=request.urgency_level,
                due_at=datetime.utcnow() + timedelta(days=7),
                approval_mode=request.approval_mode,
            )
            tasks.append(task)

        return tasks

    def _categorize_action_item(self, action_item: str) -> TaskCategory:
        """Categorize an action item based on keywords."""
        action_lower = action_item.lower()

        if any(w in action_lower for w in ["call", "phone", "speak"]):
            return TaskCategory.CALL
        elif any(w in action_lower for w in ["email", "send", "share"]):
            return TaskCategory.EMAIL
        elif any(w in action_lower for w in ["meeting", "schedule", "book"]):
            return TaskCategory.MEETING
        elif any(w in action_lower for w in ["research", "look into", "investigate"]):
            return TaskCategory.RESEARCH
        elif any(w in action_lower for w in ["proposal", "quote", "pricing"]):
            return TaskCategory.PROPOSAL
        elif any(w in action_lower for w in ["demo", "showcase", "present"]):
            return TaskCategory.DEMO
        else:
            return TaskCategory.OTHER

    async def _generate_content_recommendations(
        self,
        request: FollowUpGenerationRequest,
    ) -> list[FollowUpContentRecommendation]:
        """Generate content recommendations based on SPICED analysis."""
        recommendations = []
        spiced = request.spiced_context
        prospect = request.prospect_context

        content_items = []

        # Recommend case study if pain point mentioned
        if spiced.pain:
            content_items.append(
                ContentRecommendation(
                    content_type=ContentType.CASE_STUDY,
                    title=f"Case Study: Similar challenges in {prospect.industry or 'your industry'}",
                    description=(
                        f"Share a case study showing how we helped a similar company "
                        f"overcome '{spiced.pain[:50]}...'"
                    ),
                    relevance_score=0.9,
                    reasoning=(
                        f"The prospect mentioned pain around '{spiced.pain[:30]}...'. "
                        "A relevant case study can demonstrate proven success with similar challenges."
                    ),
                    spiced_elements_addressed=["pain", "impact"],
                )
            )

        # Recommend ROI calculator if impact is quantifiable
        if spiced.impact and any(c.isdigit() for c in spiced.impact):
            content_items.append(
                ContentRecommendation(
                    content_type=ContentType.ROI_CALCULATOR,
                    title="ROI Calculator",
                    description="Help quantify the potential return on investment",
                    relevance_score=0.85,
                    reasoning=(
                        f"The prospect mentioned quantifiable impact: '{spiced.impact[:30]}...'. "
                        "An ROI calculator can help build the business case."
                    ),
                    spiced_elements_addressed=["impact", "decision_criteria"],
                )
            )

        # Recommend proposal if decision criteria discussed
        if spiced.decision_criteria:
            content_items.append(
                ContentRecommendation(
                    content_type=ContentType.PROPOSAL,
                    title=f"Custom Proposal for {prospect.company}",
                    description="Tailored proposal addressing their specific decision criteria",
                    relevance_score=0.8,
                    reasoning=(
                        f"Decision criteria were discussed: '{spiced.decision_criteria[:30]}...'. "
                        "A tailored proposal can address these directly."
                    ),
                    spiced_elements_addressed=["decision_criteria", "expected_decision"],
                )
            )

        # Recommend one-pager if early in sales cycle
        if spiced.situation and prospect.previous_calls <= 1:
            content_items.append(
                ContentRecommendation(
                    content_type=ContentType.ONE_PAGER,
                    title=f"Solution Overview for {prospect.company}",
                    description="Concise one-pager highlighting key capabilities",
                    relevance_score=0.75,
                    reasoning=(
                        "Early-stage conversation - a one-pager can provide "
                        "a clear overview for internal sharing."
                    ),
                    spiced_elements_addressed=["situation"],
                )
            )

        # Recommend battlecard if objections raised
        if spiced.objections_raised:
            content_items.append(
                ContentRecommendation(
                    content_type=ContentType.BATTLECARD,
                    title="Competitive Battlecard",
                    description="Materials to address competitive objections",
                    relevance_score=0.7,
                    reasoning=(
                        f"Objections were raised during the call. "
                        "A battlecard can help address competitive concerns."
                    ),
                    spiced_elements_addressed=["pain"],
                )
            )

        if content_items:
            # Sort by relevance score
            content_items.sort(key=lambda x: x.relevance_score, reverse=True)

            recommendation = FollowUpContentRecommendation(
                call_id=request.call_id,
                prospect_id=uuid4(),
                recommendations=content_items,
                primary_recommendation=content_items[0] if content_items else None,
                approval_mode=request.approval_mode,
                priority=request.urgency_level,
            )
            recommendations.append(recommendation)

        return recommendations

    async def _generate_meeting_suggestions(
        self,
        request: FollowUpGenerationRequest,
    ) -> list[FollowUpMeetingSuggestion]:
        """Generate meeting suggestions based on SPICED analysis."""
        suggestions = []
        spiced = request.spiced_context
        prospect = request.prospect_context

        # Determine appropriate meeting type based on SPICED
        meeting_type = self._determine_meeting_type(spiced, prospect)

        # Build agenda based on SPICED elements
        agenda = self._build_meeting_agenda(spiced, meeting_type)

        # Suggest meeting times (next 2 business days)
        suggested_dates = self._get_suggested_meeting_times()

        suggestion = MeetingSuggestion(
            meeting_type=meeting_type,
            title=self._get_meeting_title(meeting_type, prospect),
            description=self._get_meeting_description(meeting_type, spiced),
            suggested_duration_minutes=self._get_meeting_duration(meeting_type),
            suggested_attendees=[prospect.name, request.sender_name],
            suggested_dates=suggested_dates,
            agenda=agenda,
            reasoning=self._get_meeting_reasoning(meeting_type, spiced),
            spiced_focus_areas=self._get_focus_areas(spiced),
        )

        follow_up_meeting = FollowUpMeetingSuggestion(
            call_id=request.call_id,
            prospect_id=uuid4(),
            suggestion=suggestion,
            approval_mode=request.approval_mode,
            priority=request.urgency_level,
        )
        suggestions.append(follow_up_meeting)

        return suggestions

    def _determine_meeting_type(
        self,
        spiced: SPICEDContext,
        prospect: ProspectContext,
    ) -> MeetingType:
        """Determine the appropriate next meeting type."""
        # Technical questions suggest technical deep dive
        if spiced.decision_criteria and any(
            w in spiced.decision_criteria.lower()
            for w in ["technical", "integration", "security", "architecture"]
        ):
            return MeetingType.TECHNICAL_DEEP_DIVE

        # Pricing/contract discussions suggest proposal review
        if spiced.decision_criteria and any(
            w in spiced.decision_criteria.lower()
            for w in ["price", "cost", "budget", "contract", "terms"]
        ):
            return MeetingType.PROPOSAL_REVIEW

        # Executive mentioned suggests executive briefing
        if spiced.expected_decision and any(
            w in spiced.expected_decision.lower()
            for w in ["executive", "ceo", "cfo", "board", "leadership"]
        ):
            return MeetingType.EXECUTIVE_BRIEFING

        # Early stage with limited SPICED data
        if not spiced.pain and not spiced.impact:
            return MeetingType.DISCOVERY

        # Default to demo for mid-funnel
        return MeetingType.DEMO

    def _build_meeting_agenda(
        self,
        spiced: SPICEDContext,
        meeting_type: MeetingType,
    ) -> list[str]:
        """Build meeting agenda based on SPICED context."""
        agenda = []

        if meeting_type == MeetingType.DISCOVERY:
            agenda = [
                "Brief introductions and recap",
                "Explore current situation and challenges",
                "Understand business impact and goals",
                "Discuss timeline and decision process",
                "Identify next steps",
            ]
        elif meeting_type == MeetingType.DEMO:
            agenda = [
                "Quick recap of key requirements",
                "Live product demonstration",
                "Q&A and discussion",
                "Address any concerns",
                "Outline next steps",
            ]
            # Add specific SPICED elements to address
            if spiced.pain:
                agenda.insert(2, f"Demo: Addressing '{spiced.pain[:30]}...'")
        elif meeting_type == MeetingType.TECHNICAL_DEEP_DIVE:
            agenda = [
                "Technical requirements review",
                "Architecture and integration discussion",
                "Security and compliance review",
                "Implementation planning",
                "Technical Q&A",
            ]
        elif meeting_type == MeetingType.PROPOSAL_REVIEW:
            agenda = [
                "Proposal walkthrough",
                "Pricing and terms discussion",
                "ROI and business case review",
                "Address questions and concerns",
                "Discuss approval process and timeline",
            ]
        elif meeting_type == MeetingType.EXECUTIVE_BRIEFING:
            agenda = [
                "Executive summary",
                "Strategic alignment discussion",
                "Business impact and ROI",
                "Partnership overview",
                "Decision and next steps",
            ]
        else:
            agenda = [
                "Meeting objective and agenda review",
                "Discussion topics",
                "Q&A",
                "Next steps",
            ]

        return agenda

    def _get_meeting_title(
        self,
        meeting_type: MeetingType,
        prospect: ProspectContext,
    ) -> str:
        """Get meeting title based on type."""
        titles = {
            MeetingType.DISCOVERY: f"Discovery Call - {prospect.company}",
            MeetingType.DEMO: f"Product Demo - {prospect.company}",
            MeetingType.TECHNICAL_DEEP_DIVE: f"Technical Deep Dive - {prospect.company}",
            MeetingType.PROPOSAL_REVIEW: f"Proposal Review - {prospect.company}",
            MeetingType.NEGOTIATION: f"Contract Discussion - {prospect.company}",
            MeetingType.EXECUTIVE_BRIEFING: f"Executive Briefing - {prospect.company}",
            MeetingType.CHECK_IN: f"Check-in Call - {prospect.company}",
            MeetingType.ONBOARDING: f"Onboarding Kickoff - {prospect.company}",
        }
        return titles.get(meeting_type, f"Follow-up Meeting - {prospect.company}")

    def _get_meeting_description(
        self,
        meeting_type: MeetingType,
        spiced: SPICEDContext,
    ) -> str:
        """Get meeting description based on type and SPICED context."""
        descriptions = {
            MeetingType.DISCOVERY: (
                "Continue exploring requirements and understanding your needs "
                "to ensure we can provide the best solution."
            ),
            MeetingType.DEMO: (
                "Walkthrough of our solution focusing on your specific "
                "use cases and requirements."
            ),
            MeetingType.TECHNICAL_DEEP_DIVE: (
                "Detailed technical discussion covering architecture, "
                "integrations, and implementation approach."
            ),
            MeetingType.PROPOSAL_REVIEW: (
                "Review of our tailored proposal including pricing, "
                "terms, and implementation timeline."
            ),
            MeetingType.EXECUTIVE_BRIEFING: (
                "Strategic overview and discussion with leadership "
                "about the partnership opportunity."
            ),
        }
        return descriptions.get(meeting_type, "Follow-up meeting to continue our discussion.")

    def _get_meeting_duration(self, meeting_type: MeetingType) -> int:
        """Get suggested meeting duration in minutes."""
        durations = {
            MeetingType.DISCOVERY: 45,
            MeetingType.DEMO: 60,
            MeetingType.TECHNICAL_DEEP_DIVE: 90,
            MeetingType.PROPOSAL_REVIEW: 45,
            MeetingType.NEGOTIATION: 60,
            MeetingType.EXECUTIVE_BRIEFING: 30,
            MeetingType.CHECK_IN: 30,
            MeetingType.ONBOARDING: 60,
        }
        return durations.get(meeting_type, 30)

    def _get_meeting_reasoning(
        self,
        meeting_type: MeetingType,
        spiced: SPICEDContext,
    ) -> str:
        """Get reasoning for meeting suggestion."""
        if meeting_type == MeetingType.TECHNICAL_DEEP_DIVE:
            return (
                "Technical criteria were mentioned in the decision process. "
                "A technical deep dive will address these concerns directly."
            )
        elif meeting_type == MeetingType.PROPOSAL_REVIEW:
            return (
                "Pricing and contract terms were discussed. "
                "A proposal review will help move the deal forward."
            )
        elif meeting_type == MeetingType.EXECUTIVE_BRIEFING:
            return (
                "Executive involvement in the decision was mentioned. "
                "An executive briefing will help build alignment."
            )
        elif meeting_type == MeetingType.DISCOVERY:
            return (
                "More discovery is needed to fully understand requirements. "
                "A follow-up discovery call will help qualify the opportunity."
            )
        else:
            return (
                "Based on the SPICED analysis, a product demo will help "
                "demonstrate value and address key pain points."
            )

    def _get_focus_areas(self, spiced: SPICEDContext) -> list[str]:
        """Get SPICED elements to focus on in the meeting."""
        focus_areas = []
        if spiced.pain:
            focus_areas.append("pain")
        if spiced.impact:
            focus_areas.append("impact")
        if spiced.critical_event:
            focus_areas.append("critical_event")
        if spiced.decision_criteria:
            focus_areas.append("decision_criteria")
        return focus_areas or ["situation"]

    def _get_suggested_meeting_times(self) -> list[datetime]:
        """Get suggested meeting times for the next few business days."""
        times = []
        current = datetime.utcnow()

        for day_offset in range(1, 6):
            potential_date = current + timedelta(days=day_offset)
            # Skip weekends
            if potential_date.weekday() < 5:
                # Suggest 10am and 2pm slots
                times.append(potential_date.replace(hour=10, minute=0, second=0, microsecond=0))
                times.append(potential_date.replace(hour=14, minute=0, second=0, microsecond=0))
                if len(times) >= 4:
                    break

        return times

    def _get_default_prompt(self) -> str:
        """Get default prompt if template file is not found."""
        return """You are a sales follow-up assistant. Generate personalized follow-up content
based on SPICED analysis from sales calls. Focus on being helpful, professional,
and addressing the prospect's specific needs and pain points."""
