"""LeadMagic enrichment provider.

LeadMagic API provides:
- Email validation
- Email finder (by name + company)
- Profile search (LinkedIn data)
- Mobile finder
- Company data
- Jobs finder
"""

import logging
from typing import Any, Optional

from app.schemas.enrichment import EnrichmentSource
from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class LeadMagicProvider(EnrichmentProvider):
    """LeadMagic API provider for prospect and company enrichment."""

    name = "leadmagic"
    source = EnrichmentSource.LEADMAGIC
    BASE_URL = "https://api.leadmagic.io/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 300,  # LeadMagic allows 300 req/min
        timeout: float = 30.0,
    ):
        super().__init__(api_key=api_key, rate_limit=rate_limit, timeout=timeout)

    def _get_headers(self) -> dict[str, str]:
        """Get headers with LeadMagic API key."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key or "",
        }

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
        linkedin_url: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich prospect using LeadMagic APIs.

        Strategy:
        1. If LinkedIn URL provided, use profile-search for full data
        2. If email provided, validate it and get company info
        3. If name + company/domain, use email-finder to get email
        """
        result: dict[str, Any] = {}

        # Strategy 1: LinkedIn profile search (most comprehensive)
        if linkedin_url:
            profile_data = await self._search_profile(linkedin_url)
            if profile_data:
                result = self._map_profile_to_prospect(profile_data)

        # Strategy 2: Email validation (also returns company data)
        if email and not result.get("contact_info", {}).get("email_verified"):
            validation = await self._validate_email(email, name)
            if validation:
                self._merge_validation_data(result, validation)

        # Strategy 3: Find email by name + company
        if not result.get("contact_info", {}).get("email") and name and (company or domain):
            first_name, last_name = self._split_name(name)
            email_data = await self._find_email(first_name, last_name, domain, company)
            if email_data:
                self._merge_email_finder_data(result, email_data)

        return result if result else None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich company data using LeadMagic.

        Uses email validation or profile search to get company info.
        """
        # LeadMagic doesn't have a dedicated company endpoint,
        # but returns company data in email validation and profile search
        if domain:
            # Use email validation with a generic email to get company data
            validation = await self._validate_email(f"info@{domain}")
            if validation:
                return self._map_company_data(validation)
        return None

    async def _search_profile(self, profile_url: str) -> Optional[dict[str, Any]]:
        """
        Search LinkedIn profile using LeadMagic profile-search API.

        Args:
            profile_url: LinkedIn profile URL or username

        Returns:
            Profile data or None
        """
        url = f"{self.BASE_URL}/people/profile-search"
        payload = {"profile_url": profile_url}

        try:
            response = await self._make_request("POST", url, json=payload)
            if response and response.get("credits_consumed"):
                logger.info(f"LeadMagic profile-search consumed {response.get('credits_consumed')} credits")
            return response
        except Exception as e:
            logger.error(f"LeadMagic profile-search error: {e}")
            return None

    async def _validate_email(
        self,
        email: str,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Validate email using LeadMagic email-validation API.

        Args:
            email: Email to validate
            name: Optional name for better validation

        Returns:
            Validation result with company data
        """
        url = f"{self.BASE_URL}/people/email-validation"

        first_name, last_name = self._split_name(name) if name else ("", "")
        payload = {
            "email": email,
            "first_name": first_name or "Unknown",
            "last_name": last_name or "Unknown",
        }

        try:
            response = await self._make_request("POST", url, json=payload)
            if response and response.get("credits_consumed"):
                logger.info(f"LeadMagic email-validation consumed {response.get('credits_consumed')} credits")
            return response
        except Exception as e:
            logger.error(f"LeadMagic email-validation error: {e}")
            return None

    async def _find_email(
        self,
        first_name: str,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Find email using LeadMagic email-finder API.

        Args:
            first_name: Person's first name
            last_name: Person's last name
            domain: Company domain
            company_name: Company name

        Returns:
            Email finder result with verified email
        """
        url = f"{self.BASE_URL}/people/email-finder"
        payload = {
            "first_name": first_name,
        }
        if last_name:
            payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if company_name:
            payload["company_name"] = company_name

        try:
            response = await self._make_request("POST", url, json=payload)
            if response and response.get("credits_consumed"):
                logger.info(f"LeadMagic email-finder consumed {response.get('credits_consumed')} credits")
            return response
        except Exception as e:
            logger.error(f"LeadMagic email-finder error: {e}")
            return None

    async def _find_mobile(
        self,
        profile_url: Optional[str] = None,
        work_email: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Find mobile number using LeadMagic mobile-finder API.

        Args:
            profile_url: LinkedIn profile URL
            work_email: Work email address

        Returns:
            Mobile finder result
        """
        url = f"{self.BASE_URL}/people/mobile-finder"
        payload = {}
        if profile_url:
            payload["profile_url"] = profile_url
        if work_email:
            payload["work_email"] = work_email

        if not payload:
            return None

        try:
            response = await self._make_request("POST", url, json=payload)
            if response and response.get("credits_consumed"):
                logger.info(f"LeadMagic mobile-finder consumed {response.get('credits_consumed')} credits")
            return response
        except Exception as e:
            logger.error(f"LeadMagic mobile-finder error: {e}")
            return None

    async def verify_email(self, email: str) -> dict[str, Any]:
        """Verify email address using LeadMagic."""
        result = await self._validate_email(email)
        if result:
            return {
                "email": email,
                "verified": result.get("email_status") == "valid",
                "deliverable": result.get("email_status") == "valid",
                "status": result.get("email_status"),
                "message": result.get("message"),
                "mx_provider": result.get("mx_provider"),
                "is_catch_all": result.get("is_domain_catch_all", False),
                "confidence": 0.95 if result.get("email_status") == "valid" else 0.3,
            }
        return {
            "email": email,
            "verified": False,
            "deliverable": None,
            "confidence": 0.0,
        }

    async def get_credits(self) -> Optional[dict[str, Any]]:
        """Get current credit balance."""
        # Note: LeadMagic MCP has get_credits but may not have direct API endpoint
        # This would need to be verified with their API
        return None

    def _split_name(self, name: Optional[str]) -> tuple[str, Optional[str]]:
        """Split full name into first and last name."""
        if not name:
            return "", None
        parts = name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else None
        return first_name, last_name

    def _map_profile_to_prospect(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map LeadMagic profile-search response to prospect model."""
        return {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "full_name": data.get("full_name"),
            "title": data.get("professional_title"),
            "company_name": data.get("company_name"),
            "company_domain": data.get("company_website", "").replace("https://", "").replace("http://", "").rstrip("/") if data.get("company_website") else None,
            "seniority_level": self._infer_seniority(data.get("professional_title", "")),
            "contact_info": {
                "email": None,  # Profile search doesn't return email
                "phone": None,
            },
            "social_profiles": {
                "linkedin_url": data.get("profile_url"),
                "linkedin_username": data.get("profile_url", "").split("/in/")[-1].rstrip("/") if "/in/" in data.get("profile_url", "") else None,
            },
            "linkedin_insights": {
                "headline": data.get("professional_title"),
                "summary": data.get("bio"),
                "location": data.get("location"),
                "industry": data.get("company_industry"),
                "skills": [],  # Not returned by profile-search
                "experience": data.get("work_experience", []),
                "education": data.get("education", []),
                "total_tenure_years": data.get("total_tenure_years"),
            },
        }

    def _merge_validation_data(self, result: dict[str, Any], validation: dict[str, Any]) -> None:
        """Merge email validation data into result."""
        if "contact_info" not in result:
            result["contact_info"] = {}

        result["contact_info"]["email"] = validation.get("email")
        result["contact_info"]["email_verified"] = validation.get("email_status") == "valid"

        # Company data from validation
        if validation.get("company_name"):
            result["company_name"] = result.get("company_name") or validation.get("company_name")
        if validation.get("company_industry"):
            result["company_industry"] = validation.get("company_industry")
        if validation.get("company_size"):
            result["company_size"] = validation.get("company_size")

    def _merge_email_finder_data(self, result: dict[str, Any], email_data: dict[str, Any]) -> None:
        """Merge email finder data into result."""
        if "contact_info" not in result:
            result["contact_info"] = {}

        if email_data.get("email"):
            result["contact_info"]["email"] = email_data.get("email")
            result["contact_info"]["email_verified"] = email_data.get("status") == "valid"

        # Company data
        if email_data.get("company_name"):
            result["company_name"] = result.get("company_name") or email_data.get("company_name")
        if email_data.get("company_industry"):
            result["company_industry"] = email_data.get("company_industry")
        if email_data.get("company_size"):
            result["company_size"] = email_data.get("company_size")

    def _map_company_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map LeadMagic response to company model."""
        return {
            "name": data.get("company_name"),
            "domain": data.get("domain") or (data.get("email", "").split("@")[-1] if data.get("email") else None),
            "industry": data.get("company_industry"),
            "employee_range": data.get("company_size"),
            "founded_year": data.get("company_founded"),
            "social_profiles": {
                "linkedin_url": data.get("company_linkedin_url"),
                "twitter_url": data.get("company_twitter_url"),
                "facebook_url": data.get("company_facebook_url"),
            },
        }

    def _infer_seniority(self, title: str) -> Optional[str]:
        """Infer seniority level from job title."""
        title_lower = title.lower()
        if any(x in title_lower for x in ["ceo", "cto", "cfo", "coo", "chief", "founder", "owner", "president"]):
            return "executive"
        if any(x in title_lower for x in ["vp", "vice president", "svp", "evp"]):
            return "vp"
        if any(x in title_lower for x in ["director", "head of"]):
            return "director"
        if any(x in title_lower for x in ["manager", "lead", "principal"]):
            return "manager"
        if any(x in title_lower for x in ["senior", "sr.", "staff"]):
            return "senior"
        if any(x in title_lower for x in ["junior", "jr.", "associate", "entry"]):
            return "entry"
        return "individual_contributor"
