"""Batch processor for CSV imports and bulk prospect enrichment."""

import asyncio
import csv
import io
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, BinaryIO, Optional
from uuid import uuid4

from app.core.config import settings
from app.models.prospect import (
    ProspectCreate,
    ProspectEnriched,
    ProspectBulkImport,
    ProspectBulkImportResult,
    EnrichmentSource,
)

from .service import EnrichmentService
from .hubspot_mapper import HubSpotFieldMapper

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processor for bulk prospect imports and enrichment."""

    # Column name mappings for common CSV formats
    COLUMN_MAPPINGS = {
        # Standard field names
        "first_name": ["first_name", "firstname", "first", "fname", "given_name"],
        "last_name": ["last_name", "lastname", "last", "lname", "surname", "family_name"],
        "full_name": ["full_name", "fullname", "name", "contact_name", "attendee_name"],
        "email": ["email", "email_address", "e-mail", "emailaddress", "work_email"],
        "title": ["title", "job_title", "jobtitle", "position", "role"],
        "company_name": ["company", "company_name", "companyname", "organization", "org", "employer"],
        "company_domain": ["domain", "company_domain", "website", "company_website", "url"],
    }

    # Event platform specific mappings
    EVENT_PLATFORM_MAPPINGS = {
        "eventbrite": {
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "title": "job_title",
            "company_name": "company",
        },
        "hopin": {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "title": "Job Title",
            "company_name": "Company",
        },
        "zoom": {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "User Email",
            "company_name": "Company",
        },
        "hubspot": {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "title": "Job Title",
            "company_name": "Company Name",
        },
        "salesforce": {
            "first_name": "FirstName",
            "last_name": "LastName",
            "email": "Email",
            "title": "Title",
            "company_name": "Company",
        },
    }

    def __init__(
        self,
        enrichment_service: Optional[EnrichmentService] = None,
        batch_size: int = 50,
        max_concurrent: int = 10,
    ):
        """
        Initialize batch processor.

        Args:
            enrichment_service: Service for enriching prospects
            batch_size: Number of prospects per batch
            max_concurrent: Maximum concurrent enrichment tasks
        """
        self.enrichment_service = enrichment_service or EnrichmentService()
        self.batch_size = batch_size or settings.enrichment_batch_size
        self.max_concurrent = max_concurrent
        self.hubspot_mapper = HubSpotFieldMapper()

    async def close(self) -> None:
        """Close resources."""
        await self.enrichment_service.close()

    async def process_csv(
        self,
        file_content: str | bytes | BinaryIO,
        source: str = "csv_import",
        event_name: Optional[str] = None,
        event_date: Optional[datetime] = None,
        auto_enrich: bool = True,
        sync_to_hubspot: bool = False,
        platform: Optional[str] = None,
        delimiter: str = ",",
    ) -> ProspectBulkImportResult:
        """
        Process CSV file and optionally enrich prospects.

        Args:
            file_content: CSV content as string, bytes, or file object
            source: Source identifier for the import
            event_name: Name of event (if event attendee list)
            event_date: Date of event
            auto_enrich: Whether to automatically enrich prospects
            sync_to_hubspot: Whether to sync to HubSpot after enrichment
            platform: Event platform for column mapping (eventbrite, hopin, etc.)
            delimiter: CSV delimiter character

        Returns:
            Import result with statistics and enriched prospects
        """
        # Parse CSV
        prospects, parse_errors = self._parse_csv(file_content, platform, delimiter)

        if not prospects:
            return ProspectBulkImportResult(
                total_records=0,
                successful=0,
                failed=len(parse_errors),
                duplicates=0,
                enriched=0,
                errors=parse_errors,
            )

        # Deduplicate by email
        unique_prospects, duplicates = self._deduplicate(prospects)

        result = ProspectBulkImportResult(
            total_records=len(prospects),
            successful=len(unique_prospects),
            failed=len(parse_errors),
            duplicates=duplicates,
            enriched=0,
            errors=parse_errors,
        )

        # Enrich if requested
        if auto_enrich and unique_prospects:
            enriched_prospects = await self._enrich_batch(
                unique_prospects,
                sync_to_hubspot=sync_to_hubspot,
            )
            result.prospects = enriched_prospects
            result.enriched = len(enriched_prospects)

        return result

    async def process_event_list(
        self,
        attendees: list[dict[str, Any]],
        event_name: str,
        event_date: Optional[datetime] = None,
        platform: Optional[str] = None,
        auto_enrich: bool = True,
        sync_to_hubspot: bool = False,
    ) -> ProspectBulkImportResult:
        """
        Process event attendee list.

        Args:
            attendees: List of attendee dictionaries
            event_name: Name of the event
            event_date: Date of the event
            platform: Event platform for field mapping
            auto_enrich: Whether to automatically enrich
            sync_to_hubspot: Whether to sync to HubSpot

        Returns:
            Import result
        """
        prospects = []

        # Get platform-specific mapping
        field_mapping = self.EVENT_PLATFORM_MAPPINGS.get(platform, {})

        for attendee in attendees:
            prospect = self._map_attendee_to_prospect(attendee, field_mapping)
            if prospect:
                prospects.append(prospect)

        return await self._process_prospect_list(
            prospects,
            source=f"event:{platform or 'unknown'}",
            event_name=event_name,
            event_date=event_date,
            auto_enrich=auto_enrich,
            sync_to_hubspot=sync_to_hubspot,
        )

    async def enrich_prospects_streaming(
        self,
        prospects: list[ProspectCreate],
        sync_to_hubspot: bool = False,
    ) -> AsyncGenerator[ProspectEnriched, None]:
        """
        Enrich prospects and yield results as they complete.

        Args:
            prospects: List of prospects to enrich
            sync_to_hubspot: Whether to prepare HubSpot mapping

        Yields:
            Enriched prospects as they complete
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def enrich_with_limit(prospect: ProspectCreate) -> Optional[ProspectEnriched]:
            async with semaphore:
                result = await self.enrichment_service.enrich_prospect(prospect)
                if result.success and result.prospect:
                    if sync_to_hubspot:
                        self.hubspot_mapper.map_prospect_to_hubspot(result.prospect)
                    return result.prospect
                return None

        # Create tasks for all prospects
        for batch_start in range(0, len(prospects), self.batch_size):
            batch = prospects[batch_start:batch_start + self.batch_size]
            tasks = [enrich_with_limit(p) for p in batch]

            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    yield result

    def _parse_csv(
        self,
        file_content: str | bytes | BinaryIO,
        platform: Optional[str] = None,
        delimiter: str = ",",
    ) -> tuple[list[ProspectCreate], list[dict]]:
        """Parse CSV content into prospect list."""
        prospects = []
        errors = []

        # Handle different input types
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8-sig")  # Handle BOM
        elif hasattr(file_content, "read"):
            file_content = file_content.read()
            if isinstance(file_content, bytes):
                file_content = file_content.decode("utf-8-sig")

        # Parse CSV
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

        # Detect column mapping
        if reader.fieldnames:
            column_map = self._detect_column_mapping(reader.fieldnames, platform)
        else:
            errors.append({"row": 0, "error": "No headers found in CSV"})
            return [], errors

        for row_num, row in enumerate(reader, start=2):
            try:
                prospect_data = {}

                for field, csv_column in column_map.items():
                    if csv_column and csv_column in row:
                        value = row[csv_column].strip() if row[csv_column] else None
                        if value:
                            prospect_data[field] = value

                # Skip rows without minimum data
                if not prospect_data.get("email") and not prospect_data.get("full_name"):
                    if not prospect_data.get("first_name") or not prospect_data.get("last_name"):
                        errors.append({
                            "row": row_num,
                            "error": "Missing required fields (email or name)",
                        })
                        continue

                prospect = ProspectCreate(**prospect_data)
                prospects.append(prospect)

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return prospects, errors

    def _detect_column_mapping(
        self,
        headers: list[str],
        platform: Optional[str] = None,
    ) -> dict[str, Optional[str]]:
        """Detect which CSV columns map to prospect fields."""
        column_map = {}

        # Use platform-specific mapping if available
        if platform and platform in self.EVENT_PLATFORM_MAPPINGS:
            platform_map = self.EVENT_PLATFORM_MAPPINGS[platform]
            for field, csv_col in platform_map.items():
                if csv_col in headers:
                    column_map[field] = csv_col
            return column_map

        # Auto-detect mapping
        headers_lower = {h.lower().strip(): h for h in headers}

        for field, possible_names in self.COLUMN_MAPPINGS.items():
            column_map[field] = None
            for name in possible_names:
                if name in headers_lower:
                    column_map[field] = headers_lower[name]
                    break

        return column_map

    def _map_attendee_to_prospect(
        self,
        attendee: dict[str, Any],
        field_mapping: dict[str, str],
    ) -> Optional[ProspectCreate]:
        """Map event attendee data to prospect."""
        prospect_data = {}

        for field in ["first_name", "last_name", "full_name", "email", "title", "company_name", "company_domain"]:
            # Check field mapping
            mapped_key = field_mapping.get(field, field)
            if mapped_key in attendee and attendee[mapped_key]:
                prospect_data[field] = str(attendee[mapped_key]).strip()

        if not prospect_data:
            return None

        return ProspectCreate(**prospect_data)

    def _deduplicate(
        self,
        prospects: list[ProspectCreate],
    ) -> tuple[list[ProspectCreate], int]:
        """Remove duplicate prospects by email."""
        seen_emails: set[str] = set()
        unique = []
        duplicates = 0

        for prospect in prospects:
            email = prospect.email.lower() if prospect.email else None

            if email:
                if email in seen_emails:
                    duplicates += 1
                    continue
                seen_emails.add(email)

            unique.append(prospect)

        return unique, duplicates

    async def _process_prospect_list(
        self,
        prospects: list[ProspectCreate],
        source: str,
        event_name: Optional[str] = None,
        event_date: Optional[datetime] = None,
        auto_enrich: bool = True,
        sync_to_hubspot: bool = False,
    ) -> ProspectBulkImportResult:
        """Process a list of prospects."""
        unique_prospects, duplicates = self._deduplicate(prospects)

        result = ProspectBulkImportResult(
            total_records=len(prospects),
            successful=len(unique_prospects),
            failed=0,
            duplicates=duplicates,
            enriched=0,
        )

        if auto_enrich and unique_prospects:
            enriched = await self._enrich_batch(unique_prospects, sync_to_hubspot)
            result.prospects = enriched
            result.enriched = len(enriched)

        return result

    async def _enrich_batch(
        self,
        prospects: list[ProspectCreate],
        sync_to_hubspot: bool = False,
    ) -> list[ProspectEnriched]:
        """Enrich a batch of prospects concurrently."""
        enriched = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def enrich_one(prospect: ProspectCreate) -> Optional[ProspectEnriched]:
            async with semaphore:
                try:
                    result = await self.enrichment_service.enrich_prospect(prospect)
                    if result.success and result.prospect:
                        if sync_to_hubspot:
                            self.hubspot_mapper.map_prospect_to_hubspot(result.prospect)
                        return result.prospect
                except Exception as e:
                    logger.error(f"Error enriching prospect: {e}")
                return None

        # Process in batches
        for batch_start in range(0, len(prospects), self.batch_size):
            batch = prospects[batch_start:batch_start + self.batch_size]
            tasks = [enrich_one(p) for p in batch]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    enriched.append(result)

            # Small delay between batches to respect rate limits
            if batch_start + self.batch_size < len(prospects):
                await asyncio.sleep(1)

        return enriched


def parse_csv_preview(
    file_content: str | bytes,
    max_rows: int = 5,
) -> dict[str, Any]:
    """
    Parse CSV and return preview with detected columns.

    Args:
        file_content: CSV content
        max_rows: Maximum rows to preview

    Returns:
        Preview information including headers and sample data
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(file_content))

    headers = reader.fieldnames or []
    rows = []

    for i, row in enumerate(reader):
        if i >= max_rows:
            break
        rows.append(row)

    # Detect mappings
    processor = BatchProcessor()
    column_map = processor._detect_column_mapping(headers)

    return {
        "headers": headers,
        "detected_mapping": column_map,
        "sample_rows": rows,
        "total_columns": len(headers),
    }
