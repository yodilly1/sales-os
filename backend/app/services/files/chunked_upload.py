"""Chunked file upload service for handling large file uploads."""

import hashlib
import math
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import StorageClient, get_storage_client
from app.models.file import (
    ChunkUploadResponse,
    File,
    FileChunk,
    FileResponse,
    FileStatus,
    FileType,
    FileUploadInitRequest,
    FileUploadInitResponse,
)
from app.services.files.validation import FileValidationService


class ChunkedUploadError(Exception):
    """Exception raised during chunked upload operations."""

    pass


class ChunkedUploadService:
    """Service for handling chunked file uploads.

    Supports both small files (single upload) and large files (multipart upload).
    Uses S3 multipart upload API for large files.
    """

    def __init__(
        self,
        storage: Optional[StorageClient] = None,
        validation: Optional[FileValidationService] = None,
    ):
        """Initialize the chunked upload service.

        Args:
            storage: Storage client instance
            validation: File validation service
        """
        self.storage = storage or get_storage_client()
        self.validation = validation or FileValidationService()
        self.chunk_size = settings.chunk_size_bytes
        self.max_file_size = settings.max_file_size_bytes
        self.temp_dir = Path(settings.upload_temp_dir)

    def _generate_storage_key(
        self,
        organization_id: uuid.UUID,
        file_type: FileType,
        filename: str,
    ) -> str:
        """Generate a unique storage key for a file.

        Args:
            organization_id: Organization ID
            file_type: Type of file
            filename: Original filename

        Returns:
            S3 storage key
        """
        file_uuid = uuid.uuid4().hex
        ext = Path(filename).suffix.lower()
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")

        return f"{organization_id}/{file_type.value}/{date_prefix}/{file_uuid}{ext}"

    def _calculate_chunks(self, size_bytes: int) -> tuple[int, int]:
        """Calculate number of chunks and chunk size.

        Args:
            size_bytes: Total file size in bytes

        Returns:
            Tuple of (total_chunks, chunk_size)
        """
        if size_bytes <= self.chunk_size:
            return 1, size_bytes

        total_chunks = math.ceil(size_bytes / self.chunk_size)
        return total_chunks, self.chunk_size

    async def initiate_upload(
        self,
        db: AsyncSession,
        request: FileUploadInitRequest,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FileUploadInitResponse:
        """Initiate a new file upload.

        Args:
            db: Database session
            request: Upload initiation request
            organization_id: Organization ID
            user_id: User ID

        Returns:
            FileUploadInitResponse with upload details

        Raises:
            ChunkedUploadError: If validation fails
        """
        # Validate file
        validation_result = await self.validation.validate_file(
            filename=request.filename,
            size_bytes=request.size_bytes,
        )

        if not validation_result.is_valid:
            errors = [f"{e.field}: {e.message}" for e in validation_result.errors]
            raise ChunkedUploadError(f"Validation failed: {'; '.join(errors)}")

        # Determine file type
        file_type = request.file_type or self.validation.get_file_type(request.filename)
        if file_type is None:
            raise ChunkedUploadError("Unable to determine file type")

        # Generate storage key
        storage_key = self._generate_storage_key(
            organization_id, file_type, request.filename
        )

        # Calculate chunks
        total_chunks, chunk_size = self._calculate_chunks(request.size_bytes)
        is_multipart = total_chunks > 1

        # Get MIME type
        mime_type = request.content_type or self.validation.get_mime_type(request.filename)
        ext = Path(request.filename).suffix.lower()

        # Initiate multipart upload if needed
        upload_id = None
        if is_multipart:
            upload_id = await self.storage.upload_file_multipart(
                key=storage_key,
                content_type=mime_type,
                metadata={"original_filename": request.filename},
            )

        # Create file record
        file_record = File(
            organization_id=organization_id,
            user_id=user_id,
            original_filename=request.filename,
            storage_key=storage_key,
            file_type=file_type,
            mime_type=mime_type,
            extension=ext,
            size_bytes=request.size_bytes,
            status=FileStatus.UPLOADING if is_multipart else FileStatus.PENDING,
            upload_id=upload_id,
            total_chunks=total_chunks,
            uploaded_chunks=0,
            metadata=request.metadata,
            is_temporary=request.is_temporary,
            expires_at=(
                datetime.utcnow() + timedelta(hours=settings.temp_file_expiry_hours)
                if request.is_temporary
                else None
            ),
        )

        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)

        return FileUploadInitResponse(
            file_id=file_record.id,
            upload_id=upload_id,
            is_multipart=is_multipart,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            storage_key=storage_key,
        )

    async def upload_chunk(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
        chunk_number: int,
        chunk_data: bytes,
        checksum: Optional[str] = None,
    ) -> ChunkUploadResponse:
        """Upload a file chunk.

        Args:
            db: Database session
            file_id: File ID
            chunk_number: Chunk number (1-indexed)
            chunk_data: Chunk data as bytes
            checksum: Optional SHA-256 checksum of chunk

        Returns:
            ChunkUploadResponse with upload status

        Raises:
            ChunkedUploadError: If upload fails
        """
        # Get file record
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise ChunkedUploadError(f"File not found: {file_id}")

        if file_record.status not in (FileStatus.PENDING, FileStatus.UPLOADING):
            raise ChunkedUploadError(
                f"File is not in uploadable state: {file_record.status}"
            )

        if chunk_number < 1 or chunk_number > file_record.total_chunks:
            raise ChunkedUploadError(
                f"Invalid chunk number: {chunk_number}. Expected 1-{file_record.total_chunks}"
            )

        # Verify checksum if provided
        if checksum:
            calculated_checksum = hashlib.sha256(chunk_data).hexdigest()
            if calculated_checksum != checksum:
                raise ChunkedUploadError(
                    f"Checksum mismatch for chunk {chunk_number}"
                )

        # Check if chunk already uploaded
        existing_chunk = await db.execute(
            select(FileChunk).where(
                FileChunk.file_id == file_id,
                FileChunk.chunk_number == chunk_number,
            )
        )
        if existing_chunk.scalar_one_or_none():
            raise ChunkedUploadError(f"Chunk {chunk_number} already uploaded")

        # Upload chunk to S3
        if file_record.upload_id:
            # Multipart upload
            part_info = await self.storage.upload_part(
                key=file_record.storage_key,
                upload_id=file_record.upload_id,
                part_number=chunk_number,
                body=chunk_data,
            )
            etag = part_info["ETag"]
        else:
            # Single chunk upload - upload directly
            await self.storage.upload_file(
                file_data=chunk_data,
                key=file_record.storage_key,
                content_type=file_record.mime_type,
                metadata={"original_filename": file_record.original_filename},
            )
            etag = hashlib.md5(chunk_data).hexdigest()

        # Record chunk
        chunk_record = FileChunk(
            file_id=file_id,
            chunk_number=chunk_number,
            size_bytes=len(chunk_data),
            etag=etag,
            checksum=checksum or hashlib.sha256(chunk_data).hexdigest(),
        )
        db.add(chunk_record)

        # Update file record
        file_record.uploaded_chunks += 1
        file_record.status = FileStatus.UPLOADING

        is_complete = file_record.uploaded_chunks >= file_record.total_chunks

        await db.commit()

        return ChunkUploadResponse(
            chunk_number=chunk_number,
            etag=etag,
            uploaded_chunks=file_record.uploaded_chunks,
            total_chunks=file_record.total_chunks,
            is_complete=is_complete,
        )

    async def complete_upload(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
        checksum: Optional[str] = None,
    ) -> FileResponse:
        """Complete a file upload.

        Args:
            db: Database session
            file_id: File ID
            checksum: Optional SHA-256 checksum of complete file

        Returns:
            FileResponse with completed file details

        Raises:
            ChunkedUploadError: If completion fails
        """
        # Get file record with chunks
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise ChunkedUploadError(f"File not found: {file_id}")

        if file_record.status not in (FileStatus.PENDING, FileStatus.UPLOADING):
            raise ChunkedUploadError(
                f"File is not in completable state: {file_record.status}"
            )

        # Verify all chunks uploaded
        if file_record.uploaded_chunks < file_record.total_chunks:
            raise ChunkedUploadError(
                f"Not all chunks uploaded: {file_record.uploaded_chunks}/{file_record.total_chunks}"
            )

        # Complete multipart upload if applicable
        if file_record.upload_id:
            # Get all chunks in order
            chunks_result = await db.execute(
                select(FileChunk)
                .where(FileChunk.file_id == file_id)
                .order_by(FileChunk.chunk_number)
            )
            chunks = chunks_result.scalars().all()

            parts = [
                {"ETag": chunk.etag, "PartNumber": chunk.chunk_number}
                for chunk in chunks
            ]

            try:
                await self.storage.complete_multipart_upload(
                    key=file_record.storage_key,
                    upload_id=file_record.upload_id,
                    parts=parts,
                )
            except Exception as e:
                # Abort the multipart upload on failure
                await self.storage.abort_multipart_upload(
                    key=file_record.storage_key,
                    upload_id=file_record.upload_id,
                )
                file_record.status = FileStatus.FAILED
                file_record.error_message = str(e)
                await db.commit()
                raise ChunkedUploadError(f"Failed to complete upload: {e}") from e

        # Update file record
        file_record.status = FileStatus.UPLOADED
        file_record.checksum = checksum
        file_record.upload_id = None  # Clear multipart upload ID

        await db.commit()
        await db.refresh(file_record)

        return FileResponse.model_validate(file_record)

    async def abort_upload(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
    ) -> None:
        """Abort an in-progress upload.

        Args:
            db: Database session
            file_id: File ID

        Raises:
            ChunkedUploadError: If abort fails
        """
        # Get file record
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise ChunkedUploadError(f"File not found: {file_id}")

        # Abort multipart upload if in progress
        if file_record.upload_id:
            await self.storage.abort_multipart_upload(
                key=file_record.storage_key,
                upload_id=file_record.upload_id,
            )

        # Delete any uploaded parts from storage
        try:
            await self.storage.delete_file(file_record.storage_key)
        except Exception:
            pass  # File may not exist yet

        # Delete file record and chunks (cascade)
        await db.delete(file_record)
        await db.commit()

    async def get_upload_status(
        self,
        db: AsyncSession,
        file_id: uuid.UUID,
    ) -> FileResponse:
        """Get the current status of an upload.

        Args:
            db: Database session
            file_id: File ID

        Returns:
            FileResponse with current status

        Raises:
            ChunkedUploadError: If file not found
        """
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if file_record is None:
            raise ChunkedUploadError(f"File not found: {file_id}")

        return FileResponse.model_validate(file_record)

    async def upload_single_file(
        self,
        db: AsyncSession,
        file_data: BinaryIO | bytes,
        filename: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        is_temporary: bool = False,
    ) -> FileResponse:
        """Upload a file in a single request (for smaller files).

        Args:
            db: Database session
            file_data: File content
            filename: Original filename
            organization_id: Organization ID
            user_id: User ID
            content_type: MIME type
            metadata: Optional metadata
            is_temporary: Whether file is temporary

        Returns:
            FileResponse with file details

        Raises:
            ChunkedUploadError: If upload fails
        """
        # Get content as bytes
        if isinstance(file_data, bytes):
            content = file_data
        else:
            content = file_data.read()

        size_bytes = len(content)

        # Validate file
        validation_result = await self.validation.validate_file(
            filename=filename,
            size_bytes=size_bytes,
            content=content,
        )

        if not validation_result.is_valid:
            errors = [f"{e.field}: {e.message}" for e in validation_result.errors]
            raise ChunkedUploadError(f"Validation failed: {'; '.join(errors)}")

        # Determine file type
        file_type = self.validation.get_file_type(filename)
        if file_type is None:
            raise ChunkedUploadError("Unable to determine file type")

        # Generate storage key
        storage_key = self._generate_storage_key(
            organization_id, file_type, filename
        )

        # Get MIME type
        mime_type = content_type or self.validation.get_mime_type(filename)
        ext = Path(filename).suffix.lower()

        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Upload to storage
        await self.storage.upload_file(
            file_data=content,
            key=storage_key,
            content_type=mime_type,
            metadata={"original_filename": filename},
        )

        # Create file record
        file_record = File(
            organization_id=organization_id,
            user_id=user_id,
            original_filename=filename,
            storage_key=storage_key,
            file_type=file_type,
            mime_type=mime_type,
            extension=ext,
            size_bytes=size_bytes,
            status=FileStatus.UPLOADED,
            total_chunks=1,
            uploaded_chunks=1,
            metadata=metadata,
            checksum=checksum,
            is_temporary=is_temporary,
            expires_at=(
                datetime.utcnow() + timedelta(hours=settings.temp_file_expiry_hours)
                if is_temporary
                else None
            ),
        )

        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)

        return FileResponse.model_validate(file_record)

    def _ensure_temp_dir(self) -> None:
        """Ensure temporary upload directory exists."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def save_chunk_locally(
        self,
        file_id: uuid.UUID,
        chunk_number: int,
        chunk_data: bytes,
    ) -> Path:
        """Save a chunk to local temporary storage.

        Used for local processing before uploading to S3.

        Args:
            file_id: File ID
            chunk_number: Chunk number
            chunk_data: Chunk data

        Returns:
            Path to saved chunk file
        """
        self._ensure_temp_dir()

        chunk_path = self.temp_dir / f"{file_id}_{chunk_number:05d}.chunk"
        chunk_path.write_bytes(chunk_data)

        return chunk_path

    async def assemble_local_chunks(
        self,
        file_id: uuid.UUID,
        total_chunks: int,
    ) -> Path:
        """Assemble local chunks into a complete file.

        Args:
            file_id: File ID
            total_chunks: Total number of chunks

        Returns:
            Path to assembled file
        """
        self._ensure_temp_dir()

        output_path = self.temp_dir / f"{file_id}_complete"

        with open(output_path, "wb") as output_file:
            for chunk_num in range(1, total_chunks + 1):
                chunk_path = self.temp_dir / f"{file_id}_{chunk_num:05d}.chunk"
                if chunk_path.exists():
                    output_file.write(chunk_path.read_bytes())

        return output_path

    async def cleanup_local_chunks(self, file_id: uuid.UUID) -> None:
        """Clean up local chunk files.

        Args:
            file_id: File ID
        """
        # Find and delete all chunks for this file
        for chunk_file in self.temp_dir.glob(f"{file_id}_*.chunk"):
            try:
                chunk_file.unlink()
            except Exception:
                pass

        # Delete assembled file if exists
        complete_file = self.temp_dir / f"{file_id}_complete"
        if complete_file.exists():
            try:
                complete_file.unlink()
            except Exception:
                pass
