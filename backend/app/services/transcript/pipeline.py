"""Transcript processing pipeline for auto-analyzing recordings."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

from app.models.zoom import ParsedTranscript, TranscriptLine
from app.services.transcript.spiced import SPICEDAnalyzer

logger = logging.getLogger(__name__)


class CallNotes(BaseModel):
    """Generated call notes from transcript analysis."""

    meeting_topic: str
    date: datetime
    duration_minutes: float
    participants: List[str]
    summary: str
    key_points: List[str]
    action_items: List[str]
    follow_up_questions: List[str]


class ProcessingResult(BaseModel):
    """Complete result from transcript processing."""

    transcript: ParsedTranscript
    spiced_analysis: Optional[Dict[str, Any]] = None
    call_notes: Optional[CallNotes] = None
    crm_data: Optional[Dict[str, Any]] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptProcessingPipeline:
    """Pipeline for processing transcripts through SPICED analysis.

    This pipeline:
    1. Takes a parsed transcript
    2. Runs SPICED methodology analysis
    3. Generates call notes and CRM-ready data
    4. Returns structured results for storage and display
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the pipeline.

        Args:
            anthropic_api_key: Optional API key for Claude
        """
        self.spiced_analyzer = SPICEDAnalyzer(api_key=anthropic_api_key)

    async def process_transcript(
        self, transcript: ParsedTranscript
    ) -> Dict[str, Any]:
        """Process a transcript through the full pipeline.

        Args:
            transcript: Parsed transcript with timing and speaker info

        Returns:
            Complete processing results including SPICED analysis
        """
        logger.info(
            f"Processing transcript for meeting: {transcript.meeting_topic or transcript.meeting_id}"
        )

        # Get the full text for analysis
        full_text = transcript.get_full_text()

        if not full_text or len(full_text.strip()) < 100:
            logger.warning("Transcript too short for meaningful analysis")
            return {
                "error": "Transcript too short for analysis",
                "transcript_length": len(full_text) if full_text else 0,
            }

        # Run SPICED analysis
        logger.info("Running SPICED analysis...")
        spiced_result = await self.spiced_analyzer.analyze(full_text)

        # Generate call notes
        call_notes = self._generate_call_notes(transcript, spiced_result)

        # Generate CRM-ready data
        crm_data = self._generate_crm_data(transcript, spiced_result, call_notes)

        result = {
            "meeting_id": transcript.meeting_id,
            "meeting_topic": transcript.meeting_topic,
            "duration_seconds": transcript.total_duration,
            "speaker_count": len(transcript.speakers),
            "speakers": transcript.speakers,
            "line_count": len(transcript.lines),
            "spiced_analysis": spiced_result,
            "call_notes": call_notes.model_dump() if call_notes else None,
            "crm_data": crm_data,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Processing complete. Overall SPICED score: {spiced_result.get('overall_score', 'N/A')}"
        )

        return result

    def _generate_call_notes(
        self,
        transcript: ParsedTranscript,
        spiced_result: Dict[str, Any],
    ) -> CallNotes:
        """Generate structured call notes from analysis.

        Args:
            transcript: The parsed transcript
            spiced_result: SPICED analysis results

        Returns:
            CallNotes with summary and action items
        """
        # Extract key points from SPICED analysis
        key_points = []

        for element in ["situation", "pain", "impact", "critical_event"]:
            element_data = spiced_result.get(element, {})
            if element_data.get("score", 0) >= 3:
                key_points.append(element_data.get("analysis", "")[:200])

        # Extract action items from recommendations
        action_items = spiced_result.get("recommended_next_steps", [])

        # Extract follow-up questions from suggestions
        follow_up_questions = []
        for element in ["situation", "pain", "impact", "critical_event", "expected_decision", "decision_criteria"]:
            element_data = spiced_result.get(element, {})
            suggestions = element_data.get("suggestions", [])
            follow_up_questions.extend(suggestions[:1])  # Take first suggestion from each

        return CallNotes(
            meeting_topic=transcript.meeting_topic or "Sales Call",
            date=datetime.utcnow(),
            duration_minutes=transcript.total_duration / 60,
            participants=transcript.speakers,
            summary=spiced_result.get("summary", "Call analysis completed."),
            key_points=key_points[:5],  # Limit to top 5
            action_items=action_items[:5],  # Limit to top 5
            follow_up_questions=follow_up_questions[:5],  # Limit to top 5
        )

    def _generate_crm_data(
        self,
        transcript: ParsedTranscript,
        spiced_result: Dict[str, Any],
        call_notes: CallNotes,
    ) -> Dict[str, Any]:
        """Generate CRM-ready data for HubSpot integration.

        Args:
            transcript: The parsed transcript
            spiced_result: SPICED analysis results
            call_notes: Generated call notes

        Returns:
            Dict with CRM-compatible field structure
        """
        # Format for HubSpot note
        note_body = self._format_crm_note(call_notes, spiced_result)

        # Tasks to create
        tasks = []
        for i, action in enumerate(call_notes.action_items[:3]):
            tasks.append({
                "subject": action[:100],  # HubSpot has length limits
                "priority": "HIGH" if i == 0 else "MEDIUM",
                "type": "CALL",
            })

        return {
            "note": {
                "body": note_body,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "tasks": tasks,
            "properties": {
                "last_call_date": datetime.utcnow().isoformat(),
                "last_call_duration": int(transcript.total_duration / 60),
                "spiced_score": spiced_result.get("overall_score", 0),
                "call_summary": call_notes.summary[:500],
            },
            "key_insights": spiced_result.get("key_insights", []),
        }

    def _format_crm_note(
        self,
        call_notes: CallNotes,
        spiced_result: Dict[str, Any],
    ) -> str:
        """Format call notes as a CRM note body.

        Args:
            call_notes: Generated call notes
            spiced_result: SPICED analysis results

        Returns:
            Formatted note string for CRM
        """
        lines = [
            f"## Call Summary: {call_notes.meeting_topic}",
            f"**Date:** {call_notes.date.strftime('%Y-%m-%d %H:%M')}",
            f"**Duration:** {call_notes.duration_minutes:.0f} minutes",
            f"**Participants:** {', '.join(call_notes.participants)}",
            "",
            "### Summary",
            call_notes.summary,
            "",
            f"### SPICED Score: {spiced_result.get('overall_score', 0):.1f}/5.0",
            "",
        ]

        # Add SPICED element scores
        for element in ["Situation", "Pain", "Impact", "Critical Event", "Expected Decision", "Decision Criteria"]:
            element_key = element.lower().replace(" ", "_")
            element_data = spiced_result.get(element_key, {})
            score = element_data.get("score", 0)
            lines.append(f"- **{element}:** {score}/5")

        lines.extend([
            "",
            "### Key Points",
        ])
        for point in call_notes.key_points:
            lines.append(f"- {point}")

        lines.extend([
            "",
            "### Action Items",
        ])
        for action in call_notes.action_items:
            lines.append(f"- [ ] {action}")

        if call_notes.follow_up_questions:
            lines.extend([
                "",
                "### Follow-up Questions",
            ])
            for question in call_notes.follow_up_questions:
                lines.append(f"- {question}")

        return "\n".join(lines)


class BatchTranscriptProcessor:
    """Process multiple transcripts in batch."""

    def __init__(self, pipeline: Optional[TranscriptProcessingPipeline] = None):
        """Initialize batch processor.

        Args:
            pipeline: Processing pipeline instance
        """
        self.pipeline = pipeline or TranscriptProcessingPipeline()

    async def process_batch(
        self,
        transcripts: List[ParsedTranscript],
    ) -> List[Dict[str, Any]]:
        """Process multiple transcripts.

        Args:
            transcripts: List of parsed transcripts

        Returns:
            List of processing results
        """
        results = []
        for transcript in transcripts:
            try:
                result = await self.pipeline.process_transcript(transcript)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing transcript {transcript.meeting_id}: {e}")
                results.append({
                    "meeting_id": transcript.meeting_id,
                    "error": str(e),
                })
        return results
