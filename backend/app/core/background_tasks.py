"""Background task handling for large exports and imports.

This module provides utilities for:
- Tracking long-running jobs
- Progress reporting
- Job status persistence
- Cleanup of completed jobs
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import uuid


class JobStatus(str, Enum):
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobProgress:
    """Track progress of a background job."""

    def __init__(
        self,
        job_id: str,
        job_type: str,
        total_items: int = 0,
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.total_items = total_items
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.last_updated: datetime = datetime.utcnow()

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    def start(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

    def update(
        self,
        processed: int,
        successful: int = 0,
        failed: int = 0,
    ):
        """Update progress."""
        self.processed_items = processed
        self.successful_items = successful
        self.failed_items = failed
        self.last_updated = datetime.utcnow()

    def complete(self, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.result = result

    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.error_message = error_message

    def cancel(self):
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "result": self.result,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_updated": self.last_updated.isoformat(),
        }


class BackgroundJobManager:
    """Manager for background jobs.

    In-memory implementation for development.
    For production, use Redis or database for persistence.
    """

    def __init__(self):
        self._jobs: Dict[str, JobProgress] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._cleanup_interval = 3600  # 1 hour
        self._retention_hours = 24

    def create_job(
        self,
        job_type: str,
        total_items: int = 0,
    ) -> JobProgress:
        """Create a new background job.

        Args:
            job_type: Type of job (export, import, etc.)
            total_items: Total items to process

        Returns:
            JobProgress instance
        """
        job_id = str(uuid.uuid4())
        job = JobProgress(job_id, job_type, total_items)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[JobProgress]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    async def run_job(
        self,
        job: JobProgress,
        task_fn: Callable[[JobProgress], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Run a job asynchronously.

        Args:
            job: JobProgress instance
            task_fn: Async function to execute
        """
        job.start()

        try:
            result = await task_fn(job)
            job.complete(result)
        except asyncio.CancelledError:
            job.cancel()
        except Exception as e:
            job.fail(str(e))

    def start_job_task(
        self,
        job: JobProgress,
        task_fn: Callable[[JobProgress], Awaitable[Dict[str, Any]]],
    ) -> asyncio.Task:
        """Start a job as a background task.

        Args:
            job: JobProgress instance
            task_fn: Async function to execute

        Returns:
            asyncio.Task
        """
        task = asyncio.create_task(self.run_job(job, task_fn))
        self._tasks[job.job_id] = task
        return task

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or not running
        """
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True

        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.cancel()
            return True

        return False

    def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> list:
        """List jobs with optional filtering.

        Args:
            job_type: Filter by job type
            status: Filter by status
            limit: Maximum results

        Returns:
            List of job dictionaries
        """
        jobs = list(self._jobs.values())

        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by last_updated descending
        jobs.sort(key=lambda j: j.last_updated, reverse=True)

        return [j.to_dict() for j in jobs[:limit]]

    async def cleanup_old_jobs(self) -> int:
        """Remove completed/failed jobs older than retention period.

        Returns:
            Number of jobs cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=self._retention_hours)
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                if job.completed_at and job.completed_at < cutoff:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]
            if job_id in self._tasks:
                del self._tasks[job_id]

        return len(to_remove)


# Global job manager instance
job_manager = BackgroundJobManager()


def get_job_manager() -> BackgroundJobManager:
    """Get the global job manager instance."""
    return job_manager


# Utility functions for export/import jobs
async def run_export_job(
    job: JobProgress,
    export_fn: Callable,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """Wrapper for running export jobs with progress tracking.

    Args:
        job: JobProgress instance
        export_fn: Export function to call
        *args, **kwargs: Arguments for export function

    Returns:
        Export result
    """

    def progress_callback(processed: int, total: int):
        job.total_items = total
        job.update(processed, successful=processed)

    kwargs["on_progress"] = progress_callback
    result = await export_fn(*args, **kwargs)

    return {"file_path": result}


async def run_import_job(
    job: JobProgress,
    import_fn: Callable,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """Wrapper for running import jobs with progress tracking.

    Args:
        job: JobProgress instance
        import_fn: Import function to call
        *args, **kwargs: Arguments for import function

    Returns:
        Import result
    """

    def progress_callback(processed: int, total: int, successful: int, failed: int):
        job.total_items = total
        job.update(processed, successful, failed)

    kwargs["on_progress"] = progress_callback
    successful, failed, imported_ids = await import_fn(*args, **kwargs)

    return {
        "successful": successful,
        "failed": failed,
        "imported_ids": imported_ids,
    }
