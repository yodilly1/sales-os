"""Hunter.io enrichment provider for email verification."""

import logging
from typing import Any, Optional

from app.models.prospect import EnrichmentSource

from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class HunterProvider(EnrichmentProvider):
    """Hunter.io API provider for email finding and verification."""

    name = "hunter"
    source = EnrichmentSource.HUNTER
    BASE_URL = "https://api.hunter.io/v2"

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Find email for prospect using Hunter email finder."""
        if not self.is_configured:
            logger.warning("Hunter not configured, skipping")
            return None

        # If we have an email, verify it
        if email:
            verification = await self.verify_email(email)
            return {
                "contact_info": {
                    "email": email,
                    "email_verified": verification.get("verified", False),
                },
                "source": self.source,
            }

        # Otherwise try to find email
        if name and domain:
            url = f"{self.BASE_URL}/email-finder"
            # Split name
            parts = name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            params = {
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": self.api_key,
            }

            data = await self._make_request("GET", url, params=params)
            if data and data.get("data"):
                result = data["data"]
                return {
                    "contact_info": {
                        "email": result.get("email"),
                        "email_verified": result.get("score", 0) > 80,
                    },
                    "first_name": result.get("first_name"),
                    "last_name": result.get("last_name"),
                    "title": result.get("position"),
                    "company_domain": result.get("domain"),
                    "social_profiles": {
                        "linkedin_url": result.get("linkedin"),
                        "twitter_url": result.get("twitter"),
                    },
                    "source": self.source,
                }

        return None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Get company email pattern and count from Hunter."""
        if not self.is_configured:
            logger.warning("Hunter not configured, skipping")
            return None

        if not domain:
            return None

        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
        }

        data = await self._make_request("GET", url, params=params)
        if data and data.get("data"):
            result = data["data"]
            return {
                "name": result.get("organization"),
                "domain": result.get("domain"),
                "email_pattern": result.get("pattern"),
                "email_count": len(result.get("emails", [])),
                "source": self.source,
            }
        return None

    async def verify_email(self, email: str) -> dict[str, Any]:
        """Verify email address using Hunter verification API."""
        if not self.is_configured:
            return {
                "email": email,
                "verified": False,
                "deliverable": None,
                "confidence": 0.0,
            }

        url = f"{self.BASE_URL}/email-verifier"
        params = {
            "email": email,
            "api_key": self.api_key,
        }

        data = await self._make_request("GET", url, params=params)
        if data and data.get("data"):
            result = data["data"]
            status = result.get("status")
            return {
                "email": email,
                "verified": status == "valid",
                "deliverable": status in ["valid", "accept_all"],
                "confidence": result.get("score", 0) / 100,
                "status": status,
                "disposable": result.get("disposable", False),
                "webmail": result.get("webmail", False),
                "mx_records": result.get("mx_records", False),
                "smtp_server": result.get("smtp_server", False),
                "smtp_check": result.get("smtp_check", False),
            }

        return {
            "email": email,
            "verified": False,
            "deliverable": None,
            "confidence": 0.0,
        }

    async def find_emails_at_company(
        self,
        domain: str,
        limit: int = 10,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Find all emails at a company domain."""
        if not self.is_configured:
            return []

        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "limit": limit,
            "api_key": self.api_key,
        }

        if department:
            params["department"] = department
        if seniority:
            params["seniority"] = seniority

        data = await self._make_request("GET", url, params=params)
        if data and data.get("data", {}).get("emails"):
            emails = data["data"]["emails"]
            return [
                {
                    "email": e.get("value"),
                    "first_name": e.get("first_name"),
                    "last_name": e.get("last_name"),
                    "title": e.get("position"),
                    "department": e.get("department"),
                    "seniority": e.get("seniority"),
                    "confidence": e.get("confidence", 0) / 100,
                    "linkedin_url": e.get("linkedin"),
                    "twitter_url": e.get("twitter"),
                }
                for e in emails
            ]
        return []
