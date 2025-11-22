"""Transcript data exporter with SPICED analysis."""

from datetime import datetime
from typing import Any, Dict, List, AsyncIterator

from app.models.export_import import ExportType, ExportFormat
from app.models.transcript import TranscriptExport
from .base import BaseExporter


class TranscriptExporter(BaseExporter):
    """Exporter for transcript data with SPICED analysis."""

    @property
    def export_type(self) -> ExportType:
        return ExportType.TRANSCRIPTS

    @property
    def supported_formats(self) -> List[ExportFormat]:
        return [ExportFormat.JSON, ExportFormat.CSV]

    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch transcript data from database.

        Args:
            filters: Filter criteria including:
                - date_from: Start date (ISO format)
                - date_to: End date (ISO format)
                - source: Transcript source (avoma, zoom, etc.)
                - user_id: Filter by user
                - include_spiced: Whether to include SPICED analysis (default True)
            record_ids: Specific transcript IDs to export

        Yields:
            Transcript data dictionaries
        """
        # TODO: Replace with actual database queries when DB is set up
        # For now, yield sample data structure for testing
        include_spiced = filters.get("include_spiced", True)

        # Sample transcript data structure
        sample_transcripts = [
            {
                "id": "transcript-001",
                "title": "Discovery Call - Acme Corp",
                "source": "zoom",
                "call_date": "2024-01-15T10:00:00Z",
                "duration_seconds": 3600,
                "participants": ["John Sales", "Jane Prospect"],
                "raw_text": "Full transcript text here...",
                "created_at": "2024-01-15T11:00:00Z",
                "spiced_analysis": {
                    "situation": {
                        "content": "Currently using manual spreadsheets for tracking",
                        "confidence": 85,
                    },
                    "pain": {
                        "content": "Losing deals due to slow response times",
                        "confidence": 90,
                    },
                    "impact": {
                        "content": "Estimated $500K in lost revenue quarterly",
                        "confidence": 75,
                    },
                    "critical_event": {
                        "content": "Board meeting in Q2 to review sales tech",
                        "confidence": 80,
                    },
                    "expected_decision": {
                        "content": "Committee decision with CFO final approval",
                        "confidence": 70,
                    },
                    "decision_criteria": {
                        "content": "Integration with Salesforce, mobile support",
                        "confidence": 85,
                    },
                    "summary": "Strong discovery call with qualified prospect...",
                    "key_quotes": [
                        "We're losing at least 3 deals a week to faster competitors"
                    ],
                    "follow_up_tasks": ["Send case study", "Schedule demo with CFO"],
                },
            },
        ]

        # Apply filters
        for transcript in sample_transcripts:
            # Filter by record IDs if specified
            if record_ids and transcript["id"] not in record_ids:
                continue

            # Filter by date range
            if filters.get("date_from"):
                call_date = datetime.fromisoformat(
                    transcript["call_date"].replace("Z", "+00:00")
                )
                filter_from = datetime.fromisoformat(filters["date_from"])
                if call_date < filter_from:
                    continue

            if filters.get("date_to"):
                call_date = datetime.fromisoformat(
                    transcript["call_date"].replace("Z", "+00:00")
                )
                filter_to = datetime.fromisoformat(filters["date_to"])
                if call_date > filter_to:
                    continue

            # Filter by source
            if filters.get("source") and transcript["source"] != filters["source"]:
                continue

            # Remove SPICED if not requested
            if not include_spiced:
                transcript = {
                    k: v for k, v in transcript.items() if k != "spiced_analysis"
                }

            yield transcript

    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform transcript record for export format.

        Args:
            record: Raw transcript record
            format: Target export format

        Returns:
            Transformed record
        """
        if format == ExportFormat.JSON:
            return self._transform_for_json(record)
        elif format == ExportFormat.CSV:
            return self._transform_for_csv(record)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _transform_for_json(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for JSON export."""
        # JSON export keeps full structure
        return {
            "id": record.get("id"),
            "title": record.get("title"),
            "source": record.get("source"),
            "call_date": record.get("call_date"),
            "duration_seconds": record.get("duration_seconds"),
            "duration_formatted": self._format_duration(
                record.get("duration_seconds", 0)
            ),
            "participants": record.get("participants", []),
            "raw_text": record.get("raw_text"),
            "spiced_analysis": record.get("spiced_analysis"),
            "created_at": record.get("created_at"),
        }

    def _transform_for_csv(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for CSV export (flattened)."""
        spiced = record.get("spiced_analysis", {})

        return {
            "id": record.get("id"),
            "title": record.get("title"),
            "source": record.get("source"),
            "call_date": record.get("call_date"),
            "duration_seconds": record.get("duration_seconds"),
            "duration_formatted": self._format_duration(
                record.get("duration_seconds", 0)
            ),
            "participants": ", ".join(record.get("participants", [])),
            # SPICED fields (flattened)
            "spiced_situation": self._get_spiced_field(spiced, "situation"),
            "spiced_situation_confidence": self._get_spiced_confidence(
                spiced, "situation"
            ),
            "spiced_pain": self._get_spiced_field(spiced, "pain"),
            "spiced_pain_confidence": self._get_spiced_confidence(spiced, "pain"),
            "spiced_impact": self._get_spiced_field(spiced, "impact"),
            "spiced_impact_confidence": self._get_spiced_confidence(spiced, "impact"),
            "spiced_critical_event": self._get_spiced_field(spiced, "critical_event"),
            "spiced_critical_event_confidence": self._get_spiced_confidence(
                spiced, "critical_event"
            ),
            "spiced_expected_decision": self._get_spiced_field(
                spiced, "expected_decision"
            ),
            "spiced_expected_decision_confidence": self._get_spiced_confidence(
                spiced, "expected_decision"
            ),
            "spiced_decision_criteria": self._get_spiced_field(
                spiced, "decision_criteria"
            ),
            "spiced_decision_criteria_confidence": self._get_spiced_confidence(
                spiced, "decision_criteria"
            ),
            "spiced_summary": spiced.get("summary", ""),
            "key_quotes": ", ".join(spiced.get("key_quotes", [])),
            "follow_up_tasks": ", ".join(spiced.get("follow_up_tasks", [])),
            "created_at": record.get("created_at"),
        }

    def _get_spiced_field(self, spiced: Dict, field: str) -> str:
        """Extract SPICED field content."""
        field_data = spiced.get(field, {})
        if isinstance(field_data, dict):
            return field_data.get("content", "")
        return str(field_data) if field_data else ""

    def _get_spiced_confidence(self, spiced: Dict, field: str) -> int:
        """Extract SPICED field confidence."""
        field_data = spiced.get(field, {})
        if isinstance(field_data, dict):
            return field_data.get("confidence", 0)
        return 0

    def _format_duration(self, seconds: int) -> str:
        """Format duration in HH:MM:SS."""
        if not seconds:
            return "00:00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
