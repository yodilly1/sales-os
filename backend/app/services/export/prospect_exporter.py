"""Prospect list exporter with HubSpot format support."""

from datetime import datetime
from typing import Any, Dict, List, AsyncIterator

from app.models.export_import import ExportType, ExportFormat
from app.models.prospect import ProspectStatus
from .base import BaseExporter


class ProspectExporter(BaseExporter):
    """Exporter for prospect lists with HubSpot-compatible format."""

    # HubSpot standard field mappings
    HUBSPOT_FIELD_MAP = {
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "Email",
        "phone": "Phone Number",
        "title": "Job Title",
        "company_name": "Company Name",
        "company_domain": "Company Domain Name",
        "linkedin_url": "LinkedIn URL",
        "status": "Lead Status",
        "is_decision_maker": "Decision Maker",
        "tags": "Tags",
        "notes": "Notes",
        "created_at": "Create Date",
    }

    @property
    def export_type(self) -> ExportType:
        return ExportType.PROSPECTS

    @property
    def supported_formats(self) -> List[ExportFormat]:
        return [ExportFormat.JSON, ExportFormat.CSV, ExportFormat.HUBSPOT]

    async def fetch_data(
        self,
        filters: Dict[str, Any],
        record_ids: List[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch prospect data from database.

        Args:
            filters: Filter criteria including:
                - status: Filter by prospect status
                - is_decision_maker: Filter by decision maker flag
                - company_id: Filter by company
                - tags: Filter by tags (list)
                - date_from: Created after date
                - date_to: Created before date
                - include_company: Include company details (default True)
            record_ids: Specific prospect IDs to export

        Yields:
            Prospect data dictionaries
        """
        include_company = filters.get("include_company", True)

        # TODO: Replace with actual database queries
        sample_prospects = [
            {
                "id": "prospect-001",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@acme.com",
                "phone": "+1-555-123-4567",
                "title": "VP of Sales",
                "department": "Sales",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "status": ProspectStatus.QUALIFIED.value,
                "is_decision_maker": True,
                "is_champion": True,
                "notes": "Met at SaaStr conference",
                "tags": ["enterprise", "high-priority", "q1-target"],
                "company": {
                    "id": "company-001",
                    "name": "Acme Corporation",
                    "domain": "acme.com",
                    "industry": "Technology",
                    "size": "enterprise",
                    "employee_count": 5000,
                    "annual_revenue": "$500M",
                },
                "hubspot_id": "hs-12345",
                "created_at": "2024-01-10T09:00:00Z",
            },
            {
                "id": "prospect-002",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@techcorp.io",
                "phone": "+1-555-987-6543",
                "title": "CTO",
                "department": "Engineering",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "status": ProspectStatus.ENGAGED.value,
                "is_decision_maker": True,
                "is_champion": False,
                "notes": "Technical evaluator",
                "tags": ["mid-market", "technical"],
                "company": {
                    "id": "company-002",
                    "name": "TechCorp",
                    "domain": "techcorp.io",
                    "industry": "Software",
                    "size": "mid_market",
                    "employee_count": 250,
                },
                "created_at": "2024-01-12T14:30:00Z",
            },
        ]

        for prospect in sample_prospects:
            # Filter by record IDs
            if record_ids and prospect["id"] not in record_ids:
                continue

            # Filter by status
            if filters.get("status"):
                if prospect["status"] != filters["status"]:
                    continue

            # Filter by decision maker
            if filters.get("is_decision_maker") is not None:
                if prospect["is_decision_maker"] != filters["is_decision_maker"]:
                    continue

            # Filter by tags
            if filters.get("tags"):
                filter_tags = set(filters["tags"])
                prospect_tags = set(prospect.get("tags", []))
                if not filter_tags.intersection(prospect_tags):
                    continue

            # Remove company if not requested
            if not include_company:
                prospect = {k: v for k, v in prospect.items() if k != "company"}

            yield prospect

    async def transform_record(
        self, record: Dict[str, Any], format: ExportFormat
    ) -> Dict[str, Any]:
        """Transform prospect record for export format."""
        if format == ExportFormat.JSON:
            return self._transform_for_json(record)
        elif format == ExportFormat.CSV:
            return self._transform_for_csv(record)
        elif format == ExportFormat.HUBSPOT:
            return self._transform_for_hubspot(record)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _transform_for_json(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for JSON export."""
        return {
            "id": record.get("id"),
            "first_name": record.get("first_name"),
            "last_name": record.get("last_name"),
            "full_name": f"{record.get('first_name', '')} {record.get('last_name', '')}".strip(),
            "email": record.get("email"),
            "phone": record.get("phone"),
            "title": record.get("title"),
            "department": record.get("department"),
            "linkedin_url": record.get("linkedin_url"),
            "status": record.get("status"),
            "is_decision_maker": record.get("is_decision_maker", False),
            "is_champion": record.get("is_champion", False),
            "notes": record.get("notes"),
            "tags": record.get("tags", []),
            "company": record.get("company"),
            "hubspot_id": record.get("hubspot_id"),
            "created_at": record.get("created_at"),
        }

    def _transform_for_csv(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for standard CSV export."""
        company = record.get("company", {}) or {}
        return {
            "id": record.get("id"),
            "first_name": record.get("first_name"),
            "last_name": record.get("last_name"),
            "email": record.get("email"),
            "phone": record.get("phone"),
            "title": record.get("title"),
            "department": record.get("department"),
            "linkedin_url": record.get("linkedin_url"),
            "status": record.get("status"),
            "is_decision_maker": "Yes" if record.get("is_decision_maker") else "No",
            "is_champion": "Yes" if record.get("is_champion") else "No",
            "tags": ", ".join(record.get("tags", [])),
            "notes": record.get("notes", ""),
            "company_name": company.get("name", ""),
            "company_domain": company.get("domain", ""),
            "company_industry": company.get("industry", ""),
            "company_size": company.get("size", ""),
            "company_employee_count": company.get("employee_count", ""),
            "hubspot_id": record.get("hubspot_id", ""),
            "created_at": record.get("created_at"),
        }

    def _transform_for_hubspot(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record for HubSpot import format.

        Uses HubSpot's standard field names for direct import compatibility.
        """
        company = record.get("company", {}) or {}

        # Map status to HubSpot Lead Status
        status_map = {
            "new": "New",
            "contacted": "Contacted",
            "engaged": "Open",
            "qualified": "Qualified",
            "opportunity": "In Progress",
            "customer": "Customer",
            "churned": "Unqualified",
        }

        return {
            "First Name": record.get("first_name", ""),
            "Last Name": record.get("last_name", ""),
            "Email": record.get("email", ""),
            "Phone Number": record.get("phone", ""),
            "Job Title": record.get("title", ""),
            "Company Name": company.get("name", ""),
            "Company Domain Name": company.get("domain", ""),
            "LinkedIn URL": record.get("linkedin_url", ""),
            "Lead Status": status_map.get(record.get("status", ""), "New"),
            "Number of Employees": company.get("employee_count", ""),
            "Industry": company.get("industry", ""),
            "Annual Revenue": company.get("annual_revenue", ""),
            "Notes": record.get("notes", ""),
            # Custom properties (will need to be created in HubSpot)
            "Is Decision Maker": "true" if record.get("is_decision_maker") else "false",
            "Is Champion": "true" if record.get("is_champion") else "false",
            "Tags": ";".join(record.get("tags", [])),  # HubSpot uses semicolon
        }

    async def _export_hubspot_csv(
        self,
        filename: str,
        on_progress=None,
    ) -> str:
        """Export data as HubSpot-compatible CSV.

        HubSpot CSV requirements:
        - UTF-8 encoding
        - Standard column headers matching HubSpot properties
        - Date format: YYYY-MM-DD
        - Boolean: true/false (lowercase)
        - Multi-value: semicolon separated
        """
        filepath = self.export_dir / f"{filename}_hubspot.csv"
        records = []
        processed = 0

        async for record in self.fetch_data(
            self.job.filters or {}, self.job.record_ids or []
        ):
            try:
                transformed = await self.transform_record(record, ExportFormat.HUBSPOT)
                records.append(transformed)
                processed += 1
                if on_progress:
                    on_progress(processed, self.job.total_records)
            except Exception as e:
                self.errors.append({
                    "record_id": record.get("id"),
                    "error": str(e),
                })

        if not records:
            import aiofiles
            async with aiofiles.open(filepath, "w") as f:
                await f.write("")
            return str(filepath)

        # Write HubSpot-formatted CSV
        headers = list(records[0].keys())
        import aiofiles
        async with aiofiles.open(filepath, "w", newline="", encoding="utf-8") as f:
            await f.write(",".join(headers) + "\n")
            for record in records:
                row = [self._csv_escape(str(record.get(h, ""))) for h in headers]
                await f.write(",".join(row) + "\n")

        return str(filepath)
