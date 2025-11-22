"""Generated content exporter with ZIP archive support."""

import os
import zipfile
import json
from datetime import datetime
from typing import Any, Dict, List, AsyncIterator
from pathlib import Path
import aiofiles
import aiofiles.os

from app.models.export_import import ExportType, ExportFormat
from app.models.content import ContentType, ContentStatus
from .base import BaseExporter


class ContentExporter(BaseExporter):
    """Exporter for generated content with file attachments."""

    @property
    def export_type(self) -> ExportType:
        return ExportType.CONTENT

    @property
    def supported_formats(self) -> List[ExportFormat]:
        return [ExportFormat.JSON, ExportFormat.CSV, ExportFormat.ZIP]

    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch content data from database.

        Args:
            filters: Filter criteria including:
                - content_type: Filter by content type
                - status: Filter by status
                - date_from: Start date
                - date_to: End date
                - include_files: Whether to include file paths (default True)
            record_ids: Specific content IDs to export

        Yields:
            Content data dictionaries
        """
        include_files = filters.get("include_files", True)

        # TODO: Replace with actual database queries
        sample_content = [
            {
                "id": "content-001",
                "title": "Acme Corp Sales Deck",
                "content_type": ContentType.SALES_DECK.value,
                "status": ContentStatus.READY.value,
                "body": "# Acme Corp Sales Deck\n\n## Value Proposition\n...",
                "rendered_html": "<h1>Acme Corp Sales Deck</h1>...",
                "pdf_path": "/exports/content/acme-deck.pdf",
                "pptx_path": "/exports/content/acme-deck.pptx",
                "metadata": {
                    "template_name": "Standard Pitch Deck",
                    "brand_colors": ["#1a73e8", "#ffffff"],
                },
                "transcript_id": "transcript-001",
                "prospect_id": "prospect-001",
                "created_at": "2024-01-16T14:00:00Z",
            },
            {
                "id": "content-002",
                "title": "Q1 QBR Proposal",
                "content_type": ContentType.PROPOSAL.value,
                "status": ContentStatus.APPROVED.value,
                "body": "# Quarterly Business Review Proposal\n...",
                "rendered_html": "<h1>QBR Proposal</h1>...",
                "pdf_path": "/exports/content/qbr-proposal.pdf",
                "metadata": {
                    "template_name": "QBR Template",
                },
                "created_at": "2024-01-17T09:00:00Z",
            },
        ]

        for content in sample_content:
            # Filter by record IDs
            if record_ids and content["id"] not in record_ids:
                continue

            # Filter by content type
            if filters.get("content_type"):
                if content["content_type"] != filters["content_type"]:
                    continue

            # Filter by status
            if filters.get("status"):
                if content["status"] != filters["status"]:
                    continue

            # Remove file paths if not requested
            if not include_files:
                content = {
                    k: v
                    for k, v in content.items()
                    if k not in ["pdf_path", "pptx_path"]
                }

            yield content

    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform content record for export format."""
        if format == ExportFormat.JSON:
            return self._transform_for_json(record)
        elif format == ExportFormat.CSV:
            return self._transform_for_csv(record)
        elif format == ExportFormat.ZIP:
            return self._transform_for_json(record)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _transform_for_json(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for JSON export."""
        return {
            "id": record.get("id"),
            "title": record.get("title"),
            "content_type": record.get("content_type"),
            "status": record.get("status"),
            "body": record.get("body"),
            "rendered_html": record.get("rendered_html"),
            "metadata": record.get("metadata", {}),
            "files": {
                "pdf": record.get("pdf_path"),
                "pptx": record.get("pptx_path"),
            },
            "references": {
                "transcript_id": record.get("transcript_id"),
                "prospect_id": record.get("prospect_id"),
                "template_id": record.get("template_id"),
            },
            "created_at": record.get("created_at"),
        }

    def _transform_for_csv(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for CSV export (flattened)."""
        metadata = record.get("metadata", {})
        return {
            "id": record.get("id"),
            "title": record.get("title"),
            "content_type": record.get("content_type"),
            "status": record.get("status"),
            "body_preview": (record.get("body") or "")[:500],  # First 500 chars
            "template_name": metadata.get("template_name", ""),
            "has_pdf": bool(record.get("pdf_path")),
            "has_pptx": bool(record.get("pptx_path")),
            "transcript_id": record.get("transcript_id", ""),
            "prospect_id": record.get("prospect_id", ""),
            "created_at": record.get("created_at"),
        }

    async def _export_zip(
        self,
        filename: str,
        on_progress=None,
    ) -> str:
        """Export content as ZIP archive with all files."""
        filepath = self.export_dir / f"{filename}.zip"
        temp_dir = self.export_dir / f"temp_{filename}"

        # Create temp directory
        if not await aiofiles.os.path.exists(temp_dir):
            await aiofiles.os.makedirs(temp_dir)

        try:
            records = []
            file_manifest = []
            processed = 0

            async for record in self.fetch_data(
                self.job.filters or {}, self.job.record_ids or []
            ):
                try:
                    transformed = await self.transform_record(record, ExportFormat.ZIP)
                    records.append(transformed)

                    # Track files to include
                    if record.get("pdf_path"):
                        file_manifest.append({
                            "content_id": record["id"],
                            "type": "pdf",
                            "original_path": record["pdf_path"],
                            "archive_path": f"files/{record['id']}.pdf",
                        })

                    if record.get("pptx_path"):
                        file_manifest.append({
                            "content_id": record["id"],
                            "type": "pptx",
                            "original_path": record["pptx_path"],
                            "archive_path": f"files/{record['id']}.pptx",
                        })

                    processed += 1
                    if on_progress:
                        on_progress(processed, self.job.total_records)

                except Exception as e:
                    self.errors.append({
                        "record_id": record.get("id"),
                        "error": str(e),
                    })

            # Write manifest JSON
            manifest = {
                "export_type": "content",
                "exported_at": datetime.utcnow().isoformat(),
                "total_records": len(records),
                "files_included": len(file_manifest),
                "records": records,
                "file_manifest": file_manifest,
            }

            manifest_path = temp_dir / "manifest.json"
            async with aiofiles.open(manifest_path, "w") as f:
                await f.write(json.dumps(manifest, indent=2, default=str))

            # Create ZIP archive
            with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add manifest
                zf.write(manifest_path, "manifest.json")

                # Add files (in real implementation, copy actual files)
                # For now, create placeholder files directory structure
                for file_info in file_manifest:
                    # In production: copy actual file
                    # zf.write(file_info["original_path"], file_info["archive_path"])
                    pass

            return str(filepath)

        finally:
            # Cleanup temp directory
            import shutil
            if await aiofiles.os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
