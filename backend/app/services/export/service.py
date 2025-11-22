"""Export service orchestrator."""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Type
from pathlib import Path
import aiofiles.os

from app.core.config import settings
from app.models.export_import import (
    ExportJob,
    ExportType,
    ExportFormat,
    ExportStatus,
    ExportJobCreate,
    ExportJobSchema,
    ExportProgress,
)
from .base import BaseExporter
from .transcript_exporter import TranscriptExporter
from .content_exporter import ContentExporter
from .prospect_exporter import ProspectExporter
from .coaching_exporter import CoachingExporter
from .backup_exporter import BackupExporter


class ExportService:
    """Service for managing data exports.

    Orchestrates the export process including:
    - Job creation and tracking
    - Async processing for large exports
    - File management and cleanup
    - Progress reporting
    """

    # Map export types to exporter classes
    EXPORTERS: Dict[ExportType, Type[BaseExporter]] = {
        ExportType.TRANSCRIPTS: TranscriptExporter,
        ExportType.CONTENT: ContentExporter,
        ExportType.PROSPECTS: ProspectExporter,
        ExportType.COACHING: CoachingExporter,
        ExportType.FULL_BACKUP: BackupExporter,
    }

    def __init__(self):
        """Initialize export service."""
        self.export_dir = Path(settings.export_temp_dir)

    async def create_export_job(
        self,
        request: ExportJobCreate,
        user_id: str,
        organization_id: str,
    ) -> ExportJobSchema:
        """Create a new export job.

        Args:
            request: Export job configuration
            user_id: User requesting the export
            organization_id: Organization context

        Returns:
            Created export job details
        """
        # Validate export type and format combination
        exporter_class = self.EXPORTERS.get(request.export_type)
        if not exporter_class:
            raise ValueError(f"Unsupported export type: {request.export_type}")

        # Create a temporary job instance to check supported formats
        temp_job = ExportJob(
            id="temp",
            export_type=request.export_type,
            export_format=request.export_format,
            user_id=user_id,
            organization_id=organization_id,
        )
        temp_exporter = exporter_class(temp_job)

        if request.export_format not in temp_exporter.supported_formats:
            raise ValueError(
                f"Format {request.export_format} not supported for {request.export_type}. "
                f"Supported formats: {[f.value for f in temp_exporter.supported_formats]}"
            )

        # TODO: Create job in database
        # For now, create in-memory job
        import uuid

        job_id = str(uuid.uuid4())
        now = datetime.utcnow()

        job = ExportJob(
            id=job_id,
            export_type=request.export_type,
            export_format=request.export_format,
            status=ExportStatus.PENDING,
            filters=request.filters,
            record_ids=request.record_ids,
            user_id=user_id,
            organization_id=organization_id,
            created_at=now,
            updated_at=now,
        )

        return ExportJobSchema(
            id=job_id,
            export_type=request.export_type,
            export_format=request.export_format,
            status=ExportStatus.PENDING,
            filters=request.filters,
            record_ids=request.record_ids,
            total_records=0,
            processed_records=0,
            progress_percent=0.0,
            user_id=user_id,
            organization_id=organization_id,
            created_at=now,
            updated_at=now,
        )

    async def execute_export(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> ExportJobSchema:
        """Execute an export job synchronously.

        For small exports, this can be called directly.
        For large exports, use execute_export_async.

        Args:
            job_id: Export job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            Completed export job with download URL
        """
        # TODO: Fetch job from database
        # For now, create mock job
        job = ExportJob(
            id=job_id,
            export_type=ExportType.TRANSCRIPTS,
            export_format=ExportFormat.JSON,
            status=ExportStatus.PROCESSING,
            filters={},
            record_ids=[],
            user_id=user_id,
            organization_id=organization_id,
        )

        # Get exporter
        exporter_class = self.EXPORTERS.get(job.export_type)
        if not exporter_class:
            raise ValueError(f"No exporter for type: {job.export_type}")

        exporter = exporter_class(job)

        # Progress callback
        def on_progress(processed: int, total: int):
            job.processed_records = processed
            job.total_records = total
            job.progress_percent = (processed / total * 100) if total > 0 else 0

        try:
            # Execute export
            file_path = await exporter.export(on_progress=on_progress)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(hours=settings.export_retention_hours)

            # Generate download URL (in production, use signed URLs)
            download_url = f"/api/v1/export/download/{job_id}"

            # Update job status
            job.status = ExportStatus.COMPLETED
            job.file_path = file_path
            job.file_size_bytes = file_size
            job.download_url = download_url
            job.expires_at = expires_at.isoformat()

            if exporter.errors:
                # Partial success
                job.error_details = {"row_errors": exporter.errors}

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error_message = str(e)

        # TODO: Save job to database

        return ExportJobSchema(
            id=job.id,
            export_type=job.export_type,
            export_format=job.export_format,
            status=job.status,
            filters=job.filters or {},
            record_ids=job.record_ids or [],
            total_records=job.total_records or 0,
            processed_records=job.processed_records or 0,
            progress_percent=job.progress_percent or 0.0,
            file_path=job.file_path,
            file_size_bytes=job.file_size_bytes,
            download_url=job.download_url,
            expires_at=job.expires_at,
            error_message=job.error_message,
            user_id=job.user_id,
            organization_id=job.organization_id,
            created_at=job.created_at or datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def start_async_export(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> ExportProgress:
        """Start an export job asynchronously.

        For large exports that should run in the background.
        Use get_export_progress to check status.

        Args:
            job_id: Export job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            Initial progress status
        """
        # TODO: Queue job for background processing with Celery
        # For now, return initial status
        return ExportProgress(
            job_id=job_id,
            status=ExportStatus.PROCESSING,
            progress_percent=0.0,
            processed_records=0,
            total_records=0,
            message="Export started. Processing in background...",
        )

    async def get_export_progress(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> ExportProgress:
        """Get progress of an export job.

        Args:
            job_id: Export job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            Current progress status
        """
        # TODO: Fetch from database or cache
        return ExportProgress(
            job_id=job_id,
            status=ExportStatus.COMPLETED,
            progress_percent=100.0,
            processed_records=10,
            total_records=10,
            message="Export completed successfully",
        )

    async def get_download_path(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> Optional[str]:
        """Get the file path for a completed export.

        Args:
            job_id: Export job ID
            user_id: User context (for authorization)
            organization_id: Organization context

        Returns:
            File path if export is ready, None otherwise
        """
        # TODO: Fetch from database, verify authorization
        # For now, return mock path
        return str(self.export_dir / f"export_{job_id}.json")

    async def cleanup_expired_exports(self) -> int:
        """Clean up expired export files.

        Should be run periodically (e.g., hourly).

        Returns:
            Number of files cleaned up
        """
        # TODO: Query database for expired jobs and delete files
        cleaned = 0

        if await aiofiles.os.path.exists(self.export_dir):
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=settings.export_retention_hours)

            for filename in os.listdir(self.export_dir):
                filepath = self.export_dir / filename
                if os.path.isfile(filepath):
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff:
                        os.remove(filepath)
                        cleaned += 1

        return cleaned

    async def list_exports(
        self,
        user_id: str,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExportJobSchema]:
        """List export jobs for a user.

        Args:
            user_id: User ID
            organization_id: Organization context
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of export jobs
        """
        # TODO: Query database
        return []

    async def cancel_export(
        self,
        job_id: str,
        user_id: str,
        organization_id: str,
    ) -> bool:
        """Cancel a pending or processing export job.

        Args:
            job_id: Export job ID
            user_id: User context
            organization_id: Organization context

        Returns:
            True if cancelled, False if not cancellable
        """
        # TODO: Update database, signal background worker
        return True

    def get_supported_formats(self, export_type: ExportType) -> List[ExportFormat]:
        """Get supported formats for an export type.

        Args:
            export_type: Type of export

        Returns:
            List of supported formats
        """
        exporter_class = self.EXPORTERS.get(export_type)
        if not exporter_class:
            return []

        # Create temporary instance to get supported formats
        temp_job = ExportJob(
            id="temp",
            export_type=export_type,
            export_format=ExportFormat.JSON,
            user_id="temp",
            organization_id="temp",
        )
        exporter = exporter_class(temp_job)
        return exporter.supported_formats
