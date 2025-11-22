"""
SPICED Analyzer

Uses Claude AI to analyze sales call transcripts against the SPICED framework
and generate coaching feedback aligned with Winning by Design methodology.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from ..claude_client import ClaudeClient
from ...models.coaching import (
    CallType,
    CoachingFeedback,
    CoachingSummary,
    CoachingTip,
    ElementGap,
    ElementScore,
    GapAnalysisReport,
    ImprovementArea,
    MissedOpportunity,
    NextCallPlan,
    QuestionTransition,
    SPICEDElement,
    SPICEDScores,
    Strength,
    TalkTrack,
)

logger = logging.getLogger(__name__)


class SPICEDAnalyzer:
    """
    Analyzes sales calls against the SPICED framework using Claude AI.

    Provides:
    - Transcript analysis and scoring
    - Coaching feedback generation
    - Gap analysis and missed opportunity detection
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        prompts_dir: Path,
    ):
        """
        Initialize the SPICED analyzer.

        Args:
            claude_client: Claude API client
            prompts_dir: Directory containing prompt templates
        """
        self.claude_client = claude_client
        self.prompts_dir = prompts_dir
        self._coaching_prompt: Optional[str] = None

    @property
    def coaching_prompt(self) -> str:
        """Load and cache the coaching prompt template."""
        if self._coaching_prompt is None:
            prompt_path = self.prompts_dir / "spiced_coaching.md"
            if prompt_path.exists():
                self._coaching_prompt = prompt_path.read_text()
            else:
                # Fallback to embedded prompt
                self._coaching_prompt = self._get_default_prompt()
        return self._coaching_prompt

    async def analyze_transcript(
        self,
        transcript: str,
        rep_name: str,
        call_type: CallType = CallType.DISCOVERY,
        prospect_company: Optional[str] = None,
        call_duration: Optional[str] = None,
        previous_scores: Optional[list[float]] = None,
    ) -> CoachingFeedback:
        """
        Analyze a transcript and generate SPICED coaching feedback.

        Args:
            transcript: Full call transcript text
            rep_name: Name of the sales rep
            call_type: Type of sales call
            prospect_company: Prospect's company name
            call_duration: Duration of the call
            previous_scores: Recent overall scores for context

        Returns:
            Complete coaching feedback with scores and recommendations
        """
        logger.info(f"Analyzing transcript for {rep_name}")

        # Build the prompt with context
        prompt = self._build_analysis_prompt(
            transcript=transcript,
            rep_name=rep_name,
            call_type=call_type,
            prospect_company=prospect_company,
            call_duration=call_duration,
            previous_scores=previous_scores,
        )

        # Call Claude for analysis
        response = await self.claude_client.complete(
            prompt=prompt,
            system=self._get_system_prompt(),
            max_tokens=4000,
            temperature=0.3,
        )

        # Parse the response into structured feedback
        feedback = self._parse_feedback_response(response)

        logger.info(f"Generated feedback with overall score {feedback.overall_score}")

        return feedback

    async def analyze_gaps(
        self,
        transcript: str,
        spiced_scores: SPICEDScores,
        call_id: UUID,
        rep_id: UUID,
    ) -> GapAnalysisReport:
        """
        Analyze gaps and missed opportunities in a call.

        Args:
            transcript: Full call transcript
            spiced_scores: Previously extracted SPICED scores
            call_id: ID of the analyzed call
            rep_id: ID of the sales rep

        Returns:
            Detailed gap analysis report
        """
        logger.info(f"Analyzing gaps for call {call_id}")

        prompt = self._build_gap_analysis_prompt(transcript, spiced_scores)

        response = await self.claude_client.complete(
            prompt=prompt,
            system=self._get_gap_analysis_system_prompt(),
            max_tokens=3000,
            temperature=0.3,
        )

        report = self._parse_gap_analysis_response(response, call_id, rep_id)

        return report

    def _build_analysis_prompt(
        self,
        transcript: str,
        rep_name: str,
        call_type: CallType,
        prospect_company: Optional[str],
        call_duration: Optional[str],
        previous_scores: Optional[list[float]],
    ) -> str:
        """Build the full analysis prompt with transcript and context."""
        context_parts = [
            f"Rep Name: {rep_name}",
            f"Call Type: {call_type.value}",
        ]

        if prospect_company:
            context_parts.append(f"Prospect Company: {prospect_company}")
        if call_duration:
            context_parts.append(f"Call Duration: {call_duration}")
        if previous_scores:
            context_parts.append(f"Previous Overall Scores: {previous_scores}")

        context = "\n".join(context_parts)

        return f"""Analyze the following sales call transcript and provide SPICED coaching feedback.

## Call Context
{context}

## Transcript
<transcript>
{transcript}
</transcript>

Provide your analysis in the specified JSON format, including:
1. Score each SPICED element (1-5) with justification and evidence
2. Identify 2-3 key strengths with specific examples
3. Identify 2-3 improvement areas with suggested questions
4. Provide 2-3 WbD-aligned coaching tips
5. Include 1-2 specific talk tracks for future calls
6. Summarize overall assessment and priority focus

Return ONLY valid JSON matching the expected schema."""

    def _build_gap_analysis_prompt(
        self,
        transcript: str,
        spiced_scores: SPICEDScores,
    ) -> str:
        """Build the gap analysis prompt."""
        scores_summary = {
            "situation": {
                "score": spiced_scores.situation.score,
                "justification": spiced_scores.situation.justification,
            },
            "pain": {
                "score": spiced_scores.pain.score,
                "justification": spiced_scores.pain.justification,
            },
            "impact": {
                "score": spiced_scores.impact.score,
                "justification": spiced_scores.impact.justification,
            },
            "critical_event": {
                "score": spiced_scores.critical_event.score,
                "justification": spiced_scores.critical_event.justification,
            },
            "expected_decision": {
                "score": spiced_scores.expected_decision.score,
                "justification": spiced_scores.expected_decision.justification,
            },
            "decision_criteria": {
                "score": spiced_scores.decision_criteria.score,
                "justification": spiced_scores.decision_criteria.justification,
            },
        }

        return f"""Analyze gaps and missed opportunities in this sales call.

## SPICED Scores Already Extracted
{json.dumps(scores_summary, indent=2)}

## Transcript
<transcript>
{transcript}
</transcript>

For each SPICED element, identify:
1. What information was gathered (known)
2. What information is still missing (unknown)
3. The most critical gap
4. A recovery question for the next call

Also identify specific missed opportunities where the rep could have dug deeper.

Return your analysis in the specified JSON format."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for coaching analysis."""
        return """You are an expert sales coach trained in the Winning by Design (WbD) SPICED methodology.

Your role is to analyze sales call transcripts and provide constructive, actionable coaching feedback that helps sales professionals improve their discovery skills.

## SPICED Framework
- **S**ituation: Current state, processes, tools, team structure
- **P**ain: Problems, challenges, frustrations
- **I**mpact: Business consequences, quantified cost/value
- **C**ritical Event: Timeline driver, urgency, deadline
- **E**xpected Decision: Decision process, stakeholders, authority
- **D**ecision Criteria: Requirements, evaluation metrics, success criteria

## Scoring Scale (1-5)
1 = Not addressed at all
2 = Mentioned superficially, not validated
3 = Adequately covered with moderate depth
4 = Well-developed with good detail
5 = Exceptional - deep, quantified, actionable insights

## Coaching Principles
- Be constructive, not critical
- Lead with strengths before improvements
- Be specific with examples and quotes
- Provide actionable talk tracks
- Align all feedback with WbD methodology

Always return valid JSON matching the expected response schema."""

    def _get_gap_analysis_system_prompt(self) -> str:
        """Get the system prompt for gap analysis."""
        return """You are an expert sales coach analyzing gaps and missed opportunities in a sales call.

Focus on:
1. What information is still unknown that should have been gathered
2. Specific moments where follow-up questions could have gone deeper
3. Recovery strategies for the next call

Be constructive and provide actionable recovery questions for each gap.

Always return valid JSON matching the expected response schema."""

    def _parse_feedback_response(self, response: str) -> CoachingFeedback:
        """Parse Claude's response into structured CoachingFeedback."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # Parse SPICED scores
            scores_data = data.get("scores", {})
            scores = SPICEDScores(
                situation=self._parse_element_score(scores_data.get("situation", {}), SPICEDElement.SITUATION),
                pain=self._parse_element_score(scores_data.get("pain", {}), SPICEDElement.PAIN),
                impact=self._parse_element_score(scores_data.get("impact", {}), SPICEDElement.IMPACT),
                critical_event=self._parse_element_score(scores_data.get("critical_event", {}), SPICEDElement.CRITICAL_EVENT),
                expected_decision=self._parse_element_score(scores_data.get("expected_decision", {}), SPICEDElement.EXPECTED_DECISION),
                decision_criteria=self._parse_element_score(scores_data.get("decision_criteria", {}), SPICEDElement.DECISION_CRITERIA),
            )

            # Parse strengths
            strengths = [
                Strength(
                    title=s.get("title", "Strength"),
                    description=s.get("description", ""),
                    example=s.get("example", ""),
                )
                for s in data.get("strengths", [])[:5]
            ]
            if not strengths:
                strengths = [Strength(title="Good effort", description="Engaged with prospect", example="N/A")]

            # Parse improvements
            improvements = [
                ImprovementArea(
                    title=i.get("title", "Improvement"),
                    gap=i.get("gap", ""),
                    suggested_question=i.get("suggested_question", ""),
                    impact=i.get("impact", ""),
                )
                for i in data.get("improvements", [])[:5]
            ]
            if not improvements:
                improvements = [ImprovementArea(
                    title="Continue improving",
                    gap="Room for deeper discovery",
                    suggested_question="Tell me more about that...",
                    impact="Better understanding leads to better solutions",
                )]

            # Parse coaching tips
            coaching_tips = [
                CoachingTip(
                    tip=t.get("tip", ""),
                    rationale=t.get("rationale", ""),
                    practice_exercise=t.get("practice_exercise", ""),
                )
                for t in data.get("coaching_tips", [])[:5]
            ]
            if not coaching_tips:
                coaching_tips = [CoachingTip(
                    tip="Focus on open-ended questions",
                    rationale="Open questions encourage deeper sharing",
                    practice_exercise="Start questions with 'How' or 'What'",
                )]

            # Parse talk tracks
            talk_tracks = [
                TalkTrack(
                    situation=t.get("situation", ""),
                    script=t.get("script", ""),
                    purpose=t.get("purpose", ""),
                )
                for t in data.get("talk_tracks", [])[:3]
            ]

            # Parse summary
            summary_data = data.get("summary", {})
            summary = CoachingSummary(
                overall_assessment=summary_data.get("overall_assessment", "Call analyzed successfully."),
                priority_focus=summary_data.get("priority_focus", "Continue developing SPICED skills"),
                next_call_goal=summary_data.get("next_call_goal", "Apply feedback from this analysis"),
            )

            return CoachingFeedback(
                scores=scores,
                overall_score=data.get("overall_score", scores.overall_score),
                strengths=strengths,
                improvements=improvements,
                coaching_tips=coaching_tips,
                talk_tracks=talk_tracks,
                summary=summary,
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse feedback response: {e}")
            # Return a default feedback structure
            return self._get_default_feedback()

    def _parse_element_score(self, data: dict, element: SPICEDElement) -> ElementScore:
        """Parse a single element score from response data."""
        return ElementScore(
            element=element,
            score=data.get("score", 3),
            justification=data.get("justification", "Score not provided"),
            evidence=data.get("evidence", []),
        )

    def _parse_gap_analysis_response(
        self,
        response: str,
        call_id: UUID,
        rep_id: UUID,
    ) -> GapAnalysisReport:
        """Parse Claude's gap analysis response."""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # Parse gaps by element
            gaps_by_element = {}
            gaps_data = data.get("gaps_by_element", {})

            for element in SPICEDElement:
                element_key = element.value
                if element_key in gaps_data:
                    gap_data = gaps_data[element_key]
                    gaps_by_element[element] = ElementGap(
                        element=element,
                        known=gap_data.get("known", []),
                        unknown=gap_data.get("unknown", []),
                        critical_gap=gap_data.get("critical_gap", "Not analyzed"),
                        recovery_question=gap_data.get("recovery_question", "Follow up on this area"),
                    )
                else:
                    gaps_by_element[element] = ElementGap(
                        element=element,
                        known=[],
                        unknown=["Not analyzed"],
                        critical_gap="Analysis not available",
                        recovery_question="Explore this area in next call",
                    )

            # Parse missed opportunities
            missed_opportunities = [
                MissedOpportunity(
                    timestamp_or_quote=m.get("timestamp_or_quote", ""),
                    what_was_said=m.get("what_was_said", ""),
                    follow_up_missed=m.get("follow_up_missed", ""),
                    impact_of_missing=m.get("impact_of_missing", ""),
                )
                for m in data.get("missed_opportunities", [])[:10]
            ]

            # Parse next call plan
            plan_data = data.get("next_call_plan", {})
            transitions = [
                QuestionTransition(
                    from_topic=t.get("from_topic", ""),
                    to_question=t.get("to_question", ""),
                )
                for t in plan_data.get("transitions", [])
            ]

            next_call_plan = NextCallPlan(
                priority_questions=plan_data.get("priority_questions", ["Follow up on gaps"]),
                transitions=transitions,
            )

            return GapAnalysisReport(
                call_id=call_id,
                rep_id=rep_id,
                gaps_by_element=gaps_by_element,
                missed_opportunities=missed_opportunities,
                next_call_plan=next_call_plan,
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse gap analysis response: {e}")
            return self._get_default_gap_analysis(call_id, rep_id)

    def _extract_json(self, response: str) -> str:
        """Extract JSON from a response that might be wrapped in markdown."""
        # Try to find JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        # Try to find raw JSON
        if "{" in response:
            start = response.find("{")
            # Find the matching closing brace
            depth = 0
            for i, char in enumerate(response[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return response[start:i + 1]

        return response

    def _get_default_feedback(self) -> CoachingFeedback:
        """Return default feedback when parsing fails."""
        default_score = ElementScore(
            element=SPICEDElement.SITUATION,
            score=3,
            justification="Analysis pending",
            evidence=[],
        )

        return CoachingFeedback(
            scores=SPICEDScores(
                situation=ElementScore(element=SPICEDElement.SITUATION, score=3, justification="Analysis pending", evidence=[]),
                pain=ElementScore(element=SPICEDElement.PAIN, score=3, justification="Analysis pending", evidence=[]),
                impact=ElementScore(element=SPICEDElement.IMPACT, score=3, justification="Analysis pending", evidence=[]),
                critical_event=ElementScore(element=SPICEDElement.CRITICAL_EVENT, score=3, justification="Analysis pending", evidence=[]),
                expected_decision=ElementScore(element=SPICEDElement.EXPECTED_DECISION, score=3, justification="Analysis pending", evidence=[]),
                decision_criteria=ElementScore(element=SPICEDElement.DECISION_CRITERIA, score=3, justification="Analysis pending", evidence=[]),
            ),
            overall_score=3.0,
            strengths=[Strength(title="Analysis Pending", description="Unable to parse response", example="N/A")],
            improvements=[ImprovementArea(title="Analysis Pending", gap="Unable to parse response", suggested_question="N/A", impact="N/A")],
            coaching_tips=[CoachingTip(tip="Analysis Pending", rationale="Unable to parse response", practice_exercise="N/A")],
            talk_tracks=[],
            summary=CoachingSummary(
                overall_assessment="Analysis could not be completed. Please retry.",
                priority_focus="Retry analysis",
                next_call_goal="Complete analysis",
            ),
        )

    def _get_default_gap_analysis(self, call_id: UUID, rep_id: UUID) -> GapAnalysisReport:
        """Return default gap analysis when parsing fails."""
        gaps_by_element = {}
        for element in SPICEDElement:
            gaps_by_element[element] = ElementGap(
                element=element,
                known=[],
                unknown=["Analysis failed"],
                critical_gap="Unable to analyze",
                recovery_question="Retry analysis",
            )

        return GapAnalysisReport(
            call_id=call_id,
            rep_id=rep_id,
            gaps_by_element=gaps_by_element,
            missed_opportunities=[],
            next_call_plan=NextCallPlan(priority_questions=["Retry analysis"]),
        )

    def _get_default_prompt(self) -> str:
        """Get the default embedded prompt template."""
        return """You are an expert sales coach trained in the Winning by Design SPICED methodology.
Analyze the provided transcript and return coaching feedback in JSON format."""
