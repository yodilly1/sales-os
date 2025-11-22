"""Import service orchestrator."""

import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
from pathlib import Path
import aiofiles
import aiofiles.os
import uuid

from app.core.config import settings
from app.models.export_import import (
    ImportJob,
    ImportType,
    ImportStatus,
    ImportJobCreate,
    ImportJobSchema,
    ImportProgress,
    ImportValidationResult,
    FieldMapping,
)
from .base import BaseImporter
from .prospect_importer import ProspectImporter
from .transcript_importer import TranscriptImporter
from .template_importer import TemplateImporter


class ImportService:
    """Service for managing data imports.

    Orchestrates the import process including:
    - File upload handling
    - Validation and preview
    - Field mapping suggestions
    - Async processing for large imports
    - Error reporting
    """

    # Map import types to importer classes
    IMPORTERS: Dict[ImportType, Type[BaseImporter]] = {
        ImportType.PROSPECTS: ProspectImporter,
        ImportType.TRANSCRIPTS: TranscriptImporter,
        ImportType.TEMPLATES: TemplateImporter,
    }

    def __init__(self):
        """Initialize import service."""
        self.upload_dir = Path(settings.export_temp_dir) / "uploads"

    async def _ensure_upload_dir(self):
        """Create upload directory if it doesn't exist."""
        if not await aiofiles.os.path.exists(self.upload_dir):
            await aiofiles.os.makedirs(self.upload_dir)

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Handle file upload for import.

        Args:
            file_content: Raw file content
            filename: Original filename
            user_id: User uploading the file
            organization_id: Organization context

        Returns:
            Upload result with file info
        """
        await self._ensure_upload_dir()

        # Validate file size
        max_size = settings.import_max_file_size_mb * 1024 * 1024
        if len(file_content) > max_size:
            raise ValueError(
                f"File too large. Maximum size: {settings.import_max_file_size_mb}MB"
            )

        # Validate file extension
        path = Path(filename)
        valid_extensions = [".csv", ".json"]
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Invalid file type. Supported types: {', '.join(valid_extensions)}"
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{path.suffix.lower()}"
        file_path = self.upload_dir / safe_filename

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        return {
            "file_id": file_id,
            "original_filename": filename,
            "file_path": str(file_path),
            "file_size_bytes": len(file_content),
            "file_type": path.suffix.lower(),
        }

    async def get_column_preview(
        self,
        file_path: str,
        import_type: ImportType,
    ) -> Dict[str, Any]:
        """Get column preview and mapping suggestions.

        Args:
            file_path: Path to uploaded file
            import_type: Type of import

        Returns:
            Preview with columns, sample data, and mapping suggestions
        """
        importer_class = self.IMPORTERS.get(import_type)
        if not importer_class:
            raise ValueError(f"Unsupported import type: {import_type}")

        # Read first few rows
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            columns, sample_rows = await self._preview_csv(file_path)
        elif path.suffix.lower() == ".json":
            columns, sample_rows = await self._preview_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        # Get mapping suggestions
        temp_job = ImportJob(
            id="temp",
            import_type=import_type,
            user_id="temp",
            organization_id="temp",
        )
        importer = importer_class(temp_job)

        # Get field mapping suggestions
        suggestions = {}
        if hasattr(importer, "suggest_field_mapping"):
            suggestions = importer.suggest_field_mapping(columns)
        else:
            # Default suggestions based on required/optional fields
            all_fields = importer.required_fields + importer.optional_fields
            for col in columns:
                normalized = col.lower().strip().replace(" ", "_")
                if normalized in all_fields:
                    suggestions[col] = {
                        "target_field": normalized,
                        "confidence": "high",
                    }

        return {
            "columns": columns,
            "sample_rows": sample_rows[:5],
            "total_rows": len(sample_rows),
            "required_fields": importer.required_fields,
            "optional_fields": importer.optional_fields,
            "mapping_suggestions": suggestions,
        }

    async def _preview_csv(self, file_path: str) -> tuple:
        """Preview CSV file."""
        import csv

        async with aiofiles.open(file_path, "r", encoding="utf-8-sig") as f:
            content = await f.read()

        lines = content.splitlines()
        reader = csv.DictReader(lines)

        columns = reader.fieldnames or []
        sample_rows = []

        for row in reader:
            sample_rows.append(dict(row))
            if len(sample_rows) >= 100:  # Limit preview
                break

        return list(columns), sample_rows

    async def _preview_json(self, file_path: str) -> tuple:
        """Preview JSON file."""
        import json

        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()

        data = json.loads(content)

        # Handle various JSON structures
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict) and "records" in data:
            rows = data["records"]
        elif isinstance(data, dict):
            rows = [data]
        else:
            rows = []

        # Get columns from first row
        columns = list(rows[0].keys()) if rows else []

        return columns, rows[:100]

    async def create_import_job(
        self,
        file_path: str,
        original_filename: str,
        import_type: ImportType,
        field_mapping: Dict[str, Any],
        user_id: str,
        organization_id: str,
    ) -> ImportJobSchema:
        """Create a new import job.

        Args:
            file_path: Path to uploaded file
            original_filename: Original filename
            import_type: Type of import
            field_mapping: Field mapping configuration
            user_id: User creating the import
            organization_id: Organization context

        Returns:
            Created import job details
        """
        # Validate import type
        if import_type not in self.IMPORTERS:
            raise ValueError(f"Unsupported import type: {import_type}")

        # TODO: Save job to database
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Count rows
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            _, rows = await self._preview_csv(file_path)
            total_rows = len(rows)
        else:
            _, rows = await self._preview_json(file_path)
            total_rows = len(rows)

        job = ImportJob(
            id=job_id,
            import_type=import_type,
            status=ImportStatus.PENDING,
            original_filename=original_filename,
            file_path=file_path,
            file_size_bytes=os.path.getsize(file_path),
            field_mapping=field_mapping,
            total_records=total_rows,
            user_id=user_id,
            organization_id=organization_id,
            created_at=now,
            updated_at=now,
        )

        return ImportJobSchema(
            id=job_id,
            import_type=import_type,
            status=ImportStatus.PENDING,
            original_filename=original_filename,
            field_mapping=field_mapping,
            total_records=total_rows,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            progress_percent=0.0,
            imported_ids=[],
            errors=[],
            user_id=user_id,
            organization_id=organization_id,
            created_at=now,
            updated_at=now,
        )

    async def validate_import(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> ImportValidationResult:
        """Validate an import job before processing.

        Args:
            job_id: Import job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            Validation result
        """
        # TODO: Fetch job from database
        # For now, return mock validation
        return ImportValidationResult(
            is_valid=True,
            total_rows=10,
            valid_rows=10,
            invalid_rows=0,
            errors=[],
            warnings=[],
            sample_data=[],
        )

    async def execute_import(
        self,
        job_id: str,
        file_path: str,
        import_type: ImportType,
        field_mapping: Dict[str, Any],
        user_id: str,
        organization_id: str,
    ) -> ImportJobSchema:
        """Execute an import job synchronously.

        Args:
            job_id: Import job ID
            file_path: Path to import file
            import_type: Type of import
            field_mapping: Field mapping
            user_id: User context
            organization_id: Organization context

        Returns:
            Completed import job with results
        """
        # Create job instance
        job = ImportJob(
            id=job_id,
            import_type=import_type,
            status=ImportStatus.PROCESSING,
            file_path=file_path,
            field_mapping=field_mapping,
            user_id=user_id,
            organization_id=organization_id,
        )

        # Get importer
        importer_class = self.IMPORTERS.get(import_type)
        if not importer_class:
            raise ValueError(f"No importer for type: {import_type}")

        importer = importer_class(job)

        # Progress callback
        def on_progress(processed: int, total: int, successful: int, failed: int):
            job.processed_records = processed
            job.total_records = total
            job.successful_records = successful
            job.failed_records = failed
            job.progress_percent = (processed / total * 100) if total > 0 else 0

        try:
            # Execute import
            successful, failed, imported_ids = await importer.execute_import(
                file_path, on_progress=on_progress
            )

            # Update job status
            if failed == 0:
                job.status = ImportStatus.COMPLETED
            elif successful > 0:
                job.status = ImportStatus.COMPLETED_WITH_ERRORS
            else:
                job.status = ImportStatus.FAILED

            job.successful_records = successful
            job.failed_records = failed
            job.imported_ids = imported_ids
            job.errors = [
                {"row_number": e.row_number, "field": e.field, "error": e.error}
                for e in importer.errors
            ]

        except Exception as e:
            job.status = ImportStatus.FAILED
            job.error_message = str(e)

        # TODO: Save job to database

        return ImportJobSchema(
            id=job.id,
            import_type=job.import_type,
            status=job.status,
            original_filename=job.original_filename,
            field_mapping=job.field_mapping or {},
            total_records=job.total_records or 0,
            processed_records=job.processed_records or 0,
            successful_records=job.successful_records or 0,
            failed_records=job.failed_records or 0,
            progress_percent=100.0,
            imported_ids=job.imported_ids or [],
            errors=job.errors or [],
            error_message=job.error_message,
            user_id=job.user_id,
            organization_id=job.organization_id,
            created_at=job.created_at or datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def get_import_progress(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> ImportProgress:
        """Get progress of an import job.

        Args:
            job_id: Import job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            Current progress status
        """
        # TODO: Fetch from database
        return ImportProgress(
            job_id=job_id,
            status=ImportStatus.COMPLETED,
            progress_percent=100.0,
            processed_records=10,
            total_records=10,
            successful_records=10,
            failed_records=0,
            message="Import completed successfully",
        )

    async def list_imports(
        self,
        user_id: str,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ImportJobSchema]:
        """List import jobs for a user.

        Args:
            user_id: User ID
            organization_id: Organization context
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of import jobs
        """
        # TODO: Query database
        return []

    async def cleanup_upload(self, file_path: str) -> bool:
        """Clean up uploaded file after import.

        Args:
            file_path: Path to uploaded file

        Returns:
            True if cleaned up, False otherwise
        """
        try:
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                return True
        except Exception:
            pass
        return False

    def get_supported_types(self) -> List[Dict[str, Any]]:
        """Get list of supported import types with details.

        Returns:
            List of import type details
        """
        result = []
        for import_type, importer_class in self.IMPORTERS.items():
            temp_job = ImportJob(
                id="temp",
                import_type=import_type,
                user_id="temp",
                organization_id="temp",
            )
            importer = importer_class(temp_job)

            result.append({
                "type": import_type.value,
                "required_fields": importer.required_fields,
                "optional_fields": importer.optional_fields,
                "supported_formats": ["csv", "json"],
            })

        return result
