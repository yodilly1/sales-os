"""
Brief Generator

Uses Claude AI to generate comprehensive meeting prep briefs by synthesizing
data from enrichment, call history, and SPICED analysis.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from app.models.meetingprep import (
    Meeting,
    MeetingType,
    AttendeeProfileSchema,
    CompanyResearchSchema,
    CallHistoryItemSchema,
    SPICEDContextSchema,
    AgendaItemSchema,
    QuestionSchema,
    ContentRecommendationSchema,
)

logger = logging.getLogger(__name__)


class BriefGenerator:
    """
    Generates meeting prep briefs using Claude AI.

    Aggregates data from:
    - Enrichment service (attendee profiles, company data)
    - Transcript service (previous calls, SPICED context)
    - Content service (relevant content recommendations)
    """

    def __init__(
        self,
        claude_client: Any,  # ClaudeClient from app.services.claude_client
        enrichment_service: Any,  # EnrichmentService
        transcript_service: Any,  # TranscriptService
        content_service: Any,  # ContentService
        prompt_path: str = "claude/prompts/meeting_prep.md",
    ):
        self.claude = claude_client
        self.enrichment = enrichment_service
        self.transcript = transcript_service
        self.content = content_service
        self.prompt_path = prompt_path
        self._prompt_template: Optional[str] = None

    @property
    def prompt_template(self) -> str:
        """Lazy load prompt template."""
        if self._prompt_template is None:
            try:
                with open(self.prompt_path, "r") as f:
                    self._prompt_template = f.read()
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {self.prompt_path}")
                self._prompt_template = self._default_prompt()
        return self._prompt_template

    async def generate(
        self,
        meeting: Meeting,
        user_id: UUID,
        include_sections: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate a complete meeting prep brief.

        Args:
            meeting: The meeting to generate prep for
            user_id: The user requesting the prep
            include_sections: Optional list of sections to include.
                If None, includes all sections.

        Returns:
            Dictionary containing all brief sections
        """
        logger.info(f"Generating prep brief for meeting {meeting.id}")

        sections = include_sections or [
            "attendee_profiles",
            "company_research",
            "call_history",
            "spiced_context",
            "suggested_agenda",
            "suggested_questions",
            "content_recommendations",
            "executive_summary",
        ]

        brief_data = {}

        # Gather data from services
        if "attendee_profiles" in sections:
            brief_data["attendee_profiles"] = await self._get_attendee_profiles(
                meeting
            )

        if "company_research" in sections:
            brief_data["company_research"] = await self._get_company_research(
                meeting
            )

        if "call_history" in sections:
            brief_data["call_history"] = await self._get_call_history(
                meeting, user_id
            )

        if "spiced_context" in sections:
            brief_data["spiced_context"] = await self._get_spiced_context(
                meeting, user_id
            )

        # Generate AI-powered sections
        ai_sections = await self._generate_ai_sections(
            meeting=meeting,
            gathered_data=brief_data,
            sections=sections,
        )

        brief_data.update(ai_sections)

        return brief_data

    async def _get_attendee_profiles(
        self,
        meeting: Meeting,
    ) -> list[dict]:
        """Fetch enriched profiles for all attendees."""
        profiles = []

        for attendee in meeting.attendees:
            try:
                # Get enrichment data
                enrichment_data = await self.enrichment.get_contact_enrichment(
                    email=attendee.email,
                    name=attendee.name,
                )

                profile = AttendeeProfileSchema(
                    email=attendee.email,
                    name=enrichment_data.get("name", attendee.name),
                    title=enrichment_data.get("title", attendee.title),
                    company=enrichment_data.get("company"),
                    linkedin_url=enrichment_data.get("linkedin_url", attendee.linkedin_url),
                    role=attendee.role,
                    background=enrichment_data.get("background"),
                    career_highlights=enrichment_data.get("career_highlights"),
                    mutual_connections=enrichment_data.get("mutual_connections"),
                    recent_activity=enrichment_data.get("recent_activity"),
                    communication_style=enrichment_data.get("communication_style"),
                    talking_points=enrichment_data.get("talking_points"),
                )
                profiles.append(profile.model_dump())

            except Exception as e:
                logger.warning(f"Failed to enrich attendee {attendee.email}: {e}")
                # Include basic profile even if enrichment fails
                profiles.append(
                    AttendeeProfileSchema(
                        email=attendee.email,
                        name=attendee.name,
                        title=attendee.title,
                    ).model_dump()
                )

        return profiles

    async def _get_company_research(
        self,
        meeting: Meeting,
    ) -> Optional[dict]:
        """Fetch company research for the meeting."""
        # Try to determine company from meeting or attendees
        company_id = meeting.company_id
        company_name = None

        if not company_id and meeting.attendees:
            # Extract company from first external attendee's email domain
            for attendee in meeting.attendees:
                if not attendee.is_organizer:
                    domain = attendee.email.split("@")[-1]
                    if domain not in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]:
                        company_name = domain.split(".")[0].capitalize()
                        break

        if not company_id and not company_name:
            return None

        try:
            if company_id:
                company_data = await self.enrichment.get_company_by_id(company_id)
            else:
                company_data = await self.enrichment.get_company_enrichment(
                    company_name=company_name
                )

            if company_data:
                return CompanyResearchSchema(
                    name=company_data.get("name", company_name),
                    website=company_data.get("website"),
                    industry=company_data.get("industry"),
                    size=company_data.get("size"),
                    headquarters=company_data.get("headquarters"),
                    description=company_data.get("description"),
                    recent_news=company_data.get("recent_news"),
                    key_initiatives=company_data.get("key_initiatives"),
                    competitors=company_data.get("competitors"),
                    tech_stack=company_data.get("tech_stack"),
                    funding_stage=company_data.get("funding_stage"),
                    annual_revenue=company_data.get("annual_revenue"),
                    existing_customer=company_data.get("existing_customer", False),
                    current_products=company_data.get("current_products"),
                ).model_dump()

        except Exception as e:
            logger.warning(f"Failed to get company research: {e}")

        return None

    async def _get_call_history(
        self,
        meeting: Meeting,
        user_id: UUID,
    ) -> list[dict]:
        """Fetch previous call history with attendees."""
        call_history = []

        # Get attendee emails for lookup
        attendee_emails = [a.email for a in meeting.attendees if not a.is_organizer]

        if not attendee_emails:
            return call_history

        try:
            # Query transcript service for previous calls
            previous_calls = await self.transcript.get_calls_by_participants(
                user_id=user_id,
                participant_emails=attendee_emails,
                limit=5,
            )

            for call in previous_calls:
                call_history.append(
                    CallHistoryItemSchema(
                        date=call.get("date"),
                        call_type=call.get("call_type", "unknown"),
                        attendees=call.get("attendees", []),
                        summary=call.get("summary", ""),
                        key_outcomes=call.get("key_outcomes"),
                        action_items=call.get("action_items"),
                        transcript_id=call.get("transcript_id"),
                    ).model_dump()
                )

        except Exception as e:
            logger.warning(f"Failed to get call history: {e}")

        return call_history

    async def _get_spiced_context(
        self,
        meeting: Meeting,
        user_id: UUID,
    ) -> Optional[dict]:
        """Get aggregated SPICED context from previous interactions."""
        attendee_emails = [a.email for a in meeting.attendees if not a.is_organizer]

        if not attendee_emails:
            return None

        try:
            # Get SPICED analysis from transcript service
            spiced_data = await self.transcript.get_aggregated_spiced(
                user_id=user_id,
                participant_emails=attendee_emails,
            )

            if spiced_data:
                return SPICEDContextSchema(
                    situation=spiced_data.get("situation"),
                    pain=spiced_data.get("pain"),
                    impact=spiced_data.get("impact"),
                    critical_event=spiced_data.get("critical_event"),
                    decision_process=spiced_data.get("decision_process"),
                    decision_criteria=spiced_data.get("decision_criteria"),
                    overall_score=spiced_data.get("overall_score"),
                    gaps=spiced_data.get("gaps"),
                    last_updated=spiced_data.get("last_updated"),
                ).model_dump()

        except Exception as e:
            logger.warning(f"Failed to get SPICED context: {e}")

        return None

    async def _generate_ai_sections(
        self,
        meeting: Meeting,
        gathered_data: dict,
        sections: list[str],
    ) -> dict:
        """Use Claude to generate AI-powered sections."""
        ai_sections = {}

        # Prepare context for Claude
        context = self._prepare_context(meeting, gathered_data)

        # Build prompt with meeting details and gathered data
        prompt = self._build_prompt(meeting, gathered_data, sections)

        try:
            response = await self.claude.generate(
                prompt=prompt,
                system_prompt=self.prompt_template,
                max_tokens=4000,
            )

            # Parse Claude's response
            ai_content = self._parse_ai_response(response)

            if "suggested_agenda" in sections:
                agenda_items = ai_content.get("suggested_agenda", [])
                ai_sections["suggested_agenda"] = [
                    AgendaItemSchema(**item).model_dump()
                    for item in agenda_items
                ]

            if "suggested_questions" in sections:
                questions = ai_content.get("suggested_questions", [])
                ai_sections["suggested_questions"] = [
                    QuestionSchema(**q).model_dump()
                    for q in questions
                ]

            if "content_recommendations" in sections:
                # Combine AI suggestions with actual content lookup
                ai_sections["content_recommendations"] = (
                    await self._get_content_recommendations(
                        meeting, ai_content.get("content_suggestions", [])
                    )
                )

            if "executive_summary" in sections:
                ai_sections["executive_summary"] = ai_content.get(
                    "executive_summary", ""
                )

        except Exception as e:
            logger.error(f"Failed to generate AI sections: {e}")
            # Return empty sections on failure
            if "suggested_agenda" in sections:
                ai_sections["suggested_agenda"] = self._default_agenda(meeting)
            if "suggested_questions" in sections:
                ai_sections["suggested_questions"] = self._default_questions(meeting)
            if "content_recommendations" in sections:
                ai_sections["content_recommendations"] = []
            if "executive_summary" in sections:
                ai_sections["executive_summary"] = self._generate_basic_summary(
                    meeting, gathered_data
                )

        return ai_sections

    def _prepare_context(self, meeting: Meeting, data: dict) -> str:
        """Prepare context string for Claude."""
        context_parts = [
            f"Meeting: {meeting.title}",
            f"Type: {meeting.meeting_type.value}",
            f"Scheduled: {meeting.scheduled_at.isoformat()}",
            f"Duration: {meeting.duration_minutes} minutes",
        ]

        if meeting.description:
            context_parts.append(f"Description: {meeting.description}")

        if data.get("attendee_profiles"):
            attendees = [
                f"- {p.get('name', p.get('email'))}: {p.get('title', 'Unknown role')}"
                for p in data["attendee_profiles"]
            ]
            context_parts.append("Attendees:\n" + "\n".join(attendees))

        if data.get("company_research"):
            company = data["company_research"]
            context_parts.append(
                f"Company: {company.get('name')} - {company.get('industry', 'Unknown industry')}"
            )

        if data.get("spiced_context"):
            spiced = data["spiced_context"]
            if spiced.get("pain"):
                context_parts.append(f"Known Pain Points: {', '.join(spiced['pain'])}")
            if spiced.get("critical_event"):
                context_parts.append(f"Critical Event: {spiced['critical_event']}")

        return "\n\n".join(context_parts)

    def _build_prompt(
        self,
        meeting: Meeting,
        data: dict,
        sections: list[str],
    ) -> str:
        """Build the prompt for Claude."""
        prompt_parts = [
            "Generate a meeting preparation brief with the following sections:",
        ]

        if "suggested_agenda" in sections:
            prompt_parts.append(
                "1. Suggested Agenda: Create a structured agenda with timing"
            )

        if "suggested_questions" in sections:
            prompt_parts.append(
                "2. Suggested Questions: Provide strategic questions to ask, "
                "categorized by type (discovery, pain, impact, etc.)"
            )

        if "content_recommendations" in sections:
            prompt_parts.append(
                "3. Content Suggestions: Recommend types of content to share"
            )

        if "executive_summary" in sections:
            prompt_parts.append(
                "4. Executive Summary: A brief overview of key points and strategy"
            )

        prompt_parts.append("\nContext:")
        prompt_parts.append(self._prepare_context(meeting, data))

        prompt_parts.append(
            "\nRespond in JSON format with keys: suggested_agenda, "
            "suggested_questions, content_suggestions, executive_summary"
        )

        return "\n\n".join(prompt_parts)

    def _parse_ai_response(self, response: str) -> dict:
        """Parse Claude's JSON response."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {}

    async def _get_content_recommendations(
        self,
        meeting: Meeting,
        ai_suggestions: list[dict],
    ) -> list[dict]:
        """Get actual content recommendations based on AI suggestions."""
        recommendations = []

        for suggestion in ai_suggestions[:5]:  # Limit to 5 recommendations
            content_type = suggestion.get("type", "")
            relevance = suggestion.get("relevance", "")

            try:
                # Search for matching content
                content_items = await self.content.search_content(
                    content_type=content_type,
                    industry=meeting.company_research.get("industry") if hasattr(meeting, "company_research") else None,
                    limit=1,
                )

                if content_items:
                    item = content_items[0]
                    recommendations.append(
                        ContentRecommendationSchema(
                            title=item.get("title"),
                            content_type=item.get("content_type"),
                            relevance=relevance,
                            url=item.get("url"),
                            content_id=item.get("id"),
                        ).model_dump()
                    )
                else:
                    # Include suggestion without actual content
                    recommendations.append(
                        ContentRecommendationSchema(
                            title=suggestion.get("title", f"Recommended {content_type}"),
                            content_type=content_type,
                            relevance=relevance,
                        ).model_dump()
                    )

            except Exception as e:
                logger.warning(f"Failed to get content recommendation: {e}")

        return recommendations

    def _default_agenda(self, meeting: Meeting) -> list[dict]:
        """Generate a default agenda based on meeting type."""
        duration = int(meeting.duration_minutes)
        meeting_type = meeting.meeting_type

        if meeting_type == MeetingType.DISCOVERY:
            return [
                AgendaItemSchema(
                    topic="Introduction and rapport building",
                    duration_minutes=5,
                    description="Brief introductions and set the tone",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Understand their situation",
                    duration_minutes=10,
                    description="Learn about their current state and context",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Explore pain points",
                    duration_minutes=10,
                    description="Dig into challenges and problems",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Discuss impact",
                    duration_minutes=5,
                    description="Quantify the business impact",
                    priority=2,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Next steps",
                    duration_minutes=5,
                    description="Align on follow-up actions",
                    priority=1,
                ).model_dump(),
            ]

        elif meeting_type == MeetingType.DEMO:
            return [
                AgendaItemSchema(
                    topic="Recap and objectives",
                    duration_minutes=5,
                    description="Confirm goals for the demo",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Product demonstration",
                    duration_minutes=max(duration - 15, 15),
                    description="Show relevant features",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Q&A and discussion",
                    duration_minutes=5,
                    description="Address questions and concerns",
                    priority=1,
                ).model_dump(),
                AgendaItemSchema(
                    topic="Next steps",
                    duration_minutes=5,
                    description="Define path forward",
                    priority=1,
                ).model_dump(),
            ]

        # Default generic agenda
        return [
            AgendaItemSchema(
                topic="Introduction",
                duration_minutes=5,
                priority=1,
            ).model_dump(),
            AgendaItemSchema(
                topic="Main discussion",
                duration_minutes=max(duration - 10, 10),
                priority=1,
            ).model_dump(),
            AgendaItemSchema(
                topic="Next steps",
                duration_minutes=5,
                priority=1,
            ).model_dump(),
        ]

    def _default_questions(self, meeting: Meeting) -> list[dict]:
        """Generate default questions based on meeting type."""
        meeting_type = meeting.meeting_type

        if meeting_type == MeetingType.DISCOVERY:
            return [
                QuestionSchema(
                    question="Can you walk me through how you currently handle this process?",
                    category="situation",
                    context="Understand their current state",
                ).model_dump(),
                QuestionSchema(
                    question="What's the biggest challenge you're facing with this?",
                    category="pain",
                    context="Identify primary pain point",
                ).model_dump(),
                QuestionSchema(
                    question="How does this impact your team/business on a daily basis?",
                    category="impact",
                    context="Quantify the problem",
                ).model_dump(),
                QuestionSchema(
                    question="Is there a timeline or event driving the need for a solution?",
                    category="critical_event",
                    context="Understand urgency",
                ).model_dump(),
                QuestionSchema(
                    question="Who else would be involved in evaluating a solution?",
                    category="decision",
                    context="Map the buying committee",
                ).model_dump(),
            ]

        return [
            QuestionSchema(
                question="What are your main objectives for today's meeting?",
                category="discovery",
            ).model_dump(),
            QuestionSchema(
                question="What would success look like for you?",
                category="discovery",
            ).model_dump(),
        ]

    def _generate_basic_summary(
        self,
        meeting: Meeting,
        data: dict,
    ) -> str:
        """Generate a basic summary without AI."""
        parts = [f"Preparing for {meeting.meeting_type.value} meeting: {meeting.title}"]

        if data.get("attendee_profiles"):
            attendee_count = len(data["attendee_profiles"])
            parts.append(f"Meeting with {attendee_count} attendee(s).")

        if data.get("company_research"):
            company = data["company_research"]
            parts.append(f"Company: {company.get('name')} ({company.get('industry', 'Unknown industry')})")

        if data.get("spiced_context") and data["spiced_context"].get("pain"):
            parts.append(f"Known pain points to address: {', '.join(data['spiced_context']['pain'][:3])}")

        if data.get("call_history"):
            parts.append(f"Previous interactions: {len(data['call_history'])} calls on record.")

        return " ".join(parts)

    def _default_prompt(self) -> str:
        """Default system prompt if file not found."""
        return """You are a sales meeting preparation assistant. Your role is to help sales professionals
prepare for upcoming meetings by generating actionable insights and recommendations.

When generating meeting prep briefs:
1. Focus on actionable insights, not generic advice
2. Tailor questions to the specific meeting type and context
3. Consider the SPICED methodology (Situation, Pain, Impact, Critical Event, Decision)
4. Recommend specific content that would be relevant
5. Create time-boxed agendas that respect the meeting duration

Always be professional, strategic, and focused on helping the salesperson succeed."""
