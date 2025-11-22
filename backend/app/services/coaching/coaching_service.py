"""
Main Coaching Service

Orchestrates SPICED analysis, coaching feedback generation,
gap analysis, trend analysis, and team benchmarking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from ..claude_client import ClaudeClient
from ...models.coaching import (
    CallMetadata,
    CallType,
    CoachingFeedback,
    CoachingReport,
    CoachingRequest,
    ElementScore,
    GapAnalysisReport,
    RepScoreHistory,
    ScoreHistoryEntry,
    SPICEDElement,
    SPICEDScores,
    TeamBenchmarkReport,
    TeamBenchmarkRequest,
    TrendAnalysisReport,
    TrendAnalysisRequest,
)
from .analyzer import SPICEDAnalyzer
from .benchmarking import TeamBenchmarkingService
from .trends import TrendAnalysisService

logger = logging.getLogger(__name__)


class CoachingService:
    """
    Main service for SPICED coaching functionality.

    Provides:
    - Per-call coaching analysis and feedback
    - Gap analysis for missed opportunities
    - Trend analysis over time
    - Team benchmarking
    """

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        prompts_dir: Optional[Path] = None,
    ):
        """
        Initialize the coaching service.

        Args:
            claude_client: Claude API client for AI-powered analysis
            prompts_dir: Directory containing prompt templates
        """
        self.claude_client = claude_client or ClaudeClient()
        self.prompts_dir = prompts_dir or Path(__file__).parent.parent.parent.parent.parent / "claude" / "prompts"

        self.analyzer = SPICEDAnalyzer(self.claude_client, self.prompts_dir)
        self.trend_service = TrendAnalysisService()
        self.benchmark_service = TeamBenchmarkingService()

        # In-memory storage for demo purposes
        # In production, this would be replaced with database integration
        self._coaching_reports: dict[UUID, CoachingReport] = {}
        self._score_history: dict[UUID, RepScoreHistory] = {}

    async def analyze_call(
        self,
        request: CoachingRequest,
    ) -> CoachingReport:
        """
        Analyze a sales call transcript and generate coaching feedback.

        Args:
            request: Coaching request with transcript and metadata

        Returns:
            Complete coaching report with SPICED scores and feedback
        """
        logger.info(f"Analyzing call for rep {request.rep_name}")

        # Get previous scores for context
        previous_scores = self._get_previous_scores(request.rep_id)

        # Analyze transcript using Claude
        feedback = await self.analyzer.analyze_transcript(
            transcript=request.transcript,
            rep_name=request.rep_name,
            call_type=request.call_type,
            prospect_company=request.prospect_company,
            previous_scores=previous_scores,
        )

        # Create call metadata
        metadata = CallMetadata(
            rep_id=request.rep_id,
            rep_name=request.rep_name,
            call_type=request.call_type,
            prospect_company=request.prospect_company,
            prospect_name=request.prospect_name,
            call_duration_minutes=request.call_duration_minutes,
            call_date=request.call_date or datetime.utcnow(),
        )

        # Create the coaching report
        report = CoachingReport(
            metadata=metadata,
            feedback=feedback,
            previous_scores=previous_scores,
        )

        # Store the report and update history
        self._store_report(report)
        self._update_score_history(report)

        logger.info(f"Generated coaching report {report.id} with overall score {feedback.overall_score}")

        return report

    async def analyze_call_with_gaps(
        self,
        request: CoachingRequest,
    ) -> tuple[CoachingReport, GapAnalysisReport]:
        """
        Analyze a call and also generate detailed gap analysis.

        Args:
            request: Coaching request with transcript and metadata

        Returns:
            Tuple of (CoachingReport, GapAnalysisReport)
        """
        # First get the coaching report
        report = await self.analyze_call(request)

        # Then generate gap analysis
        gap_report = await self.analyzer.analyze_gaps(
            transcript=request.transcript,
            spiced_scores=report.feedback.scores,
            call_id=report.metadata.call_id,
            rep_id=request.rep_id,
        )

        return report, gap_report

    async def generate_trend_analysis(
        self,
        request: TrendAnalysisRequest,
    ) -> TrendAnalysisReport:
        """
        Generate trend analysis for a rep over time.

        Args:
            request: Trend analysis request with rep ID and date range

        Returns:
            Trend analysis report with patterns and recommendations
        """
        # Get score history for the rep
        history = self._get_score_history(request.rep_id)

        if not history or len(history.entries) < request.min_calls:
            raise ValueError(
                f"Insufficient data for trend analysis. "
                f"Need at least {request.min_calls} calls, found {len(history.entries) if history else 0}"
            )

        # Filter by date range if specified
        entries = history.entries
        if request.start_date:
            entries = [e for e in entries if e.call_date >= request.start_date]
        if request.end_date:
            entries = [e for e in entries if e.call_date <= request.end_date]

        # Generate trend analysis
        report = await self.trend_service.analyze_trends(
            rep_id=request.rep_id,
            rep_name=history.rep_name,
            entries=entries,
        )

        return report

    async def generate_team_benchmark(
        self,
        request: TeamBenchmarkRequest,
    ) -> TeamBenchmarkReport:
        """
        Generate team benchmarking report.

        Args:
            request: Team benchmark request with team info and rep IDs

        Returns:
            Team benchmark report with comparisons and recommendations
        """
        # Gather score histories for all reps
        rep_histories: list[RepScoreHistory] = []
        for rep_id in request.rep_ids:
            history = self._get_score_history(rep_id)
            if history and history.entries:
                # Filter by date range if specified
                if request.start_date or request.end_date:
                    filtered_entries = history.entries
                    if request.start_date:
                        filtered_entries = [e for e in filtered_entries if e.call_date >= request.start_date]
                    if request.end_date:
                        filtered_entries = [e for e in filtered_entries if e.call_date <= request.end_date]
                    history = RepScoreHistory(
                        rep_id=history.rep_id,
                        rep_name=history.rep_name,
                        entries=filtered_entries,
                    )
                rep_histories.append(history)

        if len(rep_histories) < 2:
            raise ValueError("Need at least 2 reps with call data for team benchmarking")

        # Generate benchmark report
        report = await self.benchmark_service.generate_benchmark(
            team_id=request.team_id,
            team_name=request.team_name,
            rep_histories=rep_histories,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        return report

    def get_coaching_report(self, report_id: UUID) -> Optional[CoachingReport]:
        """Retrieve a coaching report by ID."""
        return self._coaching_reports.get(report_id)

    def get_rep_reports(
        self,
        rep_id: UUID,
        limit: int = 10,
    ) -> list[CoachingReport]:
        """Get recent coaching reports for a rep."""
        reports = [
            r for r in self._coaching_reports.values()
            if r.metadata.rep_id == rep_id
        ]
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports[:limit]

    def _get_previous_scores(self, rep_id: UUID, count: int = 5) -> Optional[list[float]]:
        """Get the last N overall scores for a rep."""
        history = self._score_history.get(rep_id)
        if not history or not history.entries:
            return None

        recent = sorted(history.entries, key=lambda e: e.call_date, reverse=True)[:count]
        return [e.overall_score for e in recent]

    def _get_score_history(self, rep_id: UUID) -> Optional[RepScoreHistory]:
        """Get complete score history for a rep."""
        return self._score_history.get(rep_id)

    def _store_report(self, report: CoachingReport) -> None:
        """Store a coaching report."""
        self._coaching_reports[report.id] = report

    def _update_score_history(self, report: CoachingReport) -> None:
        """Update score history with new report data."""
        rep_id = report.metadata.rep_id

        if rep_id not in self._score_history:
            self._score_history[rep_id] = RepScoreHistory(
                rep_id=rep_id,
                rep_name=report.metadata.rep_name,
            )

        entry = ScoreHistoryEntry(
            call_id=report.metadata.call_id,
            call_date=report.metadata.call_date,
            scores=report.feedback.scores.scores_dict,
            overall_score=report.feedback.overall_score,
            call_type=report.metadata.call_type,
        )

        self._score_history[rep_id].entries.append(entry)


class CoachingServiceFactory:
    """Factory for creating CoachingService instances."""

    _instance: Optional[CoachingService] = None

    @classmethod
    def get_instance(cls) -> CoachingService:
        """Get or create the singleton CoachingService instance."""
        if cls._instance is None:
            cls._instance = CoachingService()
        return cls._instance

    @classmethod
    def create(
        cls,
        claude_client: Optional[ClaudeClient] = None,
        prompts_dir: Optional[Path] = None,
    ) -> CoachingService:
        """Create a new CoachingService instance with custom configuration."""
        return CoachingService(
            claude_client=claude_client,
            prompts_dir=prompts_dir,
        )
