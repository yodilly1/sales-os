"""Apollo.io enrichment provider."""

import logging
from typing import Any, Optional

from app.schemas.enrichment import EnrichmentSource
from app.models.company import CompanySize

from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class ApolloProvider(EnrichmentProvider):
    """Apollo.io API provider for person and company enrichment."""

    name = "apollo"
    source = EnrichmentSource.APOLLO
    BASE_URL = "https://api.apollo.io/v1"

    def _get_headers(self) -> dict[str, str]:
        """Get headers with Apollo API key."""
        headers = super()._get_headers()
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich prospect using Apollo People API."""
        if not self.is_configured:
            logger.warning("Apollo not configured, skipping")
            return None

        url = f"{self.BASE_URL}/people/match"
        payload = {}

        if email:
            payload["email"] = email
        if name:
            # Split name into first and last
            parts = name.split(" ", 1)
            payload["first_name"] = parts[0]
            if len(parts) > 1:
                payload["last_name"] = parts[1]
        if company:
            payload["organization_name"] = company
        if domain:
            payload["domain"] = domain

        if not payload:
            return None

        data = await self._make_request("POST", url, json=payload)
        if data and data.get("person"):
            return self.map_to_prospect(data["person"])
        return None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich company using Apollo Organization API."""
        if not self.is_configured:
            logger.warning("Apollo not configured, skipping")
            return None

        url = f"{self.BASE_URL}/organizations/enrich"
        params = {}

        if domain:
            params["domain"] = domain
        elif name:
            params["name"] = name
        else:
            return None

        data = await self._make_request("GET", url, params=params)
        if data and data.get("organization"):
            return self.map_to_company(data["organization"])
        return None

    async def search_people(
        self,
        titles: Optional[list[str]] = None,
        seniorities: Optional[list[str]] = None,
        company_domains: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for people matching criteria."""
        if not self.is_configured:
            return []

        url = f"{self.BASE_URL}/mixed_people/search"
        payload = {
            "per_page": limit,
            "person_titles": titles or [],
            "person_seniorities": seniorities or [],
            "organization_domains": company_domains or [],
        }

        data = await self._make_request("POST", url, json=payload)
        if data and data.get("people"):
            return [self.map_to_prospect(p) for p in data["people"]]
        return []

    def map_to_prospect(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map Apollo person response to prospect model."""
        organization = data.get("organization", {})

        return {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "full_name": data.get("name"),
            "title": data.get("title"),
            "seniority_level": data.get("seniority"),
            "department": data.get("departments", [None])[0] if data.get("departments") else None,
            "company_name": organization.get("name"),
            "company_domain": organization.get("website_url", "").replace("https://", "").replace("http://", "").rstrip("/"),
            "contact_info": {
                "email": data.get("email"),
                "email_verified": data.get("email_status") == "verified",
                "phone": data.get("phone_numbers", [{}])[0].get("sanitized_number") if data.get("phone_numbers") else None,
            },
            "social_profiles": {
                "linkedin_url": data.get("linkedin_url"),
                "twitter_url": data.get("twitter_url"),
                "github_url": data.get("github_url"),
            },
            "linkedin_insights": {
                "headline": data.get("headline"),
                "location": data.get("city"),
            },
            "source": self.source,
        }

    def map_to_company(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map Apollo organization response to company model."""
        employee_count = data.get("estimated_num_employees")

        return {
            "name": data.get("name"),
            "domain": data.get("primary_domain"),
            "website": data.get("website_url"),
            "description": data.get("short_description"),
            "logo_url": data.get("logo_url"),
            "founded_year": data.get("founded_year"),
            "industry": data.get("industry"),
            "company_size": self._map_employee_count_to_size(employee_count),
            "employee_count": employee_count,
            "annual_revenue": data.get("annual_revenue"),
            "headquarters": {
                "city": data.get("city"),
                "state": data.get("state"),
                "country": data.get("country"),
            },
            "funding_info": {
                "total_raised": data.get("total_funding"),
                "last_funding_date": data.get("latest_funding_round_date"),
                "last_funding_stage": data.get("latest_funding_stage"),
                "is_funded": data.get("total_funding", 0) > 0,
            },
            "tech_stack": {
                "technologies": data.get("technologies", []),
            },
            "social_profiles": {
                "linkedin_url": data.get("linkedin_url"),
                "twitter_url": data.get("twitter_url"),
                "facebook_url": data.get("facebook_url"),
            },
            "source": self.source,
        }

    def _map_employee_count_to_size(self, count: Optional[int]) -> Optional[CompanySize]:
        """Map employee count to company size enum."""
        if count is None:
            return None
        if count <= 10:
            return CompanySize.STARTUP
        elif count <= 50:
            return CompanySize.SMALL
        elif count <= 200:
            return CompanySize.MEDIUM
        elif count <= 500:
            return CompanySize.LARGE
        elif count <= 1000:
            return CompanySize.ENTERPRISE
        elif count <= 5000:
            return CompanySize.LARGE_ENTERPRISE
        else:
            return CompanySize.MEGA_ENTERPRISE
