"""Full account backup exporter."""

import json
import zipfile
from datetime import datetime
from typing import Any, Dict, List, AsyncIterator
from pathlib import Path
import aiofiles
import aiofiles.os

from app.models.export_import import ExportType, ExportFormat
from .base import BaseExporter
from .transcript_exporter import TranscriptExporter
from .content_exporter import ContentExporter
from .prospect_exporter import ProspectExporter
from .coaching_exporter import CoachingExporter


class BackupExporter(BaseExporter):
    """Full account backup exporter.

    Creates a comprehensive backup archive containing:
    - All transcripts with SPICED analysis
    - All generated content with files
    - All prospects and companies
    - All coaching reports
    - All templates
    - Account settings and configuration
    """

    @property
    def export_type(self) -> ExportType:
        return ExportType.FULL_BACKUP

    @property
    def supported_formats(self) -> List[ExportFormat]:
        return [ExportFormat.JSON, ExportFormat.ZIP]

    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch all account data for backup.

        Args:
            filters: Filter criteria (mostly ignored for full backup)
                - include_content_files: Include PDF/PPTX files (default True)
            record_ids: Ignored for full backup

        Yields:
            Data sections for backup
        """
        include_files = filters.get("include_content_files", True)

        # Yield data in sections
        # TODO: Replace with actual database queries

        # 1. Organization and settings
        yield {
            "section": "organization",
            "data": {
                "id": "org-001",
                "name": "Demo Organization",
                "domain": "demo.com",
                "settings": {
                    "default_template_id": "template-001",
                    "brand_colors": ["#1a73e8", "#ffffff"],
                    "hubspot_connected": True,
                    "avoma_connected": True,
                },
                "created_at": "2024-01-01T00:00:00Z",
            },
        }

        # 2. Users
        yield {
            "section": "users",
            "data": [
                {
                    "id": "user-001",
                    "email": "john@demo.com",
                    "full_name": "John Sales",
                    "role": "sales_rep",
                    "team_id": "team-001",
                },
                {
                    "id": "user-002",
                    "email": "sarah@demo.com",
                    "full_name": "Sarah Seller",
                    "role": "manager",
                    "team_id": "team-001",
                },
            ],
        }

        # 3. Teams
        yield {
            "section": "teams",
            "data": [
                {
                    "id": "team-001",
                    "name": "Sales Team A",
                    "manager_id": "user-002",
                },
            ],
        }

        # 4. Companies
        yield {
            "section": "companies",
            "data": [
                {
                    "id": "company-001",
                    "name": "Acme Corporation",
                    "domain": "acme.com",
                    "industry": "Technology",
                    "size": "enterprise",
                    "employee_count": 5000,
                },
                {
                    "id": "company-002",
                    "name": "TechCorp",
                    "domain": "techcorp.io",
                    "industry": "Software",
                    "size": "mid_market",
                },
            ],
        }

        # 5. Prospects
        yield {
            "section": "prospects",
            "data": [
                {
                    "id": "prospect-001",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@acme.com",
                    "title": "VP of Sales",
                    "company_id": "company-001",
                    "status": "qualified",
                },
            ],
        }

        # 6. Transcripts with SPICED
        yield {
            "section": "transcripts",
            "data": [
                {
                    "id": "transcript-001",
                    "title": "Discovery Call - Acme Corp",
                    "source": "zoom",
                    "call_date": "2024-01-15T10:00:00Z",
                    "raw_text": "Full transcript...",
                    "spiced_analysis": {
                        "situation": "Current manual process",
                        "pain": "Losing deals",
                        "impact": "$500K quarterly",
                    },
                },
            ],
        }

        # 7. Content
        yield {
            "section": "content",
            "data": [
                {
                    "id": "content-001",
                    "title": "Acme Corp Sales Deck",
                    "content_type": "sales_deck",
                    "body": "# Sales Deck Content...",
                    "files": ["acme-deck.pdf", "acme-deck.pptx"] if include_files else [],
                },
            ],
        }

        # 8. Templates
        yield {
            "section": "templates",
            "data": [
                {
                    "id": "template-001",
                    "name": "Standard Pitch Deck",
                    "content_type": "sales_deck",
                    "template_body": "# {{company_name}} Pitch\n\n## Problem...",
                    "variables": ["company_name", "industry", "pain_point"],
                },
            ],
        }

        # 9. Coaching Reports
        yield {
            "section": "coaching_reports",
            "data": [
                {
                    "id": "coaching-001",
                    "transcript_id": "transcript-001",
                    "overall_score": 4.2,
                    "executive_summary": "Strong discovery call...",
                },
            ],
        }

        # 10. Integrations config (sanitized - no API keys)
        yield {
            "section": "integrations",
            "data": {
                "hubspot": {
                    "connected": True,
                    "sync_enabled": True,
                    "last_sync": "2024-01-20T00:00:00Z",
                },
                "avoma": {
                    "connected": True,
                    "auto_import": True,
                },
            },
        }

    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform backup section for export."""
        # Backup sections are already in final format
        return record

    async def _export_json(
        self,
        filename: str,
        on_progress=None,
    ) -> str:
        """Export full backup as single JSON file."""
        filepath = self.export_dir / f"{filename}.json"
        backup_data = {
            "backup_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "export_type": "full_backup",
            "sections": {},
        }

        processed = 0
        async for section in self.fetch_data(
            self.job.filters or {}, self.job.record_ids or []
        ):
            section_name = section["section"]
            backup_data["sections"][section_name] = section["data"]
            processed += 1
            if on_progress:
                on_progress(processed, 10)  # Approximate 10 sections

        # Add metadata
        backup_data["metadata"] = {
            "total_sections": len(backup_data["sections"]),
            "sections_included": list(backup_data["sections"].keys()),
        }

        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(backup_data, indent=2, default=str))

        return str(filepath)

    async def _export_zip(
        self,
        filename: str,
        on_progress=None,
    ) -> str:
        """Export full backup as ZIP archive.

        Creates a structured archive with:
        - manifest.json - Backup metadata and index
        - data/ - JSON files for each data section
        - files/ - Content files (PDFs, PPTXs)
        """
        filepath = self.export_dir / f"{filename}.zip"
        temp_dir = self.export_dir / f"backup_{filename}"

        # Create temp directory structure
        data_dir = temp_dir / "data"
        files_dir = temp_dir / "files"

        for dir_path in [temp_dir, data_dir, files_dir]:
            if not await aiofiles.os.path.exists(dir_path):
                await aiofiles.os.makedirs(dir_path)

        try:
            sections_manifest = []
            processed = 0

            async for section in self.fetch_data(
                self.job.filters or {}, self.job.record_ids or []
            ):
                section_name = section["section"]
                section_data = section["data"]

                # Write section data to separate file
                section_file = data_dir / f"{section_name}.json"
                async with aiofiles.open(section_file, "w") as f:
                    await f.write(json.dumps(section_data, indent=2, default=str))

                # Track in manifest
                record_count = (
                    len(section_data) if isinstance(section_data, list) else 1
                )
                sections_manifest.append({
                    "name": section_name,
                    "file": f"data/{section_name}.json",
                    "record_count": record_count,
                })

                processed += 1
                if on_progress:
                    on_progress(processed, 10)

            # Create manifest
            manifest = {
                "backup_version": "1.0",
                "format": "zip_archive",
                "exported_at": datetime.utcnow().isoformat(),
                "organization_id": self.job.organization_id,
                "sections": sections_manifest,
                "total_sections": len(sections_manifest),
                "restore_instructions": {
                    "version_required": "1.0+",
                    "restore_order": [
                        "organization",
                        "users",
                        "teams",
                        "companies",
                        "prospects",
                        "templates",
                        "transcripts",
                        "content",
                        "coaching_reports",
                        "integrations",
                    ],
                },
            }

            manifest_file = temp_dir / "manifest.json"
            async with aiofiles.open(manifest_file, "w") as f:
                await f.write(json.dumps(manifest, indent=2))

            # Create README
            readme_file = temp_dir / "README.txt"
            async with aiofiles.open(readme_file, "w") as f:
                await f.write(
                    f"""Sales OS Full Backup
=====================

Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This archive contains a full backup of your Sales OS account.

Contents:
- manifest.json: Backup metadata and section index
- data/: JSON files for each data section
- files/: Content files (PDFs, PPTXs) if included

To restore this backup:
1. Go to Settings > Import/Export
2. Select "Restore from Backup"
3. Upload this ZIP file
4. Follow the restore wizard

For support, contact support@sales-os.example.com
"""
                )

            # Create ZIP archive
            with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add manifest and readme
                zf.write(manifest_file, "manifest.json")
                zf.write(readme_file, "README.txt")

                # Add all data files
                for section_file in data_dir.iterdir():
                    zf.write(section_file, f"data/{section_file.name}")

                # Add content files (in real implementation)
                # for content_file in files_dir.iterdir():
                #     zf.write(content_file, f"files/{content_file.name}")

            return str(filepath)

        finally:
            # Cleanup temp directory
            import shutil
            if await aiofiles.os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
