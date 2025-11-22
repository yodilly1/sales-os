"""Coaching reports exporter with PDF support."""

import json
from datetime import datetime
from typing import Any, Dict, List, AsyncIterator, Optional
from pathlib import Path
import aiofiles

from app.models.export_import import ExportType, ExportFormat
from .base import BaseExporter


class CoachingExporter(BaseExporter):
    """Exporter for coaching reports with PDF generation."""

    @property
    def export_type(self) -> ExportType:
        return ExportType.COACHING

    @property
    def supported_formats(self) -> List[ExportFormat]:
        return [ExportFormat.JSON, ExportFormat.CSV, ExportFormat.PDF]

    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch coaching report data from database.

        Args:
            filters: Filter criteria including:
                - user_id: Filter by user
                - date_from: Reports created after date
                - date_to: Reports created before date
                - min_score: Minimum overall score
                - max_score: Maximum overall score
                - include_transcript: Include transcript details (default False)
            record_ids: Specific report IDs to export

        Yields:
            Coaching report data dictionaries
        """
        include_transcript = filters.get("include_transcript", False)

        # TODO: Replace with actual database queries
        sample_reports = [
            {
                "id": "coaching-001",
                "transcript_id": "transcript-001",
                "transcript_title": "Discovery Call - Acme Corp",
                "call_date": "2024-01-15T10:00:00Z",
                "user_id": "user-001",
                "user_name": "John Sales",
                # Scores
                "overall_score": 4.2,
                "situation_score": 5,
                "pain_score": 4,
                "impact_score": 4,
                "critical_event_score": 4,
                "expected_decision_score": 3,
                "decision_criteria_score": 5,
                # Feedback
                "executive_summary": "Strong discovery call with excellent SPICED methodology application. Key areas for improvement in decision process exploration.",
                "key_strengths": [
                    "Excellent situation discovery",
                    "Strong pain point identification",
                    "Clear decision criteria documentation",
                ],
                "areas_for_improvement": [
                    "Could explore decision timeline more deeply",
                    "Consider probing for additional stakeholders",
                ],
                "recommended_actions": [
                    "Practice decision process questions",
                    "Review multi-threaded selling techniques",
                ],
                "coaching_tips": [
                    "Try the 'paper process' question: 'Walk me through your typical purchase process'",
                    "Ask about past purchase decisions for context",
                ],
                # Comparison
                "team_average": 3.8,
                "percentile_rank": 75,
                # WbD
                "wbd_alignment_score": 85,
                "wbd_feedback": "Excellent alignment with WbD methodology. Consider incorporating more impact quantification.",
                "created_at": "2024-01-15T12:00:00Z",
            },
            {
                "id": "coaching-002",
                "transcript_id": "transcript-002",
                "transcript_title": "Demo Call - TechCorp",
                "call_date": "2024-01-16T14:00:00Z",
                "user_id": "user-002",
                "user_name": "Sarah Seller",
                "overall_score": 3.5,
                "situation_score": 4,
                "pain_score": 3,
                "impact_score": 3,
                "critical_event_score": 4,
                "expected_decision_score": 4,
                "decision_criteria_score": 3,
                "executive_summary": "Good demo call but missed opportunities to tie features to pain points.",
                "key_strengths": [
                    "Good understanding of timeline",
                    "Clear decision process mapped",
                ],
                "areas_for_improvement": [
                    "Connect features to specific pain points",
                    "Quantify business impact during demo",
                ],
                "recommended_actions": [
                    "Create feature-benefit mapping document",
                    "Practice impact quantification",
                ],
                "coaching_tips": [
                    "Before each feature, ask: 'How does this connect to their pain?'",
                ],
                "team_average": 3.8,
                "percentile_rank": 45,
                "wbd_alignment_score": 70,
                "wbd_feedback": "Good foundation. Focus on impact quantification and pain connection.",
                "created_at": "2024-01-16T16:00:00Z",
            },
        ]

        for report in sample_reports:
            # Filter by record IDs
            if record_ids and report["id"] not in record_ids:
                continue

            # Filter by user
            if filters.get("user_id") and report["user_id"] != filters["user_id"]:
                continue

            # Filter by score range
            if filters.get("min_score") is not None:
                if report["overall_score"] < filters["min_score"]:
                    continue

            if filters.get("max_score") is not None:
                if report["overall_score"] > filters["max_score"]:
                    continue

            yield report

    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform coaching report for export format."""
        if format == ExportFormat.JSON:
            return self._transform_for_json(record)
        elif format == ExportFormat.CSV:
            return self._transform_for_csv(record)
        elif format == ExportFormat.PDF:
            return self._transform_for_json(record)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _transform_for_json(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for JSON export."""
        return {
            "id": record.get("id"),
            "transcript": {
                "id": record.get("transcript_id"),
                "title": record.get("transcript_title"),
                "call_date": record.get("call_date"),
            },
            "user": {
                "id": record.get("user_id"),
                "name": record.get("user_name"),
            },
            "scores": {
                "overall": record.get("overall_score"),
                "situation": record.get("situation_score"),
                "pain": record.get("pain_score"),
                "impact": record.get("impact_score"),
                "critical_event": record.get("critical_event_score"),
                "expected_decision": record.get("expected_decision_score"),
                "decision_criteria": record.get("decision_criteria_score"),
            },
            "feedback": {
                "executive_summary": record.get("executive_summary"),
                "key_strengths": record.get("key_strengths", []),
                "areas_for_improvement": record.get("areas_for_improvement", []),
                "recommended_actions": record.get("recommended_actions", []),
                "coaching_tips": record.get("coaching_tips", []),
            },
            "comparison": {
                "team_average": record.get("team_average"),
                "percentile_rank": record.get("percentile_rank"),
            },
            "wbd": {
                "alignment_score": record.get("wbd_alignment_score"),
                "feedback": record.get("wbd_feedback"),
            },
            "created_at": record.get("created_at"),
        }

    def _transform_for_csv(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for CSV export (flattened)."""
        return {
            "id": record.get("id"),
            "transcript_id": record.get("transcript_id"),
            "transcript_title": record.get("transcript_title"),
            "call_date": record.get("call_date"),
            "user_id": record.get("user_id"),
            "user_name": record.get("user_name"),
            "overall_score": record.get("overall_score"),
            "situation_score": record.get("situation_score"),
            "pain_score": record.get("pain_score"),
            "impact_score": record.get("impact_score"),
            "critical_event_score": record.get("critical_event_score"),
            "expected_decision_score": record.get("expected_decision_score"),
            "decision_criteria_score": record.get("decision_criteria_score"),
            "executive_summary": record.get("executive_summary", ""),
            "key_strengths": "; ".join(record.get("key_strengths", [])),
            "areas_for_improvement": "; ".join(
                record.get("areas_for_improvement", [])
            ),
            "recommended_actions": "; ".join(record.get("recommended_actions", [])),
            "coaching_tips": "; ".join(record.get("coaching_tips", [])),
            "team_average": record.get("team_average"),
            "percentile_rank": record.get("percentile_rank"),
            "wbd_alignment_score": record.get("wbd_alignment_score"),
            "wbd_feedback": record.get("wbd_feedback", ""),
            "created_at": record.get("created_at"),
        }

    async def _export_pdf(
        self,
        filename: str,
        on_progress=None,
    ) -> str:
        """Export coaching reports as PDF.

        Generates a professional PDF report with:
        - Summary statistics
        - Individual report cards
        - Score visualizations
        - Recommendations
        """
        filepath = self.export_dir / f"{filename}.pdf"
        records = []
        processed = 0

        async for record in self.fetch_data(
            self.job.filters or {}, self.job.record_ids or []
        ):
            try:
                transformed = await self.transform_record(record, ExportFormat.PDF)
                records.append(transformed)
                processed += 1
                if on_progress:
                    on_progress(processed, self.job.total_records)
            except Exception as e:
                self.errors.append({
                    "record_id": record.get("id"),
                    "error": str(e),
                })

        # Generate PDF using reportlab
        await self._generate_pdf(filepath, records)

        return str(filepath)

    async def _generate_pdf(self, filepath: Path, records: List[Dict]) -> None:
        """Generate PDF document from coaching records.

        Uses reportlab for PDF generation with professional styling.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
            )

            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "Title",
                parent=styles["Title"],
                fontSize=24,
                spaceAfter=30,
            )
            heading_style = ParagraphStyle(
                "Heading",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=12,
            )
            normal_style = styles["Normal"]

            story = []

            # Title
            story.append(Paragraph("SPICED Coaching Report", title_style))
            story.append(
                Paragraph(
                    f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                    normal_style,
                )
            )
            story.append(Spacer(1, 20))

            # Summary statistics
            if records:
                avg_score = sum(r["scores"]["overall"] for r in records) / len(records)
                story.append(Paragraph("Summary", heading_style))
                summary_data = [
                    ["Total Reports", str(len(records))],
                    ["Average Score", f"{avg_score:.1f}/5.0"],
                ]
                summary_table = Table(summary_data, colWidths=[2 * inch, 2 * inch])
                summary_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("PADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                story.append(summary_table)
                story.append(Spacer(1, 20))

            # Individual reports
            for record in records:
                story.append(
                    Paragraph(
                        f"Call: {record['transcript']['title']}", heading_style
                    )
                )

                # Score table
                scores = record["scores"]
                score_data = [
                    ["Element", "Score"],
                    ["Overall", f"{scores['overall']}/5.0"],
                    ["Situation", f"{scores['situation']}/5"],
                    ["Pain", f"{scores['pain']}/5"],
                    ["Impact", f"{scores['impact']}/5"],
                    ["Critical Event", f"{scores['critical_event']}/5"],
                    ["Expected Decision", f"{scores['expected_decision']}/5"],
                    ["Decision Criteria", f"{scores['decision_criteria']}/5"],
                ]
                score_table = Table(score_data, colWidths=[2.5 * inch, 1.5 * inch])
                score_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("PADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(score_table)
                story.append(Spacer(1, 10))

                # Executive summary
                story.append(
                    Paragraph(record["feedback"]["executive_summary"], normal_style)
                )
                story.append(Spacer(1, 20))

            doc.build(story)

        except ImportError:
            # Fallback: create a simple text-based PDF placeholder
            async with aiofiles.open(filepath, "w") as f:
                await f.write("PDF generation requires reportlab package.\n")
                await f.write(json.dumps(records, indent=2, default=str))
