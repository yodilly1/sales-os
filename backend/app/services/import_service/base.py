"""Base importer class and utilities."""

import csv
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator, Callable, Tuple
from pathlib import Path
import aiofiles

from app.core.config import settings
from app.models.export_import import (
    ImportJob,
    ImportType,
    ImportStatus,
    FieldMapping,
    ImportError as ImportErrorModel,
    ImportValidationResult,
)


class BaseImporter(ABC):
    """Abstract base class for all importers."""

    def __init__(self, job: ImportJob):
        """Initialize importer with job context."""
        self.job = job
        self.errors: List[ImportErrorModel] = []
        self.warnings: List[str] = []
        self.imported_ids: List[str] = []

    @property
    @abstractmethod
    def import_type(self) -> ImportType:
        """Return the import type this importer handles."""
        pass

    @property
    @abstractmethod
    def required_fields(self) -> List[str]:
        """Return list of required field names."""
        pass

    @property
    @abstractmethod
    def optional_fields(self) -> List[str]:
        """Return list of optional field names."""
        pass

    @abstractmethod
    async def validate_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Tuple[bool, List[ImportErrorModel]]:
        """Validate a single row of data.

        Args:
            row: Mapped row data
            row_number: Row number (1-indexed)

        Returns:
            Tuple of (is_valid, list of errors)
        """
        pass

    @abstractmethod
    async def import_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Optional[str]:
        """Import a single row of data.

        Args:
            row: Validated and mapped row data
            row_number: Row number (1-indexed)

        Returns:
            ID of created record, or None if failed
        """
        pass

    async def validate_file(self, file_path: str) -> ImportValidationResult:
        """Validate the entire import file before processing.

        Args:
            file_path: Path to the import file

        Returns:
            Validation result with errors and warnings
        """
        errors: List[ImportErrorModel] = []
        warnings: List[str] = []
        sample_data: List[Dict[str, Any]] = []
        total_rows = 0
        valid_rows = 0

        # Determine file type and read
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            rows = await self._read_csv(file_path)
        elif path.suffix.lower() == ".json":
            rows = await self._read_json(file_path)
        else:
            return ImportValidationResult(
                is_valid=False,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[
                    ImportErrorModel(
                        row_number=0,
                        error=f"Unsupported file type: {path.suffix}",
                    )
                ],
            )

        # Get field mapping
        field_mapping = self.job.field_mapping or {}

        for row_number, raw_row in enumerate(rows, start=1):
            total_rows += 1

            # Apply field mapping
            mapped_row = self._apply_mapping(raw_row, field_mapping)

            # Store sample data (first 5 rows)
            if len(sample_data) < 5:
                sample_data.append(mapped_row)

            # Validate row
            is_valid, row_errors = await self.validate_row(mapped_row, row_number)

            if is_valid:
                valid_rows += 1
            else:
                errors.extend(row_errors)

        # Check for missing required fields in mapping
        source_columns = set(rows[0].keys()) if rows else set()
        mapped_targets = {m.get("target_field") for m in field_mapping.values() if isinstance(m, dict)}

        for required_field in self.required_fields:
            if required_field not in mapped_targets:
                # Check if field exists directly in source
                if required_field not in source_columns:
                    warnings.append(
                        f"Required field '{required_field}' is not mapped. "
                        f"Please map a source column to this field."
                    )

        return ImportValidationResult(
            is_valid=len(errors) == 0 and len(warnings) == 0,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=total_rows - valid_rows,
            errors=errors,
            warnings=warnings,
            sample_data=sample_data,
        )

    async def execute_import(
        self,
        file_path: str,
        on_progress: Optional[Callable[[int, int, int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """Execute the import process.

        Args:
            file_path: Path to the import file
            on_progress: Callback (processed, total, successful, failed)

        Returns:
            Tuple of (successful_count, failed_count, imported_ids)
        """
        # Read file
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            rows = await self._read_csv(file_path)
        elif path.suffix.lower() == ".json":
            rows = await self._read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        # Get field mapping
        field_mapping = self.job.field_mapping or {}

        successful = 0
        failed = 0
        total = len(rows)

        for row_number, raw_row in enumerate(rows, start=1):
            # Apply field mapping
            mapped_row = self._apply_mapping(raw_row, field_mapping)

            # Validate row
            is_valid, row_errors = await self.validate_row(mapped_row, row_number)

            if not is_valid:
                self.errors.extend(row_errors)
                failed += 1
                if on_progress:
                    on_progress(row_number, total, successful, failed)
                continue

            # Import row
            try:
                record_id = await self.import_row(mapped_row, row_number)
                if record_id:
                    self.imported_ids.append(record_id)
                    successful += 1
                else:
                    failed += 1
                    self.errors.append(
                        ImportErrorModel(
                            row_number=row_number,
                            error="Import failed without error",
                        )
                    )
            except Exception as e:
                failed += 1
                self.errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        error=str(e),
                    )
                )

            if on_progress:
                on_progress(row_number, total, successful, failed)

        return successful, failed, self.imported_ids

    async def _read_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Read CSV file and return list of dictionaries."""
        rows = []
        async with aiofiles.open(file_path, "r", encoding="utf-8-sig") as f:
            content = await f.read()

        # Parse CSV
        reader = csv.DictReader(content.splitlines())
        for row in reader:
            # Clean up keys and values
            cleaned_row = {
                k.strip(): v.strip() if isinstance(v, str) else v
                for k, v in row.items()
                if k  # Skip empty keys
            }
            rows.append(cleaned_row)

        return rows

    async def _read_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Read JSON file and return list of dictionaries."""
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()

        data = json.loads(content)

        # Handle both array and object with 'records' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "records" in data:
            return data["records"]
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("Invalid JSON format")

    def _apply_mapping(
        self, row: Dict[str, Any], mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field mapping to a row.

        Args:
            row: Original row data
            mapping: Field mapping configuration

        Returns:
            Mapped row data
        """
        if not mapping:
            return row

        result = {}

        for source_col, config in mapping.items():
            if source_col not in row:
                continue

            value = row[source_col]

            # Handle both dict config and simple string target
            if isinstance(config, dict):
                target_field = config.get("target_field", source_col)
                transform = config.get("transform")
                default = config.get("default_value")

                # Apply transform
                if transform and value:
                    value = self._apply_transform(value, transform)

                # Apply default if empty
                if not value and default:
                    value = default
            else:
                target_field = config

            result[target_field] = value

        # Include unmapped fields
        for key, value in row.items():
            if key not in mapping:
                result[key] = value

        return result

    def _apply_transform(self, value: str, transform: str) -> str:
        """Apply a transformation to a value.

        Args:
            value: Original value
            transform: Transform name

        Returns:
            Transformed value
        """
        transforms = {
            "lowercase": lambda v: v.lower(),
            "uppercase": lambda v: v.upper(),
            "titlecase": lambda v: v.title(),
            "trim": lambda v: v.strip(),
            "email_normalize": lambda v: v.lower().strip(),
        }

        if transform in transforms:
            return transforms[transform](value)

        return value

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        import re

        # Allow various phone formats
        pattern = r"^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$"
        return bool(re.match(pattern, phone))

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        import re

        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url, re.IGNORECASE))
