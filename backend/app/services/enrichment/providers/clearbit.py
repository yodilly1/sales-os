"""Clearbit enrichment provider."""

import logging
from typing import Any, Optional

from app.schemas.enrichment import EnrichmentSource
from app.models.company import CompanySize, FundingStage

from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class ClearbitProvider(EnrichmentProvider):
    """Clearbit API provider for person and company enrichment."""

    name = "clearbit"
    source = EnrichmentSource.CLEARBIT
    BASE_URL = "https://person.clearbit.com/v2"
    COMPANY_URL = "https://company.clearbit.com/v2"

    def _get_headers(self) -> dict[str, str]:
        """Get headers with Clearbit API key."""
        headers = super()._get_headers()
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich prospect using Clearbit Person API."""
        if not self.is_configured:
            logger.warning("Clearbit not configured, skipping")
            return None

        if not email:
            logger.info("Email required for Clearbit person lookup")
            return None

        url = f"{self.BASE_URL}/people/find"
        params = {"email": email}

        data = await self._make_request("GET", url, params=params)
        if data:
            return self.map_to_prospect(data)
        return None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich company using Clearbit Company API."""
        if not self.is_configured:
            logger.warning("Clearbit not configured, skipping")
            return None

        if not domain:
            logger.info("Domain required for Clearbit company lookup")
            return None

        url = f"{self.COMPANY_URL}/companies/find"
        params = {"domain": domain}

        data = await self._make_request("GET", url, params=params)
        if data:
            return self.map_to_company(data)
        return None

    def map_to_prospect(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map Clearbit person response to prospect model."""
        name_data = data.get("name", {})
        employment = data.get("employment", {})
        geo = data.get("geo", {})

        return {
            "first_name": name_data.get("givenName"),
            "last_name": name_data.get("familyName"),
            "full_name": name_data.get("fullName"),
            "title": employment.get("title"),
            "seniority_level": employment.get("seniority"),
            "role_function": employment.get("role"),
            "company_name": employment.get("name"),
            "company_domain": employment.get("domain"),
            "contact_info": {
                "email": data.get("email"),
                "email_verified": True,
                "phone": data.get("phone"),
            },
            "social_profiles": {
                "linkedin_url": data.get("linkedin", {}).get("handle"),
                "twitter_url": data.get("twitter", {}).get("handle"),
                "github_url": data.get("github", {}).get("handle"),
            },
            "linkedin_insights": {
                "location": geo.get("city"),
                "industry": employment.get("role"),
            },
            "source": self.source,
        }

    def map_to_company(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map Clearbit company response to company model."""
        metrics = data.get("metrics", {})
        geo = data.get("geo", {})
        category = data.get("category", {})

        # Map employee count to CompanySize
        employee_count = metrics.get("employees")
        company_size = self._map_employee_count_to_size(employee_count)

        # Map funding to stage
        funding_raised = metrics.get("raised")
        funding_stage = self._estimate_funding_stage(funding_raised)

        return {
            "name": data.get("name"),
            "legal_name": data.get("legalName"),
            "domain": data.get("domain"),
            "website": data.get("url"),
            "description": data.get("description"),
            "logo_url": data.get("logo"),
            "founded_year": data.get("foundedYear"),
            "industry": category.get("industry"),
            "industry_group": category.get("industryGroup"),
            "sub_industry": category.get("subIndustry"),
            "sector": category.get("sector"),
            "sic_codes": category.get("sicCode", "").split(",") if category.get("sicCode") else [],
            "naics_codes": category.get("naicsCode", "").split(",") if category.get("naicsCode") else [],
            "tags": data.get("tags", []),
            "company_size": company_size,
            "employee_count": employee_count,
            "employee_range": metrics.get("employeesRange"),
            "annual_revenue": metrics.get("annualRevenue"),
            "revenue_range": metrics.get("estimatedAnnualRevenue"),
            "headquarters": {
                "street": geo.get("streetAddress"),
                "city": geo.get("city"),
                "state": geo.get("state"),
                "country": geo.get("country"),
                "postal_code": geo.get("postalCode"),
                "formatted_address": geo.get("streetAddress"),
            },
            "funding_info": {
                "total_raised": funding_raised,
                "last_funding_stage": funding_stage,
                "is_funded": funding_raised is not None and funding_raised > 0,
            },
            "tech_stack": {
                "technologies": data.get("tech", []),
            },
            "social_profiles": {
                "linkedin_url": data.get("linkedin", {}).get("handle"),
                "twitter_url": data.get("twitter", {}).get("handle"),
                "facebook_url": data.get("facebook", {}).get("handle"),
                "crunchbase_url": data.get("crunchbase", {}).get("handle"),
            },
            "company_type": data.get("type"),
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

    def _estimate_funding_stage(self, raised: Optional[float]) -> Optional[FundingStage]:
        """Estimate funding stage based on total raised."""
        if raised is None:
            return None
        if raised == 0:
            return FundingStage.BOOTSTRAPPED
        elif raised < 500000:
            return FundingStage.PRE_SEED
        elif raised < 2000000:
            return FundingStage.SEED
        elif raised < 15000000:
            return FundingStage.SERIES_A
        elif raised < 50000000:
            return FundingStage.SERIES_B
        elif raised < 100000000:
            return FundingStage.SERIES_C
        else:
            return FundingStage.SERIES_D_PLUS
