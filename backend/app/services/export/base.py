"""Base exporter class and utilities."""

import os
import json
import csv
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator, Callable
from pathlib import Path
import aiofiles
import aiofiles.os

from app.core.config import settings
from app.models.export_import import (
    ExportJob,
    ExportType,
    ExportFormat,
    ExportStatus,
)


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    def __init__(self, job: ExportJob):
        """Initialize exporter with job context."""
        self.job = job
        self.export_dir = Path(settings.export_temp_dir)
        self.errors: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def export_type(self) -> ExportType:
        """Return the export type this exporter handles."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[ExportFormat]:
        """Return list of supported export formats."""
        pass

    @abstractmethod
    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch data to export as an async iterator.

        Args:
            filters: Filter criteria for the export
            record_ids: Specific record IDs to export (if any)

        Yields:
            Dict containing record data
        """
        pass

    @abstractmethod
    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform a record for the target format.

        Args:
            record: Raw record data
            format: Target export format

        Returns:
            Transformed record data
        """
        pass

    async def export(
        self,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Execute the export and return the file path.

        Args:
            on_progress: Optional callback for progress updates (processed, total)

        Returns:
            Path to the exported file
        """
        # Ensure export directory exists
        await self._ensure_export_dir()

        # Generate output filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_type.value}_{self.job.id}_{timestamp}"

        # Route to appropriate format handler
        if self.job.export_format == ExportFormat.JSON:
            return await self._export_json(filename, on_progress)
        elif self.job.export_format == ExportFormat.CSV:
            return await self._export_csv(filename, on_progress)
        elif self.job.export_format == ExportFormat.HUBSPOT:
            return await self._export_hubspot_csv(filename, on_progress)
        elif self.job.export_format == ExportFormat.ZIP:
            return await self._export_zip(filename, on_progress)
        elif self.job.export_format == ExportFormat.PDF:
            return await self._export_pdf(filename, on_progress)
        else:
            raise ValueError(f"Unsupported format: {self.job.export_format}")

    async def _ensure_export_dir(self):
        """Create export directory if it doesn't exist."""
        if not await aiofiles.os.path.exists(self.export_dir):
            await aiofiles.os.makedirs(self.export_dir)

    async def _export_json(
        self,
        filename: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Export data as JSON file."""
        filepath = self.export_dir / f"{filename}.json"
        records = []
        processed = 0

        async for record in self.fetch_data(
            self.job.filters or {}, self.job.record_ids or []
        ):
            try:
                transformed = await self.transform_record(record, ExportFormat.JSON)
                records.append(transformed)
                processed += 1
                if on_progress:
                    on_progress(processed, self.job.total_records)
            except Exception as e:
                self.errors.append({
                    "record_id": record.get("id"),
                    "error": str(e),
                })

        export_data = {
            "export_type": self.export_type.value,
            "exported_at": datetime.utcnow().isoformat(),
            "total_records": len(records),
            "records": records,
        }

        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(export_data, indent=2, default=str))

        return str(filepath)

    async def _export_csv(
        self,
        filename: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Export data as CSV file."""
        filepath = self.export_dir / f"{filename}.csv"
        records = []
        processed = 0

        async for record in self.fetch_data(
            self.job.filters or {}, self.job.record_ids or []
        ):
            try:
                transformed = await self.transform_record(record, ExportFormat.CSV)
                records.append(transformed)
                processed += 1
                if on_progress:
                    on_progress(processed, self.job.total_records)
            except Exception as e:
                self.errors.append({
                    "record_id": record.get("id"),
                    "error": str(e),
                })

        if not records:
            # Create empty file with headers
            async with aiofiles.open(filepath, "w") as f:
                await f.write("")
            return str(filepath)

        # Write CSV
        headers = list(records[0].keys())
        async with aiofiles.open(filepath, "w", newline="") as f:
            # Write header
            await f.write(",".join(headers) + "\n")
            # Write rows
            for record in records:
                row = [self._csv_escape(str(record.get(h, ""))) for h in headers]
                await f.write(",".join(row) + "\n")

        return str(filepath)

    async def _export_hubspot_csv(
        self,
        filename: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Export data as HubSpot-compatible CSV."""
        # Default implementation uses standard CSV
        # Subclasses can override for HubSpot-specific formatting
        return await self._export_csv(filename, on_progress)

    async def _export_zip(
        self,
        filename: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Export data as ZIP archive."""
        # Default implementation - subclasses should override
        raise NotImplementedError("ZIP export must be implemented by subclass")

    async def _export_pdf(
        self,
        filename: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Export data as PDF."""
        # Default implementation - subclasses should override
        raise NotImplementedError("PDF export must be implemented by subclass")

    def _csv_escape(self, value: str) -> str:
        """Escape a value for CSV output."""
        if not value:
            return ""
        # Escape quotes and wrap in quotes if necessary
        if "," in value or '"' in value or "\n" in value:
            return '"' + value.replace('"', '""') + '"'
        return value

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "_"
    ) -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, ", ".join(str(i) for i in v)))
            else:
                items.append((new_key, v))
        return dict(items)
