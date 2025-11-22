"""
Salesforce custom field mapping system.

Provides bidirectional field mapping between Sales OS and Salesforce,
with support for custom transformations and default values.
"""

from datetime import datetime
from typing import Any, Callable, Optional

from backend.app.models.salesforce import (
    FieldMapping,
    FieldMappingConfig,
    FieldMappingDirection,
)


# Built-in transformation functions
def transform_to_uppercase(value: Any) -> str:
    """Transform value to uppercase string."""
    return str(value).upper() if value is not None else ""


def transform_to_lowercase(value: Any) -> str:
    """Transform value to lowercase string."""
    return str(value).lower() if value is not None else ""


def transform_to_boolean(value: Any) -> bool:
    """Transform value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def transform_to_integer(value: Any) -> Optional[int]:
    """Transform value to integer."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def transform_to_float(value: Any) -> Optional[float]:
    """Transform value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def transform_date_to_salesforce(value: Any) -> Optional[str]:
    """Transform datetime to Salesforce date format (YYYY-MM-DD)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        return value[:10]  # Assume ISO format, take date part
    return None


def transform_datetime_to_salesforce(value: Any) -> Optional[str]:
    """Transform datetime to Salesforce datetime format (ISO 8601)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return None


def transform_phone_to_e164(value: Any) -> Optional[str]:
    """Transform phone number to E.164 format."""
    if value is None:
        return None
    # Remove all non-digit characters
    digits = "".join(c for c in str(value) if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+{digits}"
    elif len(digits) > 10:
        return f"+{digits}"
    return value  # Return original if can't transform


def transform_trim(value: Any) -> str:
    """Trim whitespace from string value."""
    return str(value).strip() if value is not None else ""


# Registry of available transformations
TRANSFORM_REGISTRY: dict[str, Callable[[Any], Any]] = {
    "uppercase": transform_to_uppercase,
    "lowercase": transform_to_lowercase,
    "boolean": transform_to_boolean,
    "integer": transform_to_integer,
    "float": transform_to_float,
    "date": transform_date_to_salesforce,
    "datetime": transform_datetime_to_salesforce,
    "phone_e164": transform_phone_to_e164,
    "trim": transform_trim,
}


# Default field mappings for common Salesforce objects
DEFAULT_LEAD_MAPPINGS: list[FieldMapping] = [
    FieldMapping(
        sales_os_field="first_name",
        salesforce_field="FirstName",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="last_name",
        salesforce_field="LastName",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="email",
        salesforce_field="Email",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="phone",
        salesforce_field="Phone",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="company",
        salesforce_field="Company",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="title",
        salesforce_field="Title",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="industry",
        salesforce_field="Industry",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="website",
        salesforce_field="Website",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="lead_source",
        salesforce_field="LeadSource",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="status",
        salesforce_field="Status",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="street",
        salesforce_field="Street",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="city",
        salesforce_field="City",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="state",
        salesforce_field="State",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="postal_code",
        salesforce_field="PostalCode",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="country",
        salesforce_field="Country",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="description",
        salesforce_field="Description",
        sobject_type="Lead",
    ),
    FieldMapping(
        sales_os_field="annual_revenue",
        salesforce_field="AnnualRevenue",
        sobject_type="Lead",
        transform="float",
    ),
    FieldMapping(
        sales_os_field="number_of_employees",
        salesforce_field="NumberOfEmployees",
        sobject_type="Lead",
        transform="integer",
    ),
]

DEFAULT_CONTACT_MAPPINGS: list[FieldMapping] = [
    FieldMapping(
        sales_os_field="first_name",
        salesforce_field="FirstName",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="last_name",
        salesforce_field="LastName",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="email",
        salesforce_field="Email",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="phone",
        salesforce_field="Phone",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mobile_phone",
        salesforce_field="MobilePhone",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="title",
        salesforce_field="Title",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="department",
        salesforce_field="Department",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="account_id",
        salesforce_field="AccountId",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mailing_street",
        salesforce_field="MailingStreet",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mailing_city",
        salesforce_field="MailingCity",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mailing_state",
        salesforce_field="MailingState",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mailing_postal_code",
        salesforce_field="MailingPostalCode",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="mailing_country",
        salesforce_field="MailingCountry",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="description",
        salesforce_field="Description",
        sobject_type="Contact",
    ),
    FieldMapping(
        sales_os_field="lead_source",
        salesforce_field="LeadSource",
        sobject_type="Contact",
    ),
]

DEFAULT_OPPORTUNITY_MAPPINGS: list[FieldMapping] = [
    FieldMapping(
        sales_os_field="name",
        salesforce_field="Name",
        sobject_type="Opportunity",
    ),
    FieldMapping(
        sales_os_field="stage_name",
        salesforce_field="StageName",
        sobject_type="Opportunity",
    ),
    FieldMapping(
        sales_os_field="amount",
        salesforce_field="Amount",
        sobject_type="Opportunity",
        transform="float",
    ),
    FieldMapping(
        sales_os_field="close_date",
        salesforce_field="CloseDate",
        sobject_type="Opportunity",
        transform="date",
    ),
    FieldMapping(
        sales_os_field="probability",
        salesforce_field="Probability",
        sobject_type="Opportunity",
        transform="integer",
    ),
    FieldMapping(
        sales_os_field="description",
        salesforce_field="Description",
        sobject_type="Opportunity",
    ),
    FieldMapping(
        sales_os_field="next_step",
        salesforce_field="NextStep",
        sobject_type="Opportunity",
    ),
    FieldMapping(
        sales_os_field="lead_source",
        salesforce_field="LeadSource",
        sobject_type="Opportunity",
    ),
    FieldMapping(
        sales_os_field="type",
        salesforce_field="Type",
        sobject_type="Opportunity",
    ),
]

DEFAULT_TASK_MAPPINGS: list[FieldMapping] = [
    FieldMapping(
        sales_os_field="subject",
        salesforce_field="Subject",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="what_id",
        salesforce_field="WhatId",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="who_id",
        salesforce_field="WhoId",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="owner_id",
        salesforce_field="OwnerId",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="activity_date",
        salesforce_field="ActivityDate",
        sobject_type="Task",
        transform="date",
    ),
    FieldMapping(
        sales_os_field="priority",
        salesforce_field="Priority",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="status",
        salesforce_field="Status",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="description",
        salesforce_field="Description",
        sobject_type="Task",
    ),
    FieldMapping(
        sales_os_field="is_reminder_set",
        salesforce_field="IsReminderSet",
        sobject_type="Task",
        transform="boolean",
    ),
    FieldMapping(
        sales_os_field="reminder_datetime",
        salesforce_field="ReminderDateTime",
        sobject_type="Task",
        transform="datetime",
    ),
]


class SalesforceFieldMapper:
    """
    Handles field mapping between Sales OS and Salesforce.

    Supports:
    - Bidirectional mapping
    - Custom transformations
    - Default values
    - Custom field support
    """

    def __init__(
        self,
        config: Optional[FieldMappingConfig] = None,
        use_defaults: bool = True,
    ):
        """
        Initialize the field mapper.

        Args:
            config: Custom field mapping configuration
            use_defaults: Whether to include default mappings
        """
        self._mappings: dict[str, list[FieldMapping]] = {}

        # Load default mappings if requested
        if use_defaults:
            self._load_default_mappings()

        # Override with custom config if provided
        if config:
            for mapping in config.mappings:
                self.add_mapping(mapping)

    def _load_default_mappings(self) -> None:
        """Load all default field mappings."""
        for mapping in DEFAULT_LEAD_MAPPINGS:
            self.add_mapping(mapping)
        for mapping in DEFAULT_CONTACT_MAPPINGS:
            self.add_mapping(mapping)
        for mapping in DEFAULT_OPPORTUNITY_MAPPINGS:
            self.add_mapping(mapping)
        for mapping in DEFAULT_TASK_MAPPINGS:
            self.add_mapping(mapping)

    def add_mapping(self, mapping: FieldMapping) -> None:
        """
        Add a field mapping.

        Args:
            mapping: The field mapping to add
        """
        sobject_type = mapping.sobject_type
        if sobject_type not in self._mappings:
            self._mappings[sobject_type] = []

        # Replace existing mapping for same Sales OS field
        self._mappings[sobject_type] = [
            m for m in self._mappings[sobject_type]
            if m.sales_os_field != mapping.sales_os_field
        ]
        self._mappings[sobject_type].append(mapping)

    def remove_mapping(self, sobject_type: str, sales_os_field: str) -> bool:
        """
        Remove a field mapping.

        Args:
            sobject_type: The Salesforce object type
            sales_os_field: The Sales OS field name

        Returns:
            True if mapping was removed, False if not found
        """
        if sobject_type not in self._mappings:
            return False

        original_len = len(self._mappings[sobject_type])
        self._mappings[sobject_type] = [
            m for m in self._mappings[sobject_type]
            if m.sales_os_field != sales_os_field
        ]
        return len(self._mappings[sobject_type]) < original_len

    def get_mappings(self, sobject_type: str) -> list[FieldMapping]:
        """
        Get all mappings for a Salesforce object type.

        Args:
            sobject_type: The Salesforce object type

        Returns:
            List of field mappings
        """
        return self._mappings.get(sobject_type, [])

    def _apply_transform(
        self,
        value: Any,
        transform_name: Optional[str],
    ) -> Any:
        """
        Apply a transformation to a value.

        Args:
            value: The value to transform
            transform_name: Name of the transformation function

        Returns:
            Transformed value
        """
        if transform_name is None or value is None:
            return value

        transform_func = TRANSFORM_REGISTRY.get(transform_name)
        if transform_func:
            return transform_func(value)

        return value

    def map_to_salesforce(
        self,
        sobject_type: str,
        data: dict[str, Any],
        include_custom_fields: bool = True,
    ) -> dict[str, Any]:
        """
        Map Sales OS data to Salesforce format.

        Args:
            sobject_type: The Salesforce object type
            data: Sales OS data dictionary
            include_custom_fields: Whether to include custom_fields from data

        Returns:
            Salesforce-formatted data dictionary
        """
        mappings = self.get_mappings(sobject_type)
        result: dict[str, Any] = {}

        for mapping in mappings:
            if mapping.direction == FieldMappingDirection.INBOUND:
                continue  # Skip inbound-only mappings

            value = data.get(mapping.sales_os_field)

            # Use default value if no value provided
            if value is None and mapping.default_value is not None:
                value = mapping.default_value

            # Skip if still no value and not required
            if value is None:
                continue

            # Apply transformation
            value = self._apply_transform(value, mapping.transform)

            result[mapping.salesforce_field] = value

        # Include custom fields if present
        if include_custom_fields and "custom_fields" in data:
            custom_fields = data.get("custom_fields", {})
            if isinstance(custom_fields, dict):
                result.update(custom_fields)

        return result

    def map_from_salesforce(
        self,
        sobject_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Map Salesforce data to Sales OS format.

        Args:
            sobject_type: The Salesforce object type
            data: Salesforce data dictionary

        Returns:
            Sales OS-formatted data dictionary
        """
        mappings = self.get_mappings(sobject_type)
        result: dict[str, Any] = {}

        # Create reverse mapping (Salesforce field -> Sales OS field)
        for mapping in mappings:
            if mapping.direction == FieldMappingDirection.OUTBOUND:
                continue  # Skip outbound-only mappings

            value = data.get(mapping.salesforce_field)

            if value is None:
                continue

            result[mapping.sales_os_field] = value

        # Include any unmapped Salesforce fields as custom_fields
        mapped_sf_fields = {m.salesforce_field for m in mappings}
        custom_fields = {
            k: v for k, v in data.items()
            if k not in mapped_sf_fields
            and not k.startswith("attributes")
            and k not in ("Id", "id")
        }
        if custom_fields:
            result["custom_fields"] = custom_fields

        return result

    def validate_required_fields(
        self,
        sobject_type: str,
        data: dict[str, Any],
    ) -> list[str]:
        """
        Validate that all required fields are present.

        Args:
            sobject_type: The Salesforce object type
            data: Data to validate

        Returns:
            List of missing required field names
        """
        mappings = self.get_mappings(sobject_type)
        missing = []

        for mapping in mappings:
            if not mapping.is_required:
                continue

            value = data.get(mapping.sales_os_field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(mapping.sales_os_field)

        return missing

    def export_config(self) -> FieldMappingConfig:
        """
        Export current mappings as a configuration.

        Returns:
            FieldMappingConfig with all current mappings
        """
        all_mappings = []
        for mappings in self._mappings.values():
            all_mappings.extend(mappings)

        return FieldMappingConfig(
            org_id="",
            mappings=all_mappings,
        )
