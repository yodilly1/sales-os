"""Transcript bulk importer."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.export_import import (
    ImportType,
    ImportError as ImportErrorModel,
)
from app.models.transcript import TranscriptSource
from .base import BaseImporter


class TranscriptImporter(BaseImporter):
    """Importer for bulk transcript data.

    Supports:
    - JSON format (from Sales OS export)
    - CSV format (basic metadata only)
    - Various transcript sources
    """

    @property
    def import_type(self) -> ImportType:
        return ImportType.TRANSCRIPTS

    @property
    def required_fields(self) -> List[str]:
        return ["title", "raw_text"]

    @property
    def optional_fields(self) -> List[str]:
        return [
            "source",
            "source_id",
            "call_date",
            "duration_seconds",
            "participants",
            "prospect_id",
            "metadata",
            "spiced_analysis",
        ]

    async def validate_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Tuple[bool, List[ImportErrorModel]]:
        """Validate a transcript row.

        Validates:
        - Required fields present
        - Source is valid
        - Duration is numeric
        - Call date format
        """
        errors: List[ImportErrorModel] = []

        # Check required fields
        title = row.get("title", "").strip() if isinstance(row.get("title"), str) else str(row.get("title", ""))
        raw_text = row.get("raw_text", "")

        if not title:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="title",
                    value=title,
                    error="Title is required",
                )
            )

        if not raw_text:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="raw_text",
                    error="Transcript text is required",
                )
            )

        # Validate source if present
        source = row.get("source", "").strip().lower() if row.get("source") else ""
        if source:
            valid_sources = [s.value for s in TranscriptSource]
            if source not in valid_sources:
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="source",
                        value=source,
                        error=f"Invalid source. Valid values: {', '.join(valid_sources)}",
                    )
                )

        # Validate duration if present
        duration = row.get("duration_seconds")
        if duration is not None:
            try:
                duration_int = int(duration)
                if duration_int < 0:
                    errors.append(
                        ImportErrorModel(
                            row_number=row_number,
                            field="duration_seconds",
                            value=str(duration),
                            error="Duration cannot be negative",
                        )
                    )
            except (ValueError, TypeError):
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="duration_seconds",
                        value=str(duration),
                        error="Duration must be a number (seconds)",
                    )
                )

        # Validate call_date if present
        call_date = row.get("call_date")
        if call_date:
            try:
                # Try parsing various date formats
                self._parse_date(call_date)
            except ValueError:
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="call_date",
                        value=str(call_date),
                        error="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                    )
                )

        return len(errors) == 0, errors

    async def import_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Optional[str]:
        """Import a single transcript row.

        Creates:
        - Transcript record
        - SPICED analysis (if provided)

        Returns:
            Created transcript ID, or None if failed
        """
        try:
            # Normalize data
            title = row.get("title", "").strip() if isinstance(row.get("title"), str) else str(row.get("title", ""))
            raw_text = row.get("raw_text", "")

            # Normalize source
            source_value = row.get("source", "manual").strip().lower() if row.get("source") else "manual"
            source = source_value if source_value in [s.value for s in TranscriptSource] else "manual"

            source_id = row.get("source_id", "").strip() if row.get("source_id") else None

            # Parse call date
            call_date = None
            if row.get("call_date"):
                try:
                    call_date = self._parse_date(row["call_date"])
                except ValueError:
                    pass

            # Parse duration
            duration_seconds = None
            if row.get("duration_seconds") is not None:
                try:
                    duration_seconds = int(row["duration_seconds"])
                except (ValueError, TypeError):
                    pass

            # Parse participants
            participants = row.get("participants", [])
            if isinstance(participants, str):
                participants = [p.strip() for p in participants.split(",") if p.strip()]

            # Parse metadata
            metadata = row.get("metadata", {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}

            # TODO: Save to database
            transcript_id = str(uuid.uuid4())

            transcript_data = {
                "id": transcript_id,
                "title": title,
                "source": source,
                "source_id": source_id,
                "raw_text": raw_text,
                "call_date": call_date,
                "duration_seconds": duration_seconds,
                "participants": participants,
                "metadata": metadata,
                "organization_id": self.job.organization_id,
                "user_id": self.job.user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Handle SPICED analysis if provided
            spiced_analysis = row.get("spiced_analysis")
            if spiced_analysis:
                if isinstance(spiced_analysis, str):
                    import json
                    try:
                        spiced_analysis = json.loads(spiced_analysis)
                    except json.JSONDecodeError:
                        spiced_analysis = None

                if spiced_analysis:
                    # TODO: Create SPICED analysis record
                    pass

            # In real implementation: save to database
            # await self.db.transcripts.create(transcript_data)

            return transcript_id

        except Exception as e:
            self.errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    error=f"Failed to import: {str(e)}",
                )
            )
            return None

    def _parse_date(self, date_str: str) -> str:
        """Parse a date string and return ISO format."""
        from dateutil import parser

        # Handle various formats
        parsed = parser.parse(date_str)
        return parsed.isoformat()
