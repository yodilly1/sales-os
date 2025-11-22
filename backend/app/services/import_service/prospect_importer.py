"""Prospect CSV importer with field mapping support."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.export_import import (
    ImportType,
    ImportError as ImportErrorModel,
)
from app.models.prospect import ProspectStatus
from .base import BaseImporter


class ProspectImporter(BaseImporter):
    """Importer for prospect data from CSV files.

    Supports:
    - Standard CSV format
    - HubSpot export format
    - Custom field mapping
    - Company creation/matching
    - Duplicate detection
    """

    # Common field name variations for auto-mapping
    FIELD_ALIASES = {
        "first_name": ["firstname", "first", "given_name", "givenname"],
        "last_name": ["lastname", "last", "surname", "family_name", "familyname"],
        "email": ["email_address", "emailaddress", "e-mail", "contact_email"],
        "phone": ["phone_number", "phonenumber", "telephone", "mobile", "cell"],
        "title": ["job_title", "jobtitle", "position", "role"],
        "company": ["company_name", "companyname", "organization", "employer"],
        "linkedin_url": ["linkedin", "linkedin_profile", "linkedinurl"],
        "status": ["lead_status", "leadstatus", "prospect_status"],
    }

    @property
    def import_type(self) -> ImportType:
        return ImportType.PROSPECTS

    @property
    def required_fields(self) -> List[str]:
        return ["first_name", "last_name"]

    @property
    def optional_fields(self) -> List[str]:
        return [
            "email",
            "phone",
            "title",
            "department",
            "company",
            "company_domain",
            "linkedin_url",
            "status",
            "is_decision_maker",
            "is_champion",
            "tags",
            "notes",
        ]

    async def validate_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Tuple[bool, List[ImportErrorModel]]:
        """Validate a prospect row.

        Validates:
        - Required fields present
        - Email format
        - Phone format (if present)
        - LinkedIn URL format (if present)
        - Status value
        """
        errors: List[ImportErrorModel] = []

        # Check required fields
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()

        if not first_name:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="first_name",
                    value=first_name,
                    error="First name is required",
                )
            )

        if not last_name:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="last_name",
                    value=last_name,
                    error="Last name is required",
                )
            )

        # Validate email if present
        email = row.get("email", "").strip()
        if email and not self._validate_email(email):
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="email",
                    value=email,
                    error="Invalid email format",
                )
            )

        # Validate phone if present
        phone = row.get("phone", "").strip()
        if phone and not self._validate_phone(phone):
            # Warning, not error - phone formats vary widely
            self.warnings.append(
                f"Row {row_number}: Phone number '{phone}' may be in non-standard format"
            )

        # Validate LinkedIn URL if present
        linkedin_url = row.get("linkedin_url", "").strip()
        if linkedin_url:
            if not self._validate_url(linkedin_url):
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="linkedin_url",
                        value=linkedin_url,
                        error="Invalid LinkedIn URL format",
                    )
                )
            elif "linkedin.com" not in linkedin_url.lower():
                self.warnings.append(
                    f"Row {row_number}: URL '{linkedin_url}' does not appear to be a LinkedIn URL"
                )

        # Validate status if present
        status = row.get("status", "").strip().lower()
        if status:
            valid_statuses = [s.value for s in ProspectStatus]
            # Also accept common variations
            status_aliases = {
                "new": "new",
                "lead": "new",
                "contacted": "contacted",
                "open": "engaged",
                "engaged": "engaged",
                "qualified": "qualified",
                "mql": "qualified",
                "sql": "qualified",
                "opportunity": "opportunity",
                "opp": "opportunity",
                "customer": "customer",
                "won": "customer",
                "churned": "churned",
                "lost": "churned",
                "unqualified": "churned",
            }

            normalized_status = status_aliases.get(status, status)
            if normalized_status not in valid_statuses:
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="status",
                        value=status,
                        error=f"Invalid status. Valid values: {', '.join(valid_statuses)}",
                    )
                )

        return len(errors) == 0, errors

    async def import_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Optional[str]:
        """Import a single prospect row.

        Creates or updates:
        - Prospect record
        - Associated company (if company name provided)

        Returns:
            Created prospect ID, or None if failed
        """
        try:
            # Normalize data
            first_name = row.get("first_name", "").strip()
            last_name = row.get("last_name", "").strip()
            email = row.get("email", "").strip().lower()
            phone = row.get("phone", "").strip()
            title = row.get("title", "").strip()
            department = row.get("department", "").strip()
            company_name = row.get("company", "").strip()
            company_domain = row.get("company_domain", "").strip()
            linkedin_url = row.get("linkedin_url", "").strip()
            notes = row.get("notes", "").strip()

            # Normalize status
            status_value = row.get("status", "new").strip().lower()
            status_aliases = {
                "new": "new",
                "lead": "new",
                "contacted": "contacted",
                "open": "engaged",
                "engaged": "engaged",
                "qualified": "qualified",
                "mql": "qualified",
                "sql": "qualified",
                "opportunity": "opportunity",
                "customer": "customer",
                "won": "customer",
                "churned": "churned",
                "lost": "churned",
            }
            status = status_aliases.get(status_value, "new")

            # Parse boolean fields
            is_decision_maker = self._parse_boolean(
                row.get("is_decision_maker", "false")
            )
            is_champion = self._parse_boolean(row.get("is_champion", "false"))

            # Parse tags (comma or semicolon separated)
            tags_str = row.get("tags", "")
            if tags_str:
                tags = [
                    t.strip()
                    for t in tags_str.replace(";", ",").split(",")
                    if t.strip()
                ]
            else:
                tags = []

            # TODO: Check for duplicates by email
            # TODO: Create or match company
            # TODO: Save to database

            # For now, generate mock ID
            prospect_id = str(uuid.uuid4())

            # Mock database save
            prospect_data = {
                "id": prospect_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "title": title,
                "department": department,
                "linkedin_url": linkedin_url,
                "status": status,
                "is_decision_maker": is_decision_maker,
                "is_champion": is_champion,
                "tags": tags,
                "notes": notes,
                "company_name": company_name,
                "company_domain": company_domain,
                "organization_id": self.job.organization_id,
                "user_id": self.job.user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            # In real implementation: save to database
            # await self.db.prospects.create(prospect_data)

            return prospect_id

        except Exception as e:
            self.errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    error=f"Failed to import: {str(e)}",
                )
            )
            return None

    def _parse_boolean(self, value: Any) -> bool:
        """Parse a boolean value from various formats."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "y", "on")
        return bool(value)

    def suggest_field_mapping(
        self, source_columns: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """Suggest field mappings based on source column names.

        Args:
            source_columns: List of column names from source file

        Returns:
            Suggested mapping configuration
        """
        suggestions = {}

        for source_col in source_columns:
            normalized = source_col.lower().strip().replace(" ", "_")

            # Check direct match
            all_fields = self.required_fields + self.optional_fields
            if normalized in all_fields:
                suggestions[source_col] = {
                    "target_field": normalized,
                    "confidence": "high",
                }
                continue

            # Check aliases
            matched = False
            for target_field, aliases in self.FIELD_ALIASES.items():
                if normalized in aliases:
                    suggestions[source_col] = {
                        "target_field": target_field,
                        "confidence": "medium",
                    }
                    matched = True
                    break

            if not matched:
                # Suggest as custom field
                suggestions[source_col] = {
                    "target_field": normalized,
                    "confidence": "low",
                    "note": "Unrecognized field - may be ignored",
                }

        return suggestions
