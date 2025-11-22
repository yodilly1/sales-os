"""File validation service for type checking and content validation."""

import csv
import io
import json
import mimetypes
import re
from pathlib import Path
from typing import BinaryIO, Optional

from app.core.config import settings
from app.models.file import FileType, FileValidationError, FileValidationResponse


class FileValidationService:
    """Service for validating uploaded files.

    Validates file types, extensions, content, and structure
    for transcripts, data files, and assets.
    """

    # MIME type mappings
    TRANSCRIPT_MIME_TYPES = {
        ".txt": "text/plain",
        ".vtt": "text/vtt",
        ".srt": "text/plain",  # SRT is technically text/plain
        ".json": "application/json",
    }

    DATA_MIME_TYPES = {
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    ASSET_MIME_TYPES = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
    }

    # Magic bytes for file type verification
    MAGIC_BYTES = {
        "image/png": b"\x89PNG\r\n\x1a\n",
        "image/jpeg": b"\xff\xd8\xff",
        "application/pdf": b"%PDF",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": b"PK",
    }

    def __init__(self):
        """Initialize validation service."""
        self.max_file_size = settings.max_file_size_bytes
        self.allowed_extensions = settings.all_allowed_extensions

    def get_file_type(self, filename: str) -> Optional[FileType]:
        """Determine file type from filename extension.

        Args:
            filename: Original filename

        Returns:
            FileType or None if extension not recognized
        """
        ext = Path(filename).suffix.lower()

        if ext in settings.allowed_transcript_extensions:
            return FileType.TRANSCRIPT
        elif ext in settings.allowed_data_extensions:
            return FileType.DATA
        elif ext in settings.allowed_asset_extensions:
            return FileType.ASSET

        return None

    def get_mime_type(self, filename: str) -> Optional[str]:
        """Get MIME type from filename.

        Args:
            filename: Original filename

        Returns:
            MIME type string or None
        """
        ext = Path(filename).suffix.lower()

        # Check our explicit mappings first
        all_types = {
            **self.TRANSCRIPT_MIME_TYPES,
            **self.DATA_MIME_TYPES,
            **self.ASSET_MIME_TYPES,
        }

        if ext in all_types:
            return all_types[ext]

        # Fall back to mimetypes library
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type

    def validate_extension(self, filename: str) -> tuple[bool, Optional[str]]:
        """Validate file extension.

        Args:
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        ext = Path(filename).suffix.lower()

        if not ext:
            return False, "File must have an extension"

        if ext not in self.allowed_extensions:
            allowed = ", ".join(self.allowed_extensions)
            return False, f"File extension '{ext}' not allowed. Allowed: {allowed}"

        return True, None

    def validate_size(self, size_bytes: int) -> tuple[bool, Optional[str]]:
        """Validate file size.

        Args:
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if size_bytes <= 0:
            return False, "File size must be greater than 0"

        if size_bytes > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            return False, f"File size exceeds maximum of {max_mb}MB"

        return True, None

    async def validate_content(
        self,
        file_data: BinaryIO | bytes,
        filename: str,
        file_type: FileType,
    ) -> FileValidationResponse:
        """Validate file content based on type.

        Args:
            file_data: File content
            filename: Original filename
            file_type: Expected file type

        Returns:
            FileValidationResponse with validation results
        """
        errors: list[FileValidationError] = []
        warnings: list[str] = []
        file_info: dict = {}

        # Get content as bytes
        if isinstance(file_data, bytes):
            content = file_data
        else:
            content = file_data.read()
            file_data.seek(0)  # Reset position

        ext = Path(filename).suffix.lower()

        # Validate magic bytes for binary files
        mime_type = self.get_mime_type(filename)
        if mime_type in self.MAGIC_BYTES:
            expected_magic = self.MAGIC_BYTES[mime_type]
            if not content.startswith(expected_magic):
                errors.append(
                    FileValidationError(
                        code="INVALID_CONTENT",
                        message=f"File content doesn't match expected format for {ext}",
                    )
                )
                return FileValidationResponse(is_valid=False, errors=errors)

        # Type-specific validation
        if file_type == FileType.TRANSCRIPT:
            result = await self._validate_transcript(content, ext)
            errors.extend(result.get("errors", []))
            warnings.extend(result.get("warnings", []))
            file_info.update(result.get("info", {}))

        elif file_type == FileType.DATA:
            result = await self._validate_data_file(content, ext)
            errors.extend(result.get("errors", []))
            warnings.extend(result.get("warnings", []))
            file_info.update(result.get("info", {}))

        elif file_type == FileType.ASSET:
            result = await self._validate_asset(content, ext)
            errors.extend(result.get("errors", []))
            warnings.extend(result.get("warnings", []))
            file_info.update(result.get("info", {}))

        return FileValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_info=file_info if file_info else None,
        )

    async def _validate_transcript(self, content: bytes, ext: str) -> dict:
        """Validate transcript file content.

        Args:
            content: File content as bytes
            ext: File extension

        Returns:
            Dict with errors, warnings, and info
        """
        errors = []
        warnings = []
        info = {}

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
                warnings.append("File encoding is not UTF-8, using Latin-1")
            except Exception:
                errors.append(
                    FileValidationError(
                        code="ENCODING_ERROR",
                        message="Unable to decode file as text",
                    )
                )
                return {"errors": errors}

        if ext == ".json":
            try:
                data = json.loads(text)
                info["type"] = "json"
                if isinstance(data, dict):
                    info["keys"] = list(data.keys())[:10]
                elif isinstance(data, list):
                    info["items"] = len(data)
            except json.JSONDecodeError as e:
                errors.append(
                    FileValidationError(
                        code="INVALID_JSON",
                        message=f"Invalid JSON: {e.msg}",
                    )
                )

        elif ext == ".vtt":
            if not text.strip().startswith("WEBVTT"):
                errors.append(
                    FileValidationError(
                        code="INVALID_VTT",
                        message="VTT file must start with 'WEBVTT'",
                    )
                )
            else:
                # Count cues
                cue_pattern = r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}"
                cues = re.findall(cue_pattern, text)
                info["cue_count"] = len(cues)

        elif ext == ".srt":
            # Validate SRT format (numbered entries with timestamps)
            srt_pattern = r"^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}"
            if not re.search(srt_pattern, text, re.MULTILINE):
                errors.append(
                    FileValidationError(
                        code="INVALID_SRT",
                        message="SRT file format is invalid",
                    )
                )
            else:
                entries = re.findall(r"^\d+\s*$", text, re.MULTILINE)
                info["entry_count"] = len(entries)

        elif ext == ".txt":
            # Basic text validation
            lines = text.split("\n")
            info["line_count"] = len(lines)
            info["char_count"] = len(text)

            if len(text.strip()) == 0:
                errors.append(
                    FileValidationError(
                        code="EMPTY_FILE",
                        message="Transcript file is empty",
                    )
                )

        return {"errors": errors, "warnings": warnings, "info": info}

    async def _validate_data_file(self, content: bytes, ext: str) -> dict:
        """Validate data file content (CSV, XLSX).

        Args:
            content: File content as bytes
            ext: File extension

        Returns:
            Dict with errors, warnings, and info
        """
        errors = []
        warnings = []
        info = {}

        if ext == ".csv":
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = content.decode("latin-1")
                    warnings.append("CSV encoding is not UTF-8")
                except Exception:
                    errors.append(
                        FileValidationError(
                            code="ENCODING_ERROR",
                            message="Unable to decode CSV file",
                        )
                    )
                    return {"errors": errors}

            try:
                reader = csv.reader(io.StringIO(text))
                rows = list(reader)

                if len(rows) == 0:
                    errors.append(
                        FileValidationError(
                            code="EMPTY_CSV",
                            message="CSV file is empty",
                        )
                    )
                else:
                    headers = rows[0] if rows else []
                    info["headers"] = headers
                    info["row_count"] = len(rows) - 1  # Exclude header
                    info["column_count"] = len(headers)

                    # Check for consistent column count
                    col_counts = set(len(row) for row in rows)
                    if len(col_counts) > 1:
                        warnings.append(
                            f"Inconsistent column counts detected: {col_counts}"
                        )

            except csv.Error as e:
                errors.append(
                    FileValidationError(
                        code="INVALID_CSV",
                        message=f"Invalid CSV format: {e}",
                    )
                )

        elif ext == ".xlsx":
            # Basic XLSX validation (magic bytes already checked)
            # Full parsing would require openpyxl - defer to processing stage
            info["type"] = "xlsx"
            info["size_bytes"] = len(content)

            # Check if file is not too small to be valid
            if len(content) < 100:
                errors.append(
                    FileValidationError(
                        code="INVALID_XLSX",
                        message="XLSX file appears to be corrupted or empty",
                    )
                )

        return {"errors": errors, "warnings": warnings, "info": info}

    async def _validate_asset(self, content: bytes, ext: str) -> dict:
        """Validate asset file content (images, PDFs).

        Args:
            content: File content as bytes
            ext: File extension

        Returns:
            Dict with errors, warnings, and info
        """
        errors = []
        warnings = []
        info = {"size_bytes": len(content)}

        if ext in (".png", ".jpg", ".jpeg"):
            # Basic image validation - deeper validation deferred to processing
            info["type"] = "image"

            # Size limits for images
            max_image_size = 20 * 1024 * 1024  # 20MB for images
            if len(content) > max_image_size:
                errors.append(
                    FileValidationError(
                        code="IMAGE_TOO_LARGE",
                        message="Image exceeds maximum size of 20MB",
                    )
                )

        elif ext == ".pdf":
            info["type"] = "pdf"

            # Check for PDF version
            if content[:8].startswith(b"%PDF-"):
                version = content[5:8].decode("ascii", errors="ignore")
                info["pdf_version"] = version

            # Check for EOF marker
            if not content.rstrip().endswith(b"%%EOF"):
                warnings.append("PDF file may be truncated (missing EOF marker)")

        return {"errors": errors, "warnings": warnings, "info": info}

    def validate_filename(self, filename: str) -> tuple[bool, Optional[str]]:
        """Validate filename for security issues.

        Args:
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "Filename contains invalid characters"

        # Check for null bytes
        if "\x00" in filename:
            return False, "Filename contains invalid characters"

        # Check length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"

        # Check for hidden files (Unix-style)
        if filename.startswith("."):
            return False, "Hidden files not allowed"

        # Check for reserved Windows names
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved:
            return False, "Reserved filename not allowed"

        return True, None

    async def validate_file(
        self,
        filename: str,
        size_bytes: int,
        content: Optional[BinaryIO | bytes] = None,
    ) -> FileValidationResponse:
        """Perform complete file validation.

        Args:
            filename: Original filename
            size_bytes: File size in bytes
            content: Optional file content for deep validation

        Returns:
            FileValidationResponse with all validation results
        """
        errors = []
        warnings = []

        # Validate filename
        is_valid, error = self.validate_filename(filename)
        if not is_valid:
            errors.append(
                FileValidationError(
                    code="INVALID_FILENAME",
                    message=error,
                    field="filename",
                )
            )

        # Validate extension
        is_valid, error = self.validate_extension(filename)
        if not is_valid:
            errors.append(
                FileValidationError(
                    code="INVALID_EXTENSION",
                    message=error,
                    field="filename",
                )
            )

        # Validate size
        is_valid, error = self.validate_size(size_bytes)
        if not is_valid:
            errors.append(
                FileValidationError(
                    code="INVALID_SIZE",
                    message=error,
                    field="size_bytes",
                )
            )

        # If basic validation failed, return early
        if errors:
            return FileValidationResponse(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # Get file type
        file_type = self.get_file_type(filename)

        # Content validation if provided
        file_info = None
        if content is not None and file_type is not None:
            content_result = await self.validate_content(content, filename, file_type)
            errors.extend(content_result.errors)
            warnings.extend(content_result.warnings)
            file_info = content_result.file_info

        return FileValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_info=file_info,
        )
