"""HubSpot field mapping utilities for enriched data."""

import logging
from datetime import datetime
from typing import Any, Optional

from app.models.prospect import ProspectEnriched
from app.models.company import CompanyEnriched

logger = logging.getLogger(__name__)


class HubSpotFieldMapper:
    """Maps enriched prospect and company data to HubSpot contact/company fields."""

    # Standard HubSpot contact properties
    CONTACT_FIELD_MAPPING = {
        # Basic info
        "first_name": "firstname",
        "last_name": "lastname",
        "full_name": "fullname",
        "email": "email",
        "title": "jobtitle",

        # Company association
        "company_name": "company",
        "company_domain": "website",

        # Contact info
        "contact_info.phone": "phone",
        "contact_info.mobile": "mobilephone",
        "contact_info.work_phone": "work_phone",

        # Social profiles
        "social_profiles.linkedin_url": "hs_linkedinid",
        "social_profiles.twitter_url": "twitterhandle",

        # Professional details
        "seniority_level": "hs_persona",
        "department": "department",

        # LinkedIn insights
        "linkedin_insights.location": "city",
        "linkedin_insights.industry": "industry",
    }

    # Standard HubSpot company properties
    COMPANY_FIELD_MAPPING = {
        # Basic info
        "name": "name",
        "domain": "domain",
        "website": "website",
        "description": "description",
        "logo_url": "logo",

        # Industry
        "industry": "industry",
        "sector": "type",

        # Size
        "employee_count": "numberofemployees",
        "annual_revenue": "annualrevenue",

        # Location
        "headquarters.street": "address",
        "headquarters.city": "city",
        "headquarters.state": "state",
        "headquarters.country": "country",
        "headquarters.postal_code": "zip",

        # Funding
        "funding_info.total_raised": "total_money_raised",
        "funding_info.last_funding_stage": "recent_deal_amount",

        # Social
        "social_profiles.linkedin_url": "linkedin_company_page",
        "social_profiles.twitter_url": "twitterhandle",
        "social_profiles.facebook_url": "facebook_company_page",

        # Other
        "founded_year": "founded_year",
        "company_type": "type",
    }

    # Custom properties that may need to be created in HubSpot
    CUSTOM_CONTACT_PROPERTIES = {
        "enrichment_confidence": {
            "name": "enrichment_confidence",
            "label": "Enrichment Confidence",
            "type": "number",
            "field_type": "number",
            "description": "Confidence score from data enrichment (0-1)",
        },
        "data_completeness": {
            "name": "data_completeness",
            "label": "Data Completeness",
            "type": "number",
            "field_type": "number",
            "description": "Completeness score of enriched data (0-1)",
        },
        "enrichment_sources": {
            "name": "enrichment_sources",
            "label": "Enrichment Sources",
            "type": "string",
            "field_type": "text",
            "description": "Data sources used for enrichment",
        },
        "enriched_at": {
            "name": "enriched_at",
            "label": "Last Enriched",
            "type": "datetime",
            "field_type": "date",
            "description": "When the contact was last enriched",
        },
        "seniority_level": {
            "name": "seniority_level",
            "label": "Seniority Level",
            "type": "enumeration",
            "field_type": "select",
            "description": "Prospect seniority level",
            "options": [
                {"label": "C-Level", "value": "c_level"},
                {"label": "VP", "value": "vp"},
                {"label": "Director", "value": "director"},
                {"label": "Manager", "value": "manager"},
                {"label": "Individual Contributor", "value": "ic"},
            ],
        },
        "role_function": {
            "name": "role_function",
            "label": "Role Function",
            "type": "enumeration",
            "field_type": "select",
            "description": "Prospect role function",
            "options": [
                {"label": "Sales", "value": "sales"},
                {"label": "Marketing", "value": "marketing"},
                {"label": "Engineering", "value": "engineering"},
                {"label": "Product", "value": "product"},
                {"label": "Finance", "value": "finance"},
                {"label": "Operations", "value": "operations"},
                {"label": "HR", "value": "hr"},
                {"label": "Other", "value": "other"},
            ],
        },
    }

    CUSTOM_COMPANY_PROPERTIES = {
        "tech_stack": {
            "name": "tech_stack",
            "label": "Tech Stack",
            "type": "string",
            "field_type": "textarea",
            "description": "Technologies used by the company",
        },
        "funding_stage": {
            "name": "funding_stage",
            "label": "Funding Stage",
            "type": "enumeration",
            "field_type": "select",
            "description": "Company funding stage",
            "options": [
                {"label": "Bootstrapped", "value": "bootstrapped"},
                {"label": "Pre-Seed", "value": "pre_seed"},
                {"label": "Seed", "value": "seed"},
                {"label": "Series A", "value": "series_a"},
                {"label": "Series B", "value": "series_b"},
                {"label": "Series C", "value": "series_c"},
                {"label": "Series D+", "value": "series_d_plus"},
                {"label": "Public", "value": "public"},
            ],
        },
        "company_size_category": {
            "name": "company_size_category",
            "label": "Company Size Category",
            "type": "enumeration",
            "field_type": "select",
            "description": "Company size category",
            "options": [
                {"label": "Startup (1-10)", "value": "1-10"},
                {"label": "Small (11-50)", "value": "11-50"},
                {"label": "Medium (51-200)", "value": "51-200"},
                {"label": "Large (201-500)", "value": "201-500"},
                {"label": "Enterprise (501-1000)", "value": "501-1000"},
                {"label": "Large Enterprise (1001-5000)", "value": "1001-5000"},
                {"label": "Mega Enterprise (5000+)", "value": "5000+"},
            ],
        },
    }

    def __init__(
        self,
        custom_mappings: Optional[dict[str, str]] = None,
        include_custom_properties: bool = True,
    ):
        """
        Initialize mapper with optional custom field mappings.

        Args:
            custom_mappings: Additional field mappings to use
            include_custom_properties: Whether to include custom Sales OS properties
        """
        self.contact_mapping = self.CONTACT_FIELD_MAPPING.copy()
        self.company_mapping = self.COMPANY_FIELD_MAPPING.copy()
        self.include_custom = include_custom_properties

        if custom_mappings:
            self.contact_mapping.update(custom_mappings)

    def map_prospect_to_hubspot(
        self,
        prospect: ProspectEnriched,
        include_nulls: bool = False,
    ) -> dict[str, Any]:
        """
        Map enriched prospect to HubSpot contact properties.

        Args:
            prospect: Enriched prospect data
            include_nulls: Whether to include null values in output

        Returns:
            Dictionary of HubSpot contact properties
        """
        properties = {}

        # Map standard fields
        for source_path, hubspot_field in self.contact_mapping.items():
            value = self._get_nested_value(prospect, source_path)
            if value is not None or include_nulls:
                properties[hubspot_field] = self._format_value(value)

        # Add custom properties if enabled
        if self.include_custom:
            if prospect.enrichment_confidence:
                properties["enrichment_confidence"] = str(prospect.enrichment_confidence)
            if prospect.data_completeness:
                properties["data_completeness"] = str(prospect.data_completeness)
            if prospect.enrichment_sources:
                properties["enrichment_sources"] = ",".join(
                    s.value for s in prospect.enrichment_sources
                )
            if prospect.enriched_at:
                properties["enriched_at"] = prospect.enriched_at.isoformat()
            if prospect.seniority_level:
                properties["seniority_level"] = prospect.seniority_level.lower().replace(" ", "_")
            if prospect.role_function:
                properties["role_function"] = prospect.role_function.lower().replace(" ", "_")

        # Store the mapping for reference
        prospect.hubspot_field_mapping = properties
        prospect.hubspot_mapped = True

        return properties

    def map_company_to_hubspot(
        self,
        company: CompanyEnriched,
        include_nulls: bool = False,
    ) -> dict[str, Any]:
        """
        Map enriched company to HubSpot company properties.

        Args:
            company: Enriched company data
            include_nulls: Whether to include null values in output

        Returns:
            Dictionary of HubSpot company properties
        """
        properties = {}

        # Map standard fields
        for source_path, hubspot_field in self.company_mapping.items():
            value = self._get_nested_value(company, source_path)
            if value is not None or include_nulls:
                properties[hubspot_field] = self._format_value(value)

        # Add custom properties if enabled
        if self.include_custom:
            if company.tech_stack and company.tech_stack.technologies:
                properties["tech_stack"] = ", ".join(company.tech_stack.technologies)
            if company.funding_info and company.funding_info.last_funding_stage:
                properties["funding_stage"] = company.funding_info.last_funding_stage.value
            if company.company_size:
                properties["company_size_category"] = company.company_size.value

        # Store the mapping for reference
        company.hubspot_field_mapping = properties
        company.hubspot_mapped = True

        return properties

    def get_custom_properties_schema(self) -> dict[str, list[dict]]:
        """
        Get schema definitions for custom properties that need to be created in HubSpot.

        Returns:
            Dictionary with 'contact' and 'company' property definitions
        """
        return {
            "contact": list(self.CUSTOM_CONTACT_PROPERTIES.values()),
            "company": list(self.CUSTOM_COMPANY_PROPERTIES.values()),
        }

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get value from nested object using dot notation path."""
        parts = path.split(".")
        current = obj

        for part in parts:
            if current is None:
                return None
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _format_value(self, value: Any) -> str:
        """Format value for HubSpot API."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, datetime):
            # HubSpot expects Unix timestamp in milliseconds for datetime
            return str(int(value.timestamp() * 1000))
        if isinstance(value, list):
            return ";".join(str(v) for v in value)
        if hasattr(value, "value"):  # Enum
            return value.value
        return str(value)


def create_hubspot_contact_payload(
    prospect: ProspectEnriched,
    mapper: Optional[HubSpotFieldMapper] = None,
) -> dict[str, Any]:
    """
    Create HubSpot API payload for creating/updating a contact.

    Args:
        prospect: Enriched prospect data
        mapper: Optional custom mapper instance

    Returns:
        HubSpot API payload
    """
    if mapper is None:
        mapper = HubSpotFieldMapper()

    properties = mapper.map_prospect_to_hubspot(prospect)

    return {
        "properties": properties,
    }


def create_hubspot_company_payload(
    company: CompanyEnriched,
    mapper: Optional[HubSpotFieldMapper] = None,
) -> dict[str, Any]:
    """
    Create HubSpot API payload for creating/updating a company.

    Args:
        company: Enriched company data
        mapper: Optional custom mapper instance

    Returns:
        HubSpot API payload
    """
    if mapper is None:
        mapper = HubSpotFieldMapper()

    properties = mapper.map_company_to_hubspot(company)

    return {
        "properties": properties,
    }
