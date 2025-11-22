"""File processing queue service for background file processing."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import StorageClient, get_storage_client
from app.models.file import (
    File,
    FileProcessingJob,
    FileStatus,
    FileType,
    ProcessingJobResponse,
    ProcessingStatus,
)


class ProcessingError(Exception):
    """Exception raised during file processing."""

    pass


# Type alias for processor functions
ProcessorFunc = Callable[[File, bytes, dict], Coroutine[Any, Any, dict]]


class FileProcessingService:
    """Service for managing file processing queue.

    Handles queueing, executing, and tracking file processing jobs.
    Uses database-backed queue for reliability and supports multiple workers.
    """

    # Registry of processing handlers
    _processors: dict[str, ProcessorFunc] = {}

    def __init__(
        self,
        storage: Optional[StorageClient] = None,
        max_concurrent_jobs: int = 5,
        retry_delay_seconds: int = 60,
    ):
        """Initialize processing service.

        Args:
            storage: Storage client instance
            max_concurrent_jobs: Maximum concurrent processing jobs
            retry_delay_seconds: Delay between retry attempts
        """
        self.storage = storage or get_storage_client()
        self.max_concurrent_jobs = max_concurrent_jobs
        self.retry_delay_seconds = retry_delay_seconds
        self._running = False
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)

    @classmethod
    def register_processor(cls, job_type: str, processor: ProcessorFunc) -> None:
        """Register a processor function for a job type.

        Args:
            job_type: Type of processing job
            processor: Async function to process the file
        """
        cls._processors[job_type] = processor

    @classmethod
    def get_processor(cls, job_type: str) -> Optional[ProcessorFunc]:
        """Get a registered processor.

        Args:
            job_type: Type of processing job

        Returns:
            Processor function or None
        """
        return cls._processors.get(job_type)

    async def queue_job(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
        job_type: str,
        priority: int = 0,
        input_data: Optional[dict] = None,
        max_attempts: int = 3,
    ) -> ProcessingJobResponse:
        """Queue a new processing job.

        Args:
            db: Database session
            file_id: File ID to process
            job_type: Type of processing job
            priority: Job priority (higher = more priority)
            input_data: Optional input data for the job
            max_attempts: Maximum retry attempts

        Returns:
            ProcessingJobResponse with job details

        Raises:
            ProcessingError: If file not found or invalid state
        """
        # Verify file exists and is in correct state
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise ProcessingError(f"File not found: {file_id}")

        if file_record.status != FileStatus.UPLOADED:
            raise ProcessingError(
                f"File is not ready for processing: {file_record.status}"
            )

        # Check if same job type already queued
        existing = await db.execute(
            select(FileProcessingJob).where(
                FileProcessingJob.file_id == file_id,
                FileProcessingJob.job_type == job_type,
                FileProcessingJob.status.in_([ProcessingStatus.QUEUED, ProcessingStatus.RUNNING]),
            )
        )
        if existing.scalar_one_or_none():
            raise ProcessingError(f"Job already queued: {job_type}")

        # Create job record
        job = FileProcessingJob(
            file_id=file_id,
            job_type=job_type,
            status=ProcessingStatus.QUEUED,
            priority=priority,
            input_data=input_data,
            max_attempts=max_attempts,
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        return ProcessingJobResponse.model_validate(job)

    async def get_job_status(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> ProcessingJobResponse:
        """Get the status of a processing job.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            ProcessingJobResponse with job status

        Raises:
            ProcessingError: If job not found
        """
        result = await db.execute(
            select(FileProcessingJob).where(FileProcessingJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job is None:
            raise ProcessingError(f"Job not found: {job_id}")

        return ProcessingJobResponse.model_validate(job)

    async def get_file_jobs(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
    ) -> list[ProcessingJobResponse]:
        """Get all processing jobs for a file.

        Args:
            db: Database session
            file_id: File ID

        Returns:
            List of ProcessingJobResponse
        """
        result = await db.execute(
            select(FileProcessingJob)
            .where(FileProcessingJob.file_id == file_id)
            .order_by(FileProcessingJob.queued_at.desc())
        )
        jobs = result.scalars().all()

        return [ProcessingJobResponse.model_validate(job) for job in jobs]

    async def cancel_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> ProcessingJobResponse:
        """Cancel a queued processing job.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            ProcessingJobResponse with updated status

        Raises:
            ProcessingError: If job not found or cannot be cancelled
        """
        result = await db.execute(
            select(FileProcessingJob).where(FileProcessingJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job is None:
            raise ProcessingError(f"Job not found: {job_id}")

        if job.status == ProcessingStatus.RUNNING:
            raise ProcessingError("Cannot cancel running job")

        if job.status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED):
            raise ProcessingError(f"Job already finished: {job.status}")

        job.status = ProcessingStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(job)

        return ProcessingJobResponse.model_validate(job)

    async def _get_next_job(self, db: AsyncSession) -> Optional[FileProcessingJob]:
        """Get the next job to process.

        Prioritizes by priority descending, then by queued_at ascending.

        Args:
            db: Database session

        Returns:
            Next job to process or None
        """
        # Get queued jobs or jobs ready for retry
        now = datetime.utcnow()

        result = await db.execute(
            select(FileProcessingJob)
            .where(
                (FileProcessingJob.status == ProcessingStatus.QUEUED)
                | (
                    (FileProcessingJob.status == ProcessingStatus.FAILED)
                    & (FileProcessingJob.attempts < FileProcessingJob.max_attempts)
                    & (
                        (FileProcessingJob.next_retry_at.is_(None))
                        | (FileProcessingJob.next_retry_at <= now)
                    )
                )
            )
            .order_by(
                FileProcessingJob.priority.desc(),
                FileProcessingJob.queued_at.asc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def _process_job(self, db: AsyncSession, job: FileProcessingJob) -> None:
        """Process a single job.

        Args:
            db: Database session
            job: Job to process
        """
        # Mark job as running
        job.status = ProcessingStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.attempts += 1
        await db.commit()

        # Get file record
        result = await db.execute(select(File).where(File.id == job.file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            job.status = ProcessingStatus.FAILED
            job.error_message = "File not found"
            job.completed_at = datetime.utcnow()
            await db.commit()
            return

        # Update file status
        file_record.status = FileStatus.PROCESSING
        await db.commit()

        try:
            # Get processor
            processor = self.get_processor(job.job_type)
            if processor is None:
                raise ProcessingError(f"No processor registered for: {job.job_type}")

            # Download file content
            file_content = await self.storage.download_file(file_record.storage_key)

            # Run processor
            output_data = await processor(
                file_record,
                file_content,
                job.input_data or {},
            )

            # Mark job as completed
            job.status = ProcessingStatus.COMPLETED
            job.output_data = output_data
            job.completed_at = datetime.utcnow()

            # Update file status
            file_record.status = FileStatus.COMPLETED
            file_record.processed_at = datetime.utcnow()

        except Exception as e:
            # Handle failure
            job.error_message = str(e)

            if job.attempts >= job.max_attempts:
                job.status = ProcessingStatus.FAILED
                job.completed_at = datetime.utcnow()
                file_record.status = FileStatus.FAILED
                file_record.error_message = f"Processing failed after {job.attempts} attempts: {e}"
            else:
                # Schedule retry
                job.status = ProcessingStatus.FAILED
                job.next_retry_at = datetime.utcnow() + timedelta(
                    seconds=self.retry_delay_seconds * job.attempts
                )
                file_record.status = FileStatus.UPLOADED  # Reset to uploaded for retry

        await db.commit()

    async def process_pending_jobs(self, db: AsyncSession) -> int:
        """Process all pending jobs.

        Runs until no more jobs are available.

        Args:
            db: Database session

        Returns:
            Number of jobs processed
        """
        processed = 0

        while True:
            async with self._semaphore:
                job = await self._get_next_job(db)
                if job is None:
                    break

                await self._process_job(db, job)
                processed += 1

        return processed

    async def start_worker(
        self,
        db_session_factory: Callable[[], AsyncSession],
        poll_interval: float = 5.0,
    ) -> None:
        """Start the background worker.

        Continuously polls for and processes jobs.

        Args:
            db_session_factory: Factory function to create database sessions
            poll_interval: Seconds between polling for new jobs
        """
        self._running = True

        while self._running:
            try:
                async with db_session_factory() as db:
                    job = await self._get_next_job(db)
                    if job:
                        await self._process_job(db, job)
                    else:
                        await asyncio.sleep(poll_interval)
            except Exception as e:
                # Log error and continue
                print(f"Worker error: {e}")
                await asyncio.sleep(poll_interval)

    def stop_worker(self) -> None:
        """Stop the background worker."""
        self._running = False

    async def get_queue_stats(self, db: AsyncSession) -> dict:
        """Get queue statistics.

        Args:
            db: Database session

        Returns:
            Dict with queue statistics
        """
        from sqlalchemy import func

        # Count jobs by status
        result = await db.execute(
            select(FileProcessingJob.status, func.count(FileProcessingJob.id))
            .group_by(FileProcessingJob.status)
        )
        status_counts = {str(status): count for status, count in result.all()}

        # Get average processing time for completed jobs
        result = await db.execute(
            select(func.avg(
                func.extract("epoch", FileProcessingJob.completed_at) -
                func.extract("epoch", FileProcessingJob.started_at)
            ))
            .where(FileProcessingJob.status == ProcessingStatus.COMPLETED)
        )
        avg_processing_time = result.scalar() or 0

        return {
            "status_counts": status_counts,
            "avg_processing_time_seconds": round(avg_processing_time, 2),
            "is_running": self._running,
            "max_concurrent_jobs": self.max_concurrent_jobs,
        }


# Built-in processors


async def _validate_transcript_processor(
    file: File,
    content: bytes,
    input_data: dict,
) -> dict:
    """Validate and parse transcript file."""
    from app.services.files.validation import FileValidationService

    validator = FileValidationService()
    result = await validator.validate_content(content, file.original_filename, file.file_type)

    if not result.is_valid:
        raise ProcessingError(
            f"Transcript validation failed: {[e.message for e in result.errors]}"
        )

    return {
        "validation": {
            "is_valid": result.is_valid,
            "warnings": result.warnings,
            "file_info": result.file_info,
        }
    }


async def _validate_data_processor(
    file: File,
    content: bytes,
    input_data: dict,
) -> dict:
    """Validate and parse data file (CSV, XLSX)."""
    from app.services.files.validation import FileValidationService

    validator = FileValidationService()
    result = await validator.validate_content(content, file.original_filename, file.file_type)

    if not result.is_valid:
        raise ProcessingError(
            f"Data file validation failed: {[e.message for e in result.errors]}"
        )

    return {
        "validation": {
            "is_valid": result.is_valid,
            "warnings": result.warnings,
            "file_info": result.file_info,
        }
    }


async def _validate_asset_processor(
    file: File,
    content: bytes,
    input_data: dict,
) -> dict:
    """Validate asset file (images, PDFs)."""
    from app.services.files.validation import FileValidationService

    validator = FileValidationService()
    result = await validator.validate_content(content, file.original_filename, file.file_type)

    if not result.is_valid:
        raise ProcessingError(
            f"Asset validation failed: {[e.message for e in result.errors]}"
        )

    return {
        "validation": {
            "is_valid": result.is_valid,
            "warnings": result.warnings,
            "file_info": result.file_info,
        }
    }


# Register built-in processors
FileProcessingService.register_processor("validate_transcript", _validate_transcript_processor)
FileProcessingService.register_processor("validate_data", _validate_data_processor)
FileProcessingService.register_processor("validate_asset", _validate_asset_processor)
