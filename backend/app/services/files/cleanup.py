"""File cleanup service for removing expired and orphaned files."""

import asyncio
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import StorageClient, get_storage_client
from app.models.file import File, FileChunk, FileProcessingJob, FileStatus


class CleanupError(Exception):
    """Exception raised during cleanup operations."""

    pass


class FileCleanupService:
    """Service for cleaning up expired and orphaned files.

    Handles:
    - Expired temporary files
    - Failed/abandoned multipart uploads
    - Orphaned storage files
    - Local temporary chunk files
    """

    def __init__(
        self,
        storage: Optional[StorageClient] = None,
        temp_dir: Optional[Path] = None,
    ):
        """Initialize cleanup service.

        Args:
            storage: Storage client instance
            temp_dir: Local temporary directory path
        """
        self.storage = storage or get_storage_client()
        self.temp_dir = temp_dir or Path(settings.upload_temp_dir)
        self._running = False

    async def cleanup_expired_files(self, db: AsyncSession) -> dict:
        """Remove expired temporary files.

        Args:
            db: Database session

        Returns:
            Dict with cleanup statistics
        """
        now = datetime.utcnow()
        deleted_count = 0
        storage_errors = []

        # Find expired files
        result = await db.execute(
            select(File).where(
                and_(
                    File.is_temporary == True,
                    File.expires_at.isnot(None),
                    File.expires_at <= now,
                )
            )
        )
        expired_files = result.scalars().all()

        for file in expired_files:
            try:
                # Delete from storage
                if file.status != FileStatus.PENDING:
                    try:
                        await self.storage.delete_file(file.storage_key)
                    except Exception as e:
                        storage_errors.append(f"{file.id}: {e}")

                # Mark as expired
                file.status = FileStatus.EXPIRED

                deleted_count += 1

            except Exception as e:
                storage_errors.append(f"{file.id}: {e}")

        # Delete expired file records
        await db.execute(
            delete(File).where(
                and_(
                    File.is_temporary == True,
                    File.status == FileStatus.EXPIRED,
                )
            )
        )

        await db.commit()

        return {
            "expired_files_deleted": deleted_count,
            "storage_errors": storage_errors,
        }

    async def cleanup_abandoned_uploads(
        self,
        db: AsyncSession,
        max_age_hours: int = 24,
    ) -> dict:
        """Clean up abandoned multipart uploads.

        Removes uploads that have been in UPLOADING state too long.

        Args:
            db: Database session
            max_age_hours: Maximum age for in-progress uploads

        Returns:
            Dict with cleanup statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        aborted_count = 0
        errors = []

        # Find abandoned uploads
        result = await db.execute(
            select(File).where(
                and_(
                    File.status == FileStatus.UPLOADING,
                    File.created_at <= cutoff,
                    File.upload_id.isnot(None),
                )
            )
        )
        abandoned_uploads = result.scalars().all()

        for file in abandoned_uploads:
            try:
                # Abort multipart upload
                if file.upload_id:
                    await self.storage.abort_multipart_upload(
                        key=file.storage_key,
                        upload_id=file.upload_id,
                    )

                # Mark as failed
                file.status = FileStatus.FAILED
                file.error_message = "Upload abandoned (timeout)"

                aborted_count += 1

            except Exception as e:
                errors.append(f"{file.id}: {e}")

        await db.commit()

        return {
            "abandoned_uploads_aborted": aborted_count,
            "errors": errors,
        }

    async def cleanup_failed_files(
        self,
        db: AsyncSession,
        retention_days: int = 7,
    ) -> dict:
        """Delete old failed file records.

        Args:
            db: Database session
            retention_days: Days to retain failed file records

        Returns:
            Dict with cleanup statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        # Find old failed files
        result = await db.execute(
            select(File).where(
                and_(
                    File.status == FileStatus.FAILED,
                    File.updated_at <= cutoff,
                )
            )
        )
        failed_files = result.scalars().all()

        deleted_count = 0
        storage_errors = []

        for file in failed_files:
            try:
                # Try to delete from storage (may not exist)
                try:
                    await self.storage.delete_file(file.storage_key)
                except Exception:
                    pass  # Ignore storage errors for failed files

                # Delete record (chunks will cascade)
                await db.delete(file)
                deleted_count += 1

            except Exception as e:
                storage_errors.append(f"{file.id}: {e}")

        await db.commit()

        return {
            "failed_files_deleted": deleted_count,
            "errors": storage_errors,
        }

    async def cleanup_orphaned_storage(
        self,
        db: AsyncSession,
        prefix: str = "",
        dry_run: bool = True,
    ) -> dict:
        """Find and optionally delete orphaned files in storage.

        Finds files in storage that don't have corresponding database records.

        Args:
            db: Database session
            prefix: Storage prefix to scan
            dry_run: If True, only report orphans without deleting

        Returns:
            Dict with orphaned file info
        """
        orphaned = []
        deleted_count = 0

        # List all files in storage
        storage_files = await self.storage.list_files(prefix=prefix)

        for storage_file in storage_files:
            key = storage_file["key"]

            # Check if file exists in database
            result = await db.execute(
                select(File.id).where(File.storage_key == key)
            )
            if result.scalar_one_or_none() is None:
                orphaned.append({
                    "key": key,
                    "size": storage_file["size"],
                    "last_modified": storage_file["last_modified"].isoformat(),
                })

                if not dry_run:
                    try:
                        await self.storage.delete_file(key)
                        deleted_count += 1
                    except Exception:
                        pass

        return {
            "orphaned_files": orphaned,
            "orphan_count": len(orphaned),
            "deleted_count": deleted_count if not dry_run else 0,
            "dry_run": dry_run,
        }

    async def cleanup_local_temp_files(
        self,
        max_age_hours: int = 24,
    ) -> dict:
        """Clean up local temporary chunk files.

        Args:
            max_age_hours: Maximum age for temporary files

        Returns:
            Dict with cleanup statistics
        """
        if not self.temp_dir.exists():
            return {"deleted_count": 0, "errors": []}

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        deleted_count = 0
        errors = []

        for temp_file in self.temp_dir.glob("*.chunk"):
            try:
                mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                if mtime <= cutoff:
                    temp_file.unlink()
                    deleted_count += 1
            except Exception as e:
                errors.append(f"{temp_file.name}: {e}")

        # Also clean up assembled files
        for complete_file in self.temp_dir.glob("*_complete"):
            try:
                mtime = datetime.fromtimestamp(complete_file.stat().st_mtime)
                if mtime <= cutoff:
                    complete_file.unlink()
                    deleted_count += 1
            except Exception as e:
                errors.append(f"{complete_file.name}: {e}")

        return {
            "local_files_deleted": deleted_count,
            "errors": errors,
        }

    async def cleanup_orphaned_chunks(self, db: AsyncSession) -> dict:
        """Clean up chunk records without parent files.

        Args:
            db: Database session

        Returns:
            Dict with cleanup statistics
        """
        # Find orphaned chunks (file_id doesn't exist in files table)
        result = await db.execute(
            select(FileChunk.id)
            .outerjoin(File, FileChunk.file_id == File.id)
            .where(File.id.is_(None))
        )
        orphan_ids = [row[0] for row in result.all()]

        if orphan_ids:
            await db.execute(
                delete(FileChunk).where(FileChunk.id.in_(orphan_ids))
            )
            await db.commit()

        return {
            "orphaned_chunks_deleted": len(orphan_ids),
        }

    async def cleanup_orphaned_jobs(self, db: AsyncSession) -> dict:
        """Clean up processing job records without parent files.

        Args:
            db: Database session

        Returns:
            Dict with cleanup statistics
        """
        # Find orphaned jobs
        result = await db.execute(
            select(FileProcessingJob.id)
            .outerjoin(File, FileProcessingJob.file_id == File.id)
            .where(File.id.is_(None))
        )
        orphan_ids = [row[0] for row in result.all()]

        if orphan_ids:
            await db.execute(
                delete(FileProcessingJob).where(FileProcessingJob.id.in_(orphan_ids))
            )
            await db.commit()

        return {
            "orphaned_jobs_deleted": len(orphan_ids),
        }

    async def run_full_cleanup(
        self,
        db: AsyncSession,
        include_orphan_scan: bool = False,
    ) -> dict:
        """Run all cleanup tasks.

        Args:
            db: Database session
            include_orphan_scan: Include storage orphan scan (slow)

        Returns:
            Dict with all cleanup results
        """
        results = {}

        # Cleanup expired files
        results["expired"] = await self.cleanup_expired_files(db)

        # Cleanup abandoned uploads
        results["abandoned"] = await self.cleanup_abandoned_uploads(db)

        # Cleanup failed files
        results["failed"] = await self.cleanup_failed_files(db)

        # Cleanup local temp files
        results["local_temp"] = await self.cleanup_local_temp_files()

        # Cleanup orphaned chunks and jobs
        results["orphaned_chunks"] = await self.cleanup_orphaned_chunks(db)
        results["orphaned_jobs"] = await self.cleanup_orphaned_jobs(db)

        # Optional: Scan for orphaned storage files (can be slow)
        if include_orphan_scan:
            results["orphaned_storage"] = await self.cleanup_orphaned_storage(
                db, dry_run=True
            )

        return results

    async def start_scheduler(
        self,
        db_session_factory: Callable[[], AsyncSession],
        interval_hours: float = 1.0,
    ) -> None:
        """Start the cleanup scheduler.

        Runs cleanup tasks periodically.

        Args:
            db_session_factory: Factory function to create database sessions
            interval_hours: Hours between cleanup runs
        """
        self._running = True
        interval_seconds = interval_hours * 3600

        while self._running:
            try:
                async with db_session_factory() as db:
                    await self.run_full_cleanup(db)
            except Exception as e:
                print(f"Cleanup error: {e}")

            await asyncio.sleep(interval_seconds)

    def stop_scheduler(self) -> None:
        """Stop the cleanup scheduler."""
        self._running = False

    async def delete_file(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> bool:
        """Delete a specific file.

        Args:
            db: Database session
            file_id: File ID
            organization_id: Organization ID (for access control)

        Returns:
            True if file was deleted

        Raises:
            CleanupError: If file not found or access denied
        """
        result = await db.execute(
            select(File).where(
                and_(
                    File.id == file_id,
                    File.organization_id == organization_id,
                )
            )
        )
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise CleanupError(f"File not found: {file_id}")

        # Abort multipart upload if in progress
        if file_record.upload_id:
            try:
                await self.storage.abort_multipart_upload(
                    key=file_record.storage_key,
                    upload_id=file_record.upload_id,
                )
            except Exception:
                pass

        # Delete from storage
        try:
            await self.storage.delete_file(file_record.storage_key)
        except Exception:
            pass  # File may not exist in storage

        # Delete database record (cascade deletes chunks and jobs)
        await db.delete(file_record)
        await db.commit()

        return True

    async def bulk_delete_files(
        self,
        db: AsyncSession,
        file_ids: list[uuid.UUID],
        organization_id: uuid.UUID,
    ) -> dict:
        """Delete multiple files.

        Args:
            db: Database session
            file_ids: List of file IDs
            organization_id: Organization ID (for access control)

        Returns:
            Dict with deletion results
        """
        deleted = []
        errors = []

        for file_id in file_ids:
            try:
                await self.delete_file(db, file_id, organization_id)
                deleted.append(str(file_id))
            except Exception as e:
                errors.append({"file_id": str(file_id), "error": str(e)})

        return {
            "deleted": deleted,
            "deleted_count": len(deleted),
            "errors": errors,
            "error_count": len(errors),
        }
