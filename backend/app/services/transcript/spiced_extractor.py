"""SPICED methodology extractor using Claude AI.

Extracts structured SPICED information from sales call transcripts.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.models.spiced import (
    ConfidenceLevel,
    CriticalEvent,
    DecisionCriteria,
    ExpectedDecision,
    Impact,
    Pain,
    Situation,
    SPICEDAnalysis,
    SPICEDConfidence,
)
from app.models.transcript import (
    CallNote,
    FollowUpTask,
    TaskPriority,
    Transcript,
)
from app.services.claude_client import ClaudeClient, get_claude_client

logger = logging.getLogger(__name__)


class SPICEDExtractor:
    """Extracts SPICED methodology components from transcripts.

    Uses Claude AI to analyze sales call transcripts and extract
    structured information according to the SPICED framework.
    """

    SYSTEM_PROMPT = """You are an expert sales analyst specializing in the SPICED
qualification methodology. You analyze sales call transcripts to extract structured
information that helps sales teams understand prospects and opportunities better.

Your analysis should be:
- Accurate: Only include information actually present in the transcript
- Specific: Include concrete details and direct quotes
- Balanced: Acknowledge gaps and uncertainty appropriately
- Actionable: Provide insights that help sales teams take next steps"""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize the SPICED extractor.

        Args:
            claude_client: Claude client instance. Uses default if not provided.
        """
        self.client = claude_client or get_claude_client()
        self._prompt_template: Optional[str] = None

    @property
    def prompt_template(self) -> str:
        """Load and cache the SPICED extraction prompt template."""
        if self._prompt_template is None:
            self._prompt_template = self.client.load_prompt("spiced_extraction")
        return self._prompt_template

    async def extract(
        self,
        transcript: Transcript,
        company_name: Optional[str] = None,
    ) -> SPICEDAnalysis:
        """Extract SPICED analysis from a transcript.

        Args:
            transcript: Parsed transcript to analyze
            company_name: Optional company name for context

        Returns:
            SPICEDAnalysis with extracted information
        """
        # Build context for the analysis
        context_parts = []

        if company_name:
            context_parts.append(f"Company: {company_name}")

        if transcript.title:
            context_parts.append(f"Call Title: {transcript.title}")

        if transcript.call_date:
            context_parts.append(f"Call Date: {transcript.call_date.isoformat()}")

        if transcript.speakers:
            speakers_info = ", ".join(
                f"{s.name} ({s.role or 'unknown role'})" for s in transcript.speakers
            )
            context_parts.append(f"Participants: {speakers_info}")

        context = "\n".join(context_parts) if context_parts else ""

        # Prepare transcript content
        if transcript.turns:
            # Use structured turns
            content_lines = []
            for turn in transcript.turns:
                timestamp_prefix = f"[{turn.timestamp}] " if turn.timestamp else ""
                content_lines.append(f"{timestamp_prefix}{turn.speaker}: {turn.text}")
            transcript_content = "\n\n".join(content_lines)
        else:
            # Use raw text
            transcript_content = transcript.raw_text

        full_content = f"{context}\n\n---\n\nTRANSCRIPT:\n\n{transcript_content}"

        # Get analysis from Claude
        response_data = await self.client.extract_json(
            prompt=self.prompt_template,
            content=full_content,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=4096,
        )

        # Build SPICEDAnalysis from response
        return self._build_analysis(response_data, transcript.id)

    def _build_analysis(
        self,
        data: dict,
        transcript_id: Optional[str],
    ) -> SPICEDAnalysis:
        """Build a SPICEDAnalysis from extracted data.

        Args:
            data: Raw extracted data from Claude
            transcript_id: ID of the source transcript

        Returns:
            SPICEDAnalysis object
        """
        # Helper to safely get confidence level
        def get_confidence(value: str) -> ConfidenceLevel:
            try:
                return ConfidenceLevel(value.lower())
            except (ValueError, AttributeError):
                return ConfidenceLevel.MEDIUM

        # Build each component
        situation_data = data.get("situation", {})
        situation = Situation(
            summary=situation_data.get("summary", "No situation information found"),
            current_tools=situation_data.get("current_tools", []),
            team_size=situation_data.get("team_size"),
            industry_context=situation_data.get("industry_context"),
            key_quotes=situation_data.get("key_quotes", []),
            confidence=get_confidence(situation_data.get("confidence", "medium")),
        )

        pain_data = data.get("pain", {})
        pain = Pain(
            primary_pain=pain_data.get("primary_pain", "No pain information found"),
            secondary_pains=pain_data.get("secondary_pains", []),
            symptoms=pain_data.get("symptoms", []),
            root_causes=pain_data.get("root_causes", []),
            key_quotes=pain_data.get("key_quotes", []),
            confidence=get_confidence(pain_data.get("confidence", "medium")),
        )

        impact_data = data.get("impact", {})
        impact = Impact(
            business_impact=impact_data.get(
                "business_impact", "No impact information found"
            ),
            quantified_impact=impact_data.get("quantified_impact"),
            affected_areas=impact_data.get("affected_areas", []),
            stakeholders_affected=impact_data.get("stakeholders_affected", []),
            opportunity_cost=impact_data.get("opportunity_cost"),
            key_quotes=impact_data.get("key_quotes", []),
            confidence=get_confidence(impact_data.get("confidence", "medium")),
        )

        critical_event_data = data.get("critical_event", {})
        critical_event = CriticalEvent(
            summary=critical_event_data.get(
                "summary", "No critical event information found"
            ),
            deadline=critical_event_data.get("deadline"),
            trigger_events=critical_event_data.get("trigger_events", []),
            consequences_of_delay=critical_event_data.get("consequences_of_delay"),
            urgency_level=critical_event_data.get("urgency_level"),
            key_quotes=critical_event_data.get("key_quotes", []),
            confidence=get_confidence(critical_event_data.get("confidence", "medium")),
        )

        expected_decision_data = data.get("expected_decision", {})
        expected_decision = ExpectedDecision(
            summary=expected_decision_data.get(
                "summary", "No decision process information found"
            ),
            decision_maker=expected_decision_data.get("decision_maker"),
            stakeholders=expected_decision_data.get("stakeholders", []),
            decision_timeline=expected_decision_data.get("decision_timeline"),
            approval_process=expected_decision_data.get("approval_process"),
            budget_authority=expected_decision_data.get("budget_authority"),
            key_quotes=expected_decision_data.get("key_quotes", []),
            confidence=get_confidence(
                expected_decision_data.get("confidence", "medium")
            ),
        )

        decision_criteria_data = data.get("decision_criteria", {})
        decision_criteria = DecisionCriteria(
            summary=decision_criteria_data.get(
                "summary", "No decision criteria information found"
            ),
            must_haves=decision_criteria_data.get("must_haves", []),
            nice_to_haves=decision_criteria_data.get("nice_to_haves", []),
            deal_breakers=decision_criteria_data.get("deal_breakers", []),
            evaluation_criteria=decision_criteria_data.get("evaluation_criteria", []),
            competitors_considered=decision_criteria_data.get(
                "competitors_considered", []
            ),
            key_quotes=decision_criteria_data.get("key_quotes", []),
            confidence=get_confidence(
                decision_criteria_data.get("confidence", "medium")
            ),
        )

        # Build confidence scores
        confidence_data = data.get("confidence", {})
        confidence = SPICEDConfidence(
            overall=get_confidence(confidence_data.get("overall", "medium")),
            situation=situation.confidence,
            pain=pain.confidence,
            impact=impact.confidence,
            critical_event=critical_event.confidence,
            expected_decision=expected_decision.confidence,
            decision_criteria=decision_criteria.confidence,
            completeness_score=float(confidence_data.get("completeness_score", 0.5)),
        )

        return SPICEDAnalysis(
            id=str(uuid.uuid4()),
            transcript_id=transcript_id,
            situation=situation,
            pain=pain,
            impact=impact,
            critical_event=critical_event,
            expected_decision=expected_decision,
            decision_criteria=decision_criteria,
            confidence=confidence,
            gaps_identified=data.get("gaps_identified", []),
            coaching_notes=data.get("coaching_notes", []),
            created_at=datetime.utcnow(),
        )

    async def generate_call_note(
        self,
        transcript: Transcript,
        spiced: SPICEDAnalysis,
    ) -> CallNote:
        """Generate formatted call notes from transcript and SPICED analysis.

        Args:
            transcript: The parsed transcript
            spiced: The SPICED analysis

        Returns:
            CallNote with formatted summary and details
        """
        # Build attendees list
        attendees = [s.name for s in transcript.speakers] if transcript.speakers else []

        # Build key discussion points from SPICED
        discussion_points = []
        if spiced.situation.confidence != ConfidenceLevel.NOT_FOUND:
            discussion_points.append(f"Current Situation: {spiced.situation.summary}")
        if spiced.pain.confidence != ConfidenceLevel.NOT_FOUND:
            discussion_points.append(f"Key Challenges: {spiced.pain.primary_pain}")
        if spiced.impact.confidence != ConfidenceLevel.NOT_FOUND:
            discussion_points.append(f"Business Impact: {spiced.impact.business_impact}")
        if spiced.critical_event.confidence != ConfidenceLevel.NOT_FOUND:
            discussion_points.append(f"Timeline: {spiced.critical_event.summary}")

        # Determine sentiment based on urgency and pain
        sentiment = "Neutral"
        if spiced.critical_event.urgency_level == "high":
            sentiment = "Engaged - High Urgency"
        elif spiced.pain.confidence == ConfidenceLevel.HIGH:
            sentiment = "Interested - Clear Pain Points"
        elif spiced.confidence.completeness_score < 0.3:
            sentiment = "Early Stage - Limited Information"

        # Build formatted note
        formatted_parts = [
            f"## Call Summary",
            f"",
            f"**Date:** {transcript.call_date.strftime('%Y-%m-%d') if transcript.call_date else 'Not recorded'}",
            f"**Attendees:** {', '.join(attendees) if attendees else 'Unknown'}",
            f"**Duration:** {transcript.duration_minutes or 'Unknown'} minutes",
            f"",
            f"### Situation",
            spiced.situation.summary,
            f"",
            f"### Pain Points",
            f"- **Primary:** {spiced.pain.primary_pain}",
        ]

        for secondary in spiced.pain.secondary_pains[:3]:
            formatted_parts.append(f"- {secondary}")

        formatted_parts.extend([
            f"",
            f"### Impact",
            spiced.impact.business_impact,
        ])

        if spiced.impact.quantified_impact:
            formatted_parts.append(f"- **Quantified:** {spiced.impact.quantified_impact}")

        formatted_parts.extend([
            f"",
            f"### Timeline & Urgency",
            spiced.critical_event.summary,
        ])

        if spiced.critical_event.deadline:
            formatted_parts.append(f"- **Deadline:** {spiced.critical_event.deadline}")

        formatted_parts.extend([
            f"",
            f"### Decision Process",
            spiced.expected_decision.summary,
        ])

        if spiced.expected_decision.decision_maker:
            formatted_parts.append(
                f"- **Decision Maker:** {spiced.expected_decision.decision_maker}"
            )

        formatted_parts.extend([
            f"",
            f"### Evaluation Criteria",
            spiced.decision_criteria.summary,
        ])

        if spiced.decision_criteria.must_haves:
            formatted_parts.append(f"- **Must-haves:** {', '.join(spiced.decision_criteria.must_haves[:3])}")

        if spiced.gaps_identified:
            formatted_parts.extend([
                f"",
                f"### Information Gaps (Follow-up Needed)",
            ])
            for gap in spiced.gaps_identified[:5]:
                formatted_parts.append(f"- {gap}")

        formatted_note = "\n".join(formatted_parts)

        # Build summary
        summary_parts = []
        if spiced.situation.summary:
            summary_parts.append(spiced.situation.summary)
        if spiced.pain.primary_pain:
            summary_parts.append(f"Key pain: {spiced.pain.primary_pain}")
        if spiced.critical_event.deadline:
            summary_parts.append(f"Timeline: {spiced.critical_event.deadline}")

        summary = " ".join(summary_parts) if summary_parts else "Call summary not available"

        return CallNote(
            summary=summary,
            attendees=attendees,
            key_discussion_points=discussion_points,
            customer_sentiment=sentiment,
            next_steps_discussed=[],  # Would need to extract from transcript
            objections_raised=[],  # Would need additional analysis
            questions_asked=[],  # Would need additional analysis
            commitments_made=[],  # Would need additional analysis
            formatted_note=formatted_note,
        )

    async def generate_follow_up_tasks(
        self,
        spiced: SPICEDAnalysis,
        company_name: Optional[str] = None,
    ) -> list[FollowUpTask]:
        """Generate follow-up task recommendations from SPICED analysis.

        Args:
            spiced: The SPICED analysis
            company_name: Optional company name for task titles

        Returns:
            List of recommended follow-up tasks
        """
        tasks: list[FollowUpTask] = []
        company_prefix = f"{company_name}: " if company_name else ""

        # Generate tasks based on gaps
        for gap in spiced.gaps_identified:
            tasks.append(
                FollowUpTask(
                    title=f"{company_prefix}Follow up on: {gap[:50]}",
                    description=f"Information gap identified during discovery call: {gap}",
                    priority=TaskPriority.MEDIUM,
                    due_date_suggestion="Within 3 business days",
                    related_spiced_component="gap",
                    crm_task_type="call",
                )
            )

        # Task based on critical event/deadline
        if spiced.critical_event.deadline:
            tasks.append(
                FollowUpTask(
                    title=f"{company_prefix}Prepare proposal before {spiced.critical_event.deadline}",
                    description=(
                        f"Critical deadline identified: {spiced.critical_event.summary}. "
                        f"Ensure proposal and next steps are completed before deadline."
                    ),
                    priority=TaskPriority.HIGH,
                    due_date_suggestion=f"Before {spiced.critical_event.deadline}",
                    related_spiced_component="critical_event",
                    crm_task_type="task",
                )
            )

        # Task based on decision maker
        if spiced.expected_decision.decision_maker:
            if spiced.expected_decision.confidence != ConfidenceLevel.HIGH:
                tasks.append(
                    FollowUpTask(
                        title=f"{company_prefix}Confirm decision-making process",
                        description=(
                            f"Decision maker identified as {spiced.expected_decision.decision_maker}. "
                            f"Confirm approval process and other stakeholders involved."
                        ),
                        priority=TaskPriority.MEDIUM,
                        due_date_suggestion="Within 1 week",
                        related_spiced_component="expected_decision",
                        crm_task_type="call",
                    )
                )

        # Task based on competitors
        if spiced.decision_criteria.competitors_considered:
            competitors = ", ".join(spiced.decision_criteria.competitors_considered)
            tasks.append(
                FollowUpTask(
                    title=f"{company_prefix}Prepare competitive positioning",
                    description=(
                        f"Competitors mentioned: {competitors}. "
                        f"Prepare differentiation talking points and battle cards."
                    ),
                    priority=TaskPriority.MEDIUM,
                    due_date_suggestion="Before next call",
                    related_spiced_component="decision_criteria",
                    crm_task_type="task",
                )
            )

        # Task based on must-haves
        if spiced.decision_criteria.must_haves:
            requirements = ", ".join(spiced.decision_criteria.must_haves[:3])
            tasks.append(
                FollowUpTask(
                    title=f"{company_prefix}Confirm solution meets requirements",
                    description=(
                        f"Key requirements identified: {requirements}. "
                        f"Verify our solution addresses these and prepare demo/proof points."
                    ),
                    priority=TaskPriority.HIGH,
                    due_date_suggestion="Before next call",
                    related_spiced_component="decision_criteria",
                    crm_task_type="task",
                )
            )

        # Task for quantifying impact
        if (
            spiced.impact.confidence != ConfidenceLevel.HIGH
            and not spiced.impact.quantified_impact
        ):
            tasks.append(
                FollowUpTask(
                    title=f"{company_prefix}Quantify business impact",
                    description=(
                        f"Business impact not fully quantified. Work with prospect to "
                        f"develop ROI analysis and business case."
                    ),
                    priority=TaskPriority.MEDIUM,
                    due_date_suggestion="Within 1 week",
                    related_spiced_component="impact",
                    crm_task_type="call",
                )
            )

        # Always add a general follow-up task
        tasks.append(
            FollowUpTask(
                title=f"{company_prefix}Send follow-up email with next steps",
                description="Send recap email summarizing the call and confirming next steps.",
                priority=TaskPriority.HIGH,
                due_date_suggestion="Same day",
                related_spiced_component=None,
                crm_task_type="email",
            )
        )

        # Sort by priority
        priority_order = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 2))

        return tasks
