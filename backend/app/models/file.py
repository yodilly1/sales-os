"""File models for database and API schemas."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class FileType(str, enum.Enum):
    """Type of file being uploaded."""

    TRANSCRIPT = "transcript"
    DATA = "data"
    ASSET = "asset"


class FileStatus(str, enum.Enum):
    """Status of the file in the processing pipeline."""

    PENDING = "pending"  # Upload initiated but not complete
    UPLOADING = "uploading"  # Upload in progress (chunked)
    UPLOADED = "uploaded"  # Upload complete, awaiting processing
    PROCESSING = "processing"  # Being processed
    COMPLETED = "completed"  # Processing complete
    FAILED = "failed"  # Processing failed
    EXPIRED = "expired"  # Temporary file expired


class ProcessingStatus(str, enum.Enum):
    """Status of a processing job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# SQLAlchemy Models


class File(Base):
    """File metadata stored in the database."""

    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # File info
    original_filename = Column(String(255), nullable=False)
    storage_key = Column(String(512), nullable=False, unique=True)
    file_type = Column(Enum(FileType), nullable=False)
    mime_type = Column(String(128), nullable=True)
    extension = Column(String(16), nullable=False)
    size_bytes = Column(Integer, nullable=False)

    # Status
    status = Column(Enum(FileStatus), nullable=False, default=FileStatus.PENDING)
    error_message = Column(Text, nullable=True)

    # Multipart upload tracking
    upload_id = Column(String(256), nullable=True)  # S3 multipart upload ID
    total_chunks = Column(Integer, nullable=True)
    uploaded_chunks = Column(Integer, default=0)

    # Metadata
    metadata = Column(JSON, nullable=True, default=dict)
    checksum = Column(String(64), nullable=True)  # SHA-256

    # Flags
    is_temporary = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    chunks = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")
    processing_jobs = relationship(
        "FileProcessingJob", back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_files_org_status", "organization_id", "status"),
        Index("idx_files_user_type", "user_id", "file_type"),
        Index("idx_files_expires_at", "expires_at"),
        Index("idx_files_created_at", "created_at"),
    )


class FileChunk(Base):
    """Tracks individual chunks for multipart uploads."""

    __tablename__ = "file_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)

    chunk_number = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    etag = Column(String(64), nullable=True)  # S3 ETag
    checksum = Column(String(64), nullable=True)

    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())

    file = relationship("File", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_file_number", "file_id", "chunk_number", unique=True),
    )


class FileProcessingJob(Base):
    """Tracks file processing jobs in the queue."""

    __tablename__ = "file_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)

    job_type = Column(String(64), nullable=False)  # e.g., "parse_transcript", "validate_csv"
    status = Column(Enum(ProcessingStatus), nullable=False, default=ProcessingStatus.QUEUED)
    priority = Column(Integer, default=0)  # Higher = more priority

    # Job details
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Retry tracking
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime, nullable=True)

    # Timing
    queued_at = Column(DateTime, nullable=False, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    file = relationship("File", back_populates="processing_jobs")

    __table_args__ = (
        Index("idx_jobs_status_priority", "status", "priority"),
        Index("idx_jobs_file_id", "file_id"),
        Index("idx_jobs_next_retry", "next_retry_at"),
    )


# Pydantic Schemas


class FileBase(BaseModel):
    """Base file schema."""

    original_filename: str = Field(..., max_length=255)
    file_type: FileType
    mime_type: Optional[str] = None
    metadata: Optional[dict] = None


class FileCreate(FileBase):
    """Schema for creating a file record."""

    size_bytes: int = Field(..., gt=0)
    is_temporary: bool = False


class FileChunkInfo(BaseModel):
    """Information about a file chunk."""

    chunk_number: int
    size_bytes: int
    etag: Optional[str] = None
    checksum: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileResponse(BaseModel):
    """File response schema."""

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID

    original_filename: str
    file_type: FileType
    mime_type: Optional[str]
    extension: str
    size_bytes: int

    status: FileStatus
    error_message: Optional[str]

    total_chunks: Optional[int]
    uploaded_chunks: int

    metadata: Optional[dict]
    checksum: Optional[str]

    is_temporary: bool
    is_public: bool
    expires_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FileUploadInitRequest(BaseModel):
    """Request to initiate a file upload."""

    filename: str = Field(..., max_length=255)
    size_bytes: int = Field(..., gt=0)
    content_type: Optional[str] = None
    file_type: Optional[FileType] = None  # Auto-detected if not provided
    metadata: Optional[dict] = None
    is_temporary: bool = False


class FileUploadInitResponse(BaseModel):
    """Response after initiating file upload."""

    file_id: uuid.UUID
    upload_id: Optional[str] = None  # For multipart uploads
    is_multipart: bool
    chunk_size: int
    total_chunks: int
    storage_key: str


class ChunkUploadRequest(BaseModel):
    """Request to upload a file chunk."""

    chunk_number: int = Field(..., ge=1)
    checksum: Optional[str] = None  # SHA-256 of chunk data


class ChunkUploadResponse(BaseModel):
    """Response after uploading a chunk."""

    chunk_number: int
    etag: str
    uploaded_chunks: int
    total_chunks: int
    is_complete: bool


class FileCompleteRequest(BaseModel):
    """Request to complete a file upload."""

    file_id: uuid.UUID
    checksum: Optional[str] = None  # SHA-256 of complete file


class ProcessingJobResponse(BaseModel):
    """Processing job response schema."""

    id: uuid.UUID
    file_id: uuid.UUID
    job_type: str
    status: ProcessingStatus
    priority: int

    input_data: Optional[dict]
    output_data: Optional[dict]
    error_message: Optional[str]

    attempts: int
    max_attempts: int

    queued_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FileListRequest(BaseModel):
    """Request to list files."""

    file_type: Optional[FileType] = None
    status: Optional[FileStatus] = None
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


class FileListResponse(BaseModel):
    """Response with list of files."""

    files: list[FileResponse]
    total: int
    limit: int
    offset: int


class FileValidationError(BaseModel):
    """File validation error details."""

    code: str
    message: str
    field: Optional[str] = None


class FileValidationResponse(BaseModel):
    """Response from file validation."""

    is_valid: bool
    errors: list[FileValidationError] = []
    warnings: list[str] = []
    file_info: Optional[dict] = None
