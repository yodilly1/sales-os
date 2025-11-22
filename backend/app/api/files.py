"""File upload API endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import get_storage_client
from app.models.file import (
    ChunkUploadResponse,
    FileListResponse,
    FileResponse,
    FileStatus,
    FileType,
    FileUploadInitRequest,
    FileUploadInitResponse,
    FileValidationResponse,
    ProcessingJobResponse,
)
from app.models.file import File as FileModel
from app.services.files import (
    ChunkedUploadService,
    FileCleanupService,
    FileProcessingService,
    FileValidationService,
)

router = APIRouter()


# Dependency stubs - these would be replaced with actual implementations
async def get_db() -> AsyncSession:
    """Get database session.

    This is a placeholder that would be replaced with actual database session.
    """
    # In production, this would yield an actual database session
    # from app.db.session import async_session
    # async with async_session() as session:
    #     yield session
    raise NotImplementedError("Database session not configured")


async def get_current_user() -> dict:
    """Get current authenticated user.

    This is a placeholder that would be replaced with actual auth.
    """
    # In production, this would verify JWT and return user info
    # For now, return a mock user
    return {
        "id": uuid.uuid4(),
        "organization_id": uuid.uuid4(),
        "email": "user@example.com",
    }


# Request/Response models


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""

    message: str
    data: Optional[dict] = None


class BulkDeleteRequest(BaseModel):
    """Request to delete multiple files."""

    file_ids: list[uuid.UUID]


class BulkDeleteResponse(BaseModel):
    """Response from bulk delete."""

    deleted: list[str]
    deleted_count: int
    errors: list[dict]
    error_count: int


# API Endpoints


@router.post(
    "/upload/init",
    response_model=FileUploadInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate file upload",
    description="Initialize a new file upload. Returns upload ID and chunk configuration.",
)
async def initiate_upload(
    request: FileUploadInitRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Initiate a new file upload.

    For small files, returns single-chunk configuration.
    For large files, returns multipart upload ID and chunk size.
    """
    try:
        service = ChunkedUploadService()
        result = await service.initiate_upload(
            db=db,
            request=request,
            organization_id=user["organization_id"],
            user_id=user["id"],
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/upload/{file_id}/chunk/{chunk_number}",
    response_model=ChunkUploadResponse,
    summary="Upload file chunk",
    description="Upload a single chunk of a file.",
)
async def upload_chunk(
    file_id: uuid.UUID,
    chunk_number: int,
    chunk: UploadFile = File(...),
    checksum: Optional[str] = Header(None, alias="X-Chunk-Checksum"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Upload a file chunk.

    Chunks must be uploaded in order for multipart uploads.
    Include X-Chunk-Checksum header for integrity verification.
    """
    try:
        chunk_data = await chunk.read()

        service = ChunkedUploadService()
        result = await service.upload_chunk(
            db=db,
            file_id=file_id,
            chunk_number=chunk_number,
            chunk_data=chunk_data,
            checksum=checksum,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/upload/{file_id}/complete",
    response_model=FileResponse,
    summary="Complete file upload",
    description="Complete a multipart file upload.",
)
async def complete_upload(
    file_id: uuid.UUID,
    checksum: Optional[str] = Header(None, alias="X-File-Checksum"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Complete a file upload.

    Finalizes multipart upload and marks file as ready for processing.
    Include X-File-Checksum header for complete file integrity verification.
    """
    try:
        service = ChunkedUploadService()
        result = await service.complete_upload(
            db=db,
            file_id=file_id,
            checksum=checksum,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/upload/{file_id}/abort",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abort file upload",
    description="Abort an in-progress file upload.",
)
async def abort_upload(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Abort an in-progress upload.

    Cleans up any uploaded chunks and removes file record.
    """
    try:
        service = ChunkedUploadService()
        await service.abort_upload(db=db, file_id=file_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file (single request)",
    description="Upload a complete file in a single request. For small files only.",
)
async def upload_file(
    file: UploadFile = File(...),
    file_type: Optional[FileType] = Form(None),
    is_temporary: bool = Form(False),
    metadata: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Upload a file in a single request.

    For files under the chunk size threshold.
    Use chunked upload for larger files.
    """
    import json

    try:
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metadata JSON",
                )

        content = await file.read()

        # Check file size
        if len(content) > settings.chunk_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large for single upload. Use chunked upload for files over {settings.chunk_size_mb}MB.",
            )

        service = ChunkedUploadService()
        result = await service.upload_single_file(
            db=db,
            file_data=content,
            filename=file.filename,
            organization_id=user["organization_id"],
            user_id=user["id"],
            content_type=file.content_type,
            metadata=parsed_metadata,
            is_temporary=is_temporary,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file metadata",
    description="Get metadata for a specific file.",
)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get file metadata by ID."""
    result = await db.execute(
        select(FileModel).where(
            and_(
                FileModel.id == file_id,
                FileModel.organization_id == user["organization_id"],
            )
        )
    )
    file_record = result.scalar_one_or_none()

    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return FileResponse.model_validate(file_record)


@router.get(
    "/{file_id}/download",
    summary="Download file",
    description="Download file content.",
)
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Download file content.

    Returns file as streaming response.
    """
    result = await db.execute(
        select(FileModel).where(
            and_(
                FileModel.id == file_id,
                FileModel.organization_id == user["organization_id"],
            )
        )
    )
    file_record = result.scalar_one_or_none()

    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if file_record.status not in (FileStatus.UPLOADED, FileStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File not ready for download: {file_record.status}",
        )

    storage = get_storage_client()

    async def stream_file():
        async for chunk in storage.download_file_stream(file_record.storage_key):
            yield chunk

    return StreamingResponse(
        stream_file(),
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_record.original_filename}"',
            "Content-Length": str(file_record.size_bytes),
        },
    )


@router.get(
    "/{file_id}/presigned-url",
    summary="Get presigned download URL",
    description="Get a presigned URL for direct download.",
)
async def get_presigned_url(
    file_id: uuid.UUID,
    expires_in: int = Query(default=3600, ge=60, le=86400),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get a presigned URL for direct file download.

    URL is valid for the specified duration (default 1 hour, max 24 hours).
    """
    result = await db.execute(
        select(FileModel).where(
            and_(
                FileModel.id == file_id,
                FileModel.organization_id == user["organization_id"],
            )
        )
    )
    file_record = result.scalar_one_or_none()

    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if file_record.status not in (FileStatus.UPLOADED, FileStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File not ready for download: {file_record.status}",
        )

    storage = get_storage_client()
    url = await storage.generate_presigned_url(
        key=file_record.storage_key,
        expires_in=expires_in,
    )

    return {
        "url": url,
        "expires_in": expires_in,
        "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
    }


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete a file and its content.",
)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a file.

    Removes file from storage and database.
    """
    try:
        service = FileCleanupService()
        await service.delete_file(
            db=db,
            file_id=file_id,
            organization_id=user["organization_id"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    summary="Delete multiple files",
    description="Delete multiple files at once.",
)
async def bulk_delete_files(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete multiple files.

    Returns count of successfully deleted files and any errors.
    """
    service = FileCleanupService()
    result = await service.bulk_delete_files(
        db=db,
        file_ids=request.file_ids,
        organization_id=user["organization_id"],
    )
    return result


@router.get(
    "",
    response_model=FileListResponse,
    summary="List files",
    description="List files with optional filtering.",
)
async def list_files(
    file_type: Optional[FileType] = Query(None),
    file_status: Optional[FileStatus] = Query(None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List files with optional filtering.

    Supports filtering by file type and status.
    Results are paginated.
    """
    # Build query
    query = select(FileModel).where(
        FileModel.organization_id == user["organization_id"]
    )

    if file_type:
        query = query.where(FileModel.file_type == file_type)
    if file_status:
        query = query.where(FileModel.status == file_status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = (
        query.order_by(FileModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    files = result.scalars().all()

    return FileListResponse(
        files=[FileResponse.model_validate(f) for f in files],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/validate",
    response_model=FileValidationResponse,
    summary="Validate file",
    description="Validate a file without uploading.",
)
async def validate_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Validate a file before upload.

    Checks file type, extension, size, and content validity.
    Does not store the file.
    """
    content = await file.read()

    service = FileValidationService()
    result = await service.validate_file(
        filename=file.filename,
        size_bytes=len(content),
        content=content,
    )

    return result


@router.post(
    "/{file_id}/process",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue file for processing",
    description="Add file to processing queue.",
)
async def queue_processing(
    file_id: uuid.UUID,
    job_type: str = Query(..., description="Type of processing job"),
    priority: int = Query(default=0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Queue a file for processing.

    Adds file to the processing queue with specified job type.
    Returns immediately with job ID for status tracking.
    """
    # Verify file belongs to user's organization
    result = await db.execute(
        select(FileModel).where(
            and_(
                FileModel.id == file_id,
                FileModel.organization_id == user["organization_id"],
            )
        )
    )
    file_record = result.scalar_one_or_none()

    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    try:
        service = FileProcessingService()
        job = await service.queue_job(
            db=db,
            file_id=file_id,
            job_type=job_type,
            priority=priority,
        )
        return job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{file_id}/jobs",
    response_model=list[ProcessingJobResponse],
    summary="Get file processing jobs",
    description="Get all processing jobs for a file.",
)
async def get_file_jobs(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get all processing jobs for a file."""
    # Verify file belongs to user's organization
    result = await db.execute(
        select(FileModel).where(
            and_(
                FileModel.id == file_id,
                FileModel.organization_id == user["organization_id"],
            )
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    service = FileProcessingService()
    jobs = await service.get_file_jobs(db=db, file_id=file_id)
    return jobs


@router.get(
    "/jobs/{job_id}",
    response_model=ProcessingJobResponse,
    summary="Get processing job status",
    description="Get status of a processing job.",
)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the status of a processing job."""
    try:
        service = FileProcessingService()
        job = await service.get_job_status(db=db, job_id=job_id)
        return job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel processing job",
    description="Cancel a queued processing job.",
)
async def cancel_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Cancel a queued processing job."""
    try:
        service = FileProcessingService()
        await service.cancel_job(db=db, job_id=job_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/queue/stats",
    summary="Get queue statistics",
    description="Get processing queue statistics.",
)
async def get_queue_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get processing queue statistics."""
    service = FileProcessingService()
    stats = await service.get_queue_stats(db=db)
    return stats
