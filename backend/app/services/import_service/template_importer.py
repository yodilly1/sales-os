"""Content template importer."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.export_import import (
    ImportType,
    ImportError as ImportErrorModel,
)
from app.models.content import ContentType
from .base import BaseImporter


class TemplateImporter(BaseImporter):
    """Importer for content templates.

    Supports:
    - JSON format (from Sales OS export)
    - Template body with variables
    - Styling configuration
    """

    @property
    def import_type(self) -> ImportType:
        return ImportType.TEMPLATES

    @property
    def required_fields(self) -> List[str]:
        return ["name", "content_type", "template_body"]

    @property
    def optional_fields(self) -> List[str]:
        return [
            "description",
            "variables",
            "styling",
            "is_active",
        ]

    async def validate_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Tuple[bool, List[ImportErrorModel]]:
        """Validate a template row.

        Validates:
        - Required fields present
        - Content type is valid
        - Template body contains valid variables
        """
        errors: List[ImportErrorModel] = []

        # Check required fields
        name = row.get("name", "").strip() if isinstance(row.get("name"), str) else str(row.get("name", ""))
        content_type = row.get("content_type", "").strip().lower() if row.get("content_type") else ""
        template_body = row.get("template_body", "")

        if not name:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="name",
                    value=name,
                    error="Template name is required",
                )
            )

        # Validate content type
        if not content_type:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="content_type",
                    error="Content type is required",
                )
            )
        else:
            valid_types = [t.value for t in ContentType]
            if content_type not in valid_types:
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="content_type",
                        value=content_type,
                        error=f"Invalid content type. Valid values: {', '.join(valid_types)}",
                    )
                )

        if not template_body:
            errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    field="template_body",
                    error="Template body is required",
                )
            )

        # Validate variables match template body
        variables = row.get("variables", [])
        if isinstance(variables, str):
            variables = [v.strip() for v in variables.split(",") if v.strip()]

        if template_body and variables:
            # Check that declared variables exist in template
            for var in variables:
                if f"{{{{{var}}}}}" not in template_body and f"{{{{ {var} }}}}" not in template_body:
                    self.warnings.append(
                        f"Row {row_number}: Variable '{var}' declared but not found in template body"
                    )

        # Validate styling JSON if present
        styling = row.get("styling")
        if styling and isinstance(styling, str):
            import json
            try:
                json.loads(styling)
            except json.JSONDecodeError:
                errors.append(
                    ImportErrorModel(
                        row_number=row_number,
                        field="styling",
                        value=styling[:50] + "..." if len(styling) > 50 else styling,
                        error="Invalid JSON format for styling",
                    )
                )

        return len(errors) == 0, errors

    async def import_row(
        self, row: Dict[str, Any], row_number: int
    ) -> Optional[str]:
        """Import a single template row.

        Creates:
        - ContentTemplate record

        Returns:
            Created template ID, or None if failed
        """
        try:
            # Normalize data
            name = row.get("name", "").strip() if isinstance(row.get("name"), str) else str(row.get("name", ""))
            description = row.get("description", "").strip() if row.get("description") else None
            content_type = row.get("content_type", "").strip().lower()
            template_body = row.get("template_body", "")

            # Parse variables
            variables = row.get("variables", [])
            if isinstance(variables, str):
                variables = [v.strip() for v in variables.split(",") if v.strip()]

            # Parse styling
            styling = row.get("styling", {})
            if isinstance(styling, str):
                import json
                try:
                    styling = json.loads(styling)
                except json.JSONDecodeError:
                    styling = {}

            # Parse is_active
            is_active = True
            if row.get("is_active") is not None:
                is_active_val = row.get("is_active")
                if isinstance(is_active_val, str):
                    is_active = is_active_val.lower() in ("true", "yes", "1", "y", "on")
                else:
                    is_active = bool(is_active_val)

            # TODO: Check for duplicate template names
            # TODO: Save to database
            template_id = str(uuid.uuid4())

            template_data = {
                "id": template_id,
                "name": name,
                "description": description,
                "content_type": content_type,
                "template_body": template_body,
                "variables": variables,
                "styling": styling,
                "is_active": is_active,
                "organization_id": self.job.organization_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            # In real implementation: save to database
            # await self.db.content_templates.create(template_data)

            return template_id

        except Exception as e:
            self.errors.append(
                ImportErrorModel(
                    row_number=row_number,
                    error=f"Failed to import: {str(e)}",
                )
            )
            return None

    def extract_variables_from_template(self, template_body: str) -> List[str]:
        """Extract variable names from template body.

        Supports:
        - {{variable}} format
        - {{ variable }} format (with spaces)

        Args:
            template_body: Template content

        Returns:
            List of variable names
        """
        import re

        # Match {{variable}} or {{ variable }}
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        matches = re.findall(pattern, template_body)

        # Return unique variables in order of first appearance
        seen = set()
        unique = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                unique.append(var)

        return unique
