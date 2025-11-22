"""Export API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.export_import import (
    ExportType,
    ExportFormat,
    ExportStatus,
    ExportJobCreate,
    ExportJobSchema,
    ExportProgress,
)
from app.services.export import ExportService

router = APIRouter()


# Request/Response models
class ExportRequest(BaseModel):
    """Request to create an export."""

    export_type: ExportType
    export_format: ExportFormat
    filters: dict = {}
    record_ids: List[str] = []


class ExportFormatInfo(BaseModel):
    """Information about supported export formats."""

    export_type: ExportType
    supported_formats: List[ExportFormat]


class ExportTypeInfo(BaseModel):
    """Information about an export type."""

    type: ExportType
    description: str
    supported_formats: List[ExportFormat]


# Dependency injection
def get_export_service() -> ExportService:
    """Get export service instance."""
    return ExportService()


def get_current_user():
    """Get current authenticated user.

    TODO: Implement actual authentication.
    """
    return {
        "id": "user-001",
        "organization_id": "org-001",
    }


# Endpoints
@router.get("/types", response_model=List[ExportTypeInfo])
async def list_export_types(
    service: ExportService = Depends(get_export_service),
):
    """List available export types and their supported formats.

    Returns:
        List of export types with descriptions and supported formats.
    """
    export_type_info = {
        ExportType.TRANSCRIPTS: {
            "description": "Export transcripts with SPICED analysis",
        },
        ExportType.CONTENT: {
            "description": "Export generated content with files",
        },
        ExportType.PROSPECTS: {
            "description": "Export prospect lists",
        },
        ExportType.COACHING: {
            "description": "Export coaching reports",
        },
        ExportType.FULL_BACKUP: {
            "description": "Full account backup",
        },
    }

    result = []
    for export_type in ExportType:
        formats = service.get_supported_formats(export_type)
        info = export_type_info.get(export_type, {"description": ""})
        result.append(
            ExportTypeInfo(
                type=export_type,
                description=info["description"],
                supported_formats=formats,
            )
        )

    return result


@router.get("/formats/{export_type}", response_model=ExportFormatInfo)
async def get_supported_formats(
    export_type: ExportType,
    service: ExportService = Depends(get_export_service),
):
    """Get supported formats for an export type.

    Args:
        export_type: The type of export

    Returns:
        List of supported formats for this export type.
    """
    formats = service.get_supported_formats(export_type)
    if not formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown export type: {export_type}",
        )

    return ExportFormatInfo(
        export_type=export_type,
        supported_formats=formats,
    )


@router.post("", response_model=ExportJobSchema)
async def create_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Create a new export job.

    Creates an export job and optionally starts processing.
    For large exports, processing happens in the background.

    Args:
        request: Export configuration

    Returns:
        Created export job details.
    """
    try:
        job_request = ExportJobCreate(
            export_type=request.export_type,
            export_format=request.export_format,
            filters=request.filters,
            record_ids=request.record_ids,
        )

        job = await service.create_export_job(
            request=job_request,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )

        # For small exports, execute immediately
        # For large exports, queue for background processing
        # TODO: Implement size-based decision
        background_tasks.add_task(
            service.execute_export,
            job.id,
            user["id"],
            user["organization_id"],
        )

        return job

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync", response_model=ExportJobSchema)
async def create_export_sync(
    request: ExportRequest,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Create and execute an export synchronously.

    For small exports that should complete immediately.
    The response includes the download URL.

    Args:
        request: Export configuration

    Returns:
        Completed export job with download URL.
    """
    try:
        job_request = ExportJobCreate(
            export_type=request.export_type,
            export_format=request.export_format,
            filters=request.filters,
            record_ids=request.record_ids,
        )

        job = await service.create_export_job(
            request=job_request,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )

        # Execute immediately
        result = await service.execute_export(
            job.id,
            user["id"],
            user["organization_id"],
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}", response_model=ExportJobSchema)
async def get_export_job(
    job_id: str,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Get details of an export job.

    Args:
        job_id: Export job ID

    Returns:
        Export job details including status and progress.
    """
    # TODO: Fetch from database
    # For now, return mock completed job
    return ExportJobSchema(
        id=job_id,
        export_type=ExportType.TRANSCRIPTS,
        export_format=ExportFormat.JSON,
        status=ExportStatus.COMPLETED,
        filters={},
        record_ids=[],
        total_records=10,
        processed_records=10,
        progress_percent=100.0,
        download_url=f"/api/v1/export/download/{job_id}",
        user_id=user["id"],
        organization_id=user["organization_id"],
        created_at="2024-01-20T10:00:00Z",
        updated_at="2024-01-20T10:00:00Z",
    )


@router.get("/{job_id}/progress", response_model=ExportProgress)
async def get_export_progress(
    job_id: str,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Get progress of an export job.

    Poll this endpoint to track progress of long-running exports.

    Args:
        job_id: Export job ID

    Returns:
        Current export progress.
    """
    progress = await service.get_export_progress(
        job_id,
        user["id"],
        user["organization_id"],
    )
    return progress


@router.get("/download/{job_id}")
async def download_export(
    job_id: str,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Download an exported file.

    Args:
        job_id: Export job ID

    Returns:
        The exported file.
    """
    file_path = await service.get_download_path(
        job_id,
        user["id"],
        user["organization_id"],
    )

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="Export not found or not ready",
        )

    # Determine media type based on file extension
    import os

    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        ".json": "application/json",
        ".csv": "text/csv",
        ".pdf": "application/pdf",
        ".zip": "application/zip",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    # Generate filename
    filename = f"export_{job_id}{ext}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.get("", response_model=List[ExportJobSchema])
async def list_exports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    export_type: Optional[ExportType] = None,
    status: Optional[ExportStatus] = None,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """List export jobs.

    Args:
        limit: Maximum number of results
        offset: Pagination offset
        export_type: Filter by export type
        status: Filter by status

    Returns:
        List of export jobs.
    """
    jobs = await service.list_exports(
        user["id"],
        user["organization_id"],
        limit=limit,
        offset=offset,
    )
    return jobs


@router.delete("/{job_id}")
async def cancel_export(
    job_id: str,
    service: ExportService = Depends(get_export_service),
    user: dict = Depends(get_current_user),
):
    """Cancel a pending or processing export job.

    Args:
        job_id: Export job ID

    Returns:
        Cancellation status.
    """
    cancelled = await service.cancel_export(
        job_id,
        user["id"],
        user["organization_id"],
    )

    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Export cannot be cancelled (may be completed or already cancelled)",
        )

    return {"status": "cancelled", "job_id": job_id}
