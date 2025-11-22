"""Export and Import job models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Float

from .base import BaseDBModel, BaseModel, TimestampedSchema


class ExportType(str, Enum):
    """Type of data to export."""

    TRANSCRIPTS = "transcripts"
    CONTENT = "content"
    PROSPECTS = "prospects"
    COACHING = "coaching"
    FULL_BACKUP = "full_backup"


class ExportFormat(str, Enum):
    """Export file format."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    ZIP = "zip"
    HUBSPOT = "hubspot"  # HubSpot-compatible CSV


class ExportStatus(str, Enum):
    """Status of export job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportJob(BaseDBModel):
    """Export job tracking model."""

    __tablename__ = "export_jobs"

    # Job configuration
    export_type = Column(SQLEnum(ExportType), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), nullable=False)
    status = Column(SQLEnum(ExportStatus), default=ExportStatus.PENDING)

    # Filters
    filters = Column(JSON, default=dict)  # Date range, status filters, etc.
    record_ids = Column(JSON, default=list)  # Specific record IDs to export

    # Progress tracking
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)

    # Result
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    download_url = Column(String(500))
    expires_at = Column(String(50))  # ISO date when download expires

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


class ImportType(str, Enum):
    """Type of data to import."""

    PROSPECTS = "prospects"
    TRANSCRIPTS = "transcripts"
    TEMPLATES = "templates"


class ImportStatus(str, Enum):
    """Status of import job."""

    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class ImportJob(BaseDBModel):
    """Import job tracking model."""

    __tablename__ = "import_jobs"

    # Job configuration
    import_type = Column(SQLEnum(ImportType), nullable=False)
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PENDING)

    # Source file
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)

    # Field mapping
    field_mapping = Column(JSON, default=dict)

    # Progress tracking
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)

    # Results
    imported_ids = Column(JSON, default=list)  # List of created record IDs
    errors = Column(JSON, default=list)  # List of row-level errors

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


class FieldMapping(BaseModel):
    """Field mapping configuration for imports."""

    source_column: str
    target_field: str
    transform: Optional[str] = None  # Optional transformation (e.g., "lowercase", "date")
    default_value: Optional[str] = None


# Pydantic Schemas
class ExportJobCreate(BaseModel):
    """Export job creation schema."""

    export_type: ExportType
    export_format: ExportFormat
    filters: Dict[str, Any] = {}
    record_ids: List[str] = []


class ExportJobSchema(TimestampedSchema):
    """Export job response schema."""

    export_type: ExportType
    export_format: ExportFormat
    status: ExportStatus
    filters: Dict[str, Any] = {}
    record_ids: List[str] = []
    total_records: int = 0
    processed_records: int = 0
    progress_percent: float = 0.0
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[str] = None
    error_message: Optional[str] = None
    user_id: str
    organization_id: str


class ImportJobCreate(BaseModel):
    """Import job creation schema."""

    import_type: ImportType
    field_mapping: Dict[str, FieldMapping] = {}


class ImportJobSchema(TimestampedSchema):
    """Import job response schema."""

    import_type: ImportType
    status: ImportStatus
    original_filename: Optional[str] = None
    field_mapping: Dict[str, Any] = {}
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    progress_percent: float = 0.0
    imported_ids: List[str] = []
    errors: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    user_id: str
    organization_id: str


class ImportError(BaseModel):
    """Import error for a single row."""

    row_number: int
    field: Optional[str] = None
    value: Optional[str] = None
    error: str


class ImportValidationResult(BaseModel):
    """Result of import validation."""

    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[ImportError] = []
    warnings: List[str] = []
    sample_data: List[Dict[str, Any]] = []  # First few rows for preview


class ExportProgress(BaseModel):
    """Export progress update."""

    job_id: str
    status: ExportStatus
    progress_percent: float
    processed_records: int
    total_records: int
    message: Optional[str] = None


class ImportProgress(BaseModel):
    """Import progress update."""

    job_id: str
    status: ImportStatus
    progress_percent: float
    processed_records: int
    total_records: int
    successful_records: int
    failed_records: int
    message: Optional[str] = None
