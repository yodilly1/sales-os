"""Import API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, UploadFile, File, Form
from pydantic import BaseModel
import json

from app.models.export_import import (
    ImportType,
    ImportStatus,
    ImportJobSchema,
    ImportProgress,
    ImportValidationResult,
)
from app.services.import_service import ImportService

router = APIRouter()


# Request/Response models
class FieldMappingConfig(BaseModel):
    """Field mapping configuration."""

    source_column: str
    target_field: str
    transform: Optional[str] = None
    default_value: Optional[str] = None


class ImportRequest(BaseModel):
    """Request to create an import job."""

    file_id: str
    import_type: ImportType
    field_mapping: Dict[str, Dict[str, Any]] = {}


class ImportTypeInfo(BaseModel):
    """Information about an import type."""

    type: ImportType
    required_fields: List[str]
    optional_fields: List[str]
    supported_formats: List[str]


class ColumnPreview(BaseModel):
    """Preview of import file columns."""

    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    total_rows: int
    required_fields: List[str]
    optional_fields: List[str]
    mapping_suggestions: Dict[str, Dict[str, Any]]


class UploadResult(BaseModel):
    """Result of file upload."""

    file_id: str
    original_filename: str
    file_size_bytes: int
    file_type: str


# Dependency injection
def get_import_service() -> ImportService:
    """Get import service instance."""
    return ImportService()


def get_current_user():
    """Get current authenticated user.

    TODO: Implement actual authentication.
    """
    return {
        "id": "user-001",
        "organization_id": "org-001",
    }


# Endpoints
@router.get("/types", response_model=List[ImportTypeInfo])
async def list_import_types(
    service: ImportService = Depends(get_import_service),
):
    """List available import types and their field requirements.

    Returns:
        List of import types with required/optional fields.
    """
    return service.get_supported_types()


@router.post("/upload", response_model=UploadResult)
async def upload_file(
    file: UploadFile = File(...),
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Upload a file for import.

    Accepts CSV or JSON files. Returns a file_id for use in subsequent operations.

    Args:
        file: The file to upload

    Returns:
        Upload result with file_id.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    allowed_types = [".csv", ".json"]
    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    try:
        content = await file.read()
        result = await service.upload_file(
            file_content=content,
            filename=file.filename,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )
        return UploadResult(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preview/{file_id}", response_model=ColumnPreview)
async def preview_file(
    file_id: str,
    import_type: ImportType = Query(...),
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Preview an uploaded file and get mapping suggestions.

    Shows columns, sample data, and suggested field mappings.

    Args:
        file_id: ID from upload
        import_type: Type of import

    Returns:
        Column preview with mapping suggestions.
    """
    # TODO: Get file path from file_id via database
    # For now, construct path
    from pathlib import Path
    from app.core.config import settings

    upload_dir = Path(settings.export_temp_dir) / "uploads"

    # Try both csv and json extensions
    file_path = None
    for ext in [".csv", ".json"]:
        potential_path = upload_dir / f"{file_id}{ext}"
        if potential_path.exists():
            file_path = str(potential_path)
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        result = await service.get_column_preview(file_path, import_type)
        return ColumnPreview(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=ImportValidationResult)
async def validate_import(
    file_id: str = Form(...),
    import_type: str = Form(...),
    field_mapping: str = Form("{}"),
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Validate an import file before processing.

    Runs validation on all rows and reports errors.

    Args:
        file_id: ID from upload
        import_type: Type of import
        field_mapping: JSON string of field mappings

    Returns:
        Validation result with errors and warnings.
    """
    try:
        mapping = json.loads(field_mapping)
        import_type_enum = ImportType(import_type)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # TODO: Get file path and create job for validation
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


@router.post("", response_model=ImportJobSchema)
async def create_import(
    background_tasks: BackgroundTasks,
    file_id: str = Form(...),
    import_type: str = Form(...),
    field_mapping: str = Form("{}"),
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Create and start an import job.

    Creates an import job and starts processing in the background.

    Args:
        file_id: ID from upload
        import_type: Type of import
        field_mapping: JSON string of field mappings

    Returns:
        Created import job details.
    """
    try:
        mapping = json.loads(field_mapping)
        import_type_enum = ImportType(import_type)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get file path
    from pathlib import Path
    from app.core.config import settings

    upload_dir = Path(settings.export_temp_dir) / "uploads"
    file_path = None
    original_filename = f"{file_id}.csv"

    for ext in [".csv", ".json"]:
        potential_path = upload_dir / f"{file_id}{ext}"
        if potential_path.exists():
            file_path = str(potential_path)
            original_filename = f"import{ext}"
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        job = await service.create_import_job(
            file_path=file_path,
            original_filename=original_filename,
            import_type=import_type_enum,
            field_mapping=mapping,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )

        # Start processing in background
        background_tasks.add_task(
            service.execute_import,
            job.id,
            file_path,
            import_type_enum,
            mapping,
            user["id"],
            user["organization_id"],
        )

        return job

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync", response_model=ImportJobSchema)
async def create_import_sync(
    file_id: str = Form(...),
    import_type: str = Form(...),
    field_mapping: str = Form("{}"),
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Create and execute an import synchronously.

    For small imports that should complete immediately.

    Args:
        file_id: ID from upload
        import_type: Type of import
        field_mapping: JSON string of field mappings

    Returns:
        Completed import job with results.
    """
    try:
        mapping = json.loads(field_mapping)
        import_type_enum = ImportType(import_type)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get file path
    from pathlib import Path
    from app.core.config import settings
    import uuid

    upload_dir = Path(settings.export_temp_dir) / "uploads"
    file_path = None
    original_filename = f"{file_id}.csv"

    for ext in [".csv", ".json"]:
        potential_path = upload_dir / f"{file_id}{ext}"
        if potential_path.exists():
            file_path = str(potential_path)
            original_filename = f"import{ext}"
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        job = await service.create_import_job(
            file_path=file_path,
            original_filename=original_filename,
            import_type=import_type_enum,
            field_mapping=mapping,
            user_id=user["id"],
            organization_id=user["organization_id"],
        )

        # Execute immediately
        result = await service.execute_import(
            job.id,
            file_path,
            import_type_enum,
            mapping,
            user["id"],
            user["organization_id"],
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}", response_model=ImportJobSchema)
async def get_import_job(
    job_id: str,
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Get details of an import job.

    Args:
        job_id: Import job ID

    Returns:
        Import job details including status and progress.
    """
    # TODO: Fetch from database
    from datetime import datetime

    return ImportJobSchema(
        id=job_id,
        import_type=ImportType.PROSPECTS,
        status=ImportStatus.COMPLETED,
        original_filename="prospects.csv",
        field_mapping={},
        total_records=10,
        processed_records=10,
        successful_records=10,
        failed_records=0,
        progress_percent=100.0,
        imported_ids=["id-1", "id-2", "id-3"],
        errors=[],
        user_id=user["id"],
        organization_id=user["organization_id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/{job_id}/progress", response_model=ImportProgress)
async def get_import_progress(
    job_id: str,
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Get progress of an import job.

    Poll this endpoint to track progress of long-running imports.

    Args:
        job_id: Import job ID

    Returns:
        Current import progress.
    """
    progress = await service.get_import_progress(
        job_id,
        user["id"],
        user["organization_id"],
    )
    return progress


@router.get("", response_model=List[ImportJobSchema])
async def list_imports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    import_type: Optional[ImportType] = None,
    status: Optional[ImportStatus] = None,
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """List import jobs.

    Args:
        limit: Maximum number of results
        offset: Pagination offset
        import_type: Filter by import type
        status: Filter by status

    Returns:
        List of import jobs.
    """
    jobs = await service.list_imports(
        user["id"],
        user["organization_id"],
        limit=limit,
        offset=offset,
    )
    return jobs


@router.delete("/file/{file_id}")
async def delete_uploaded_file(
    file_id: str,
    service: ImportService = Depends(get_import_service),
    user: dict = Depends(get_current_user),
):
    """Delete an uploaded file.

    Clean up an uploaded file that won't be imported.

    Args:
        file_id: File ID from upload

    Returns:
        Deletion status.
    """
    from pathlib import Path
    from app.core.config import settings

    upload_dir = Path(settings.export_temp_dir) / "uploads"

    deleted = False
    for ext in [".csv", ".json"]:
        file_path = upload_dir / f"{file_id}{ext}"
        if await service.cleanup_upload(str(file_path)):
            deleted = True
            break

    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")

    return {"status": "deleted", "file_id": file_id}
