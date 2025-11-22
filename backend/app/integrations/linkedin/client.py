"""
LinkedIn API Client

Handles communication with LinkedIn APIs including:
- LinkedIn Marketing API
- LinkedIn Voyager API (unofficial)
- Sales Navigator integration
- Third-party enrichment services (as fallback)
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

import httpx

from .exceptions import (
    LinkedInAPIError,
    LinkedInAuthError,
    LinkedInConnectionError,
    LinkedInNotFoundError,
    LinkedInPrivacyError,
    LinkedInRateLimitError,
)
from .parser import LinkedInURLParser
from .rate_limiter import LinkedInRateLimiter, get_rate_limiter

logger = logging.getLogger(__name__)


class BaseLinkedInClient(ABC):
    """Abstract base class for LinkedIn clients"""

    @abstractmethod
    async def get_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch profile data"""
        pass

    @abstractmethod
    async def get_company(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch company data"""
        pass

    @abstractmethod
    async def search_profiles(self, query: str, **filters) -> List[Dict[str, Any]]:
        """Search for profiles"""
        pass


class LinkedInClient:
    """
    LinkedIn API Client

    Supports multiple backends:
    - LinkedIn Official API (requires OAuth)
    - Third-party enrichment services (Proxycurl, Apollo, etc.)
    - Direct scraping (not recommended for production)

    Configuration via environment variables:
    - LINKEDIN_CLIENT_ID: OAuth client ID
    - LINKEDIN_CLIENT_SECRET: OAuth client secret
    - LINKEDIN_ACCESS_TOKEN: Pre-authorized access token
    - LINKEDIN_ENRICHMENT_PROVIDER: "proxycurl", "apollo", "clearbit"
    - LINKEDIN_ENRICHMENT_API_KEY: API key for enrichment provider
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        enrichment_provider: Optional[str] = None,
        enrichment_api_key: Optional[str] = None,
        rate_limiter: Optional[LinkedInRateLimiter] = None,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 3600,  # 1 hour default
    ):
        # OAuth credentials
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")

        # Enrichment provider configuration
        self.enrichment_provider = enrichment_provider or os.getenv(
            "LINKEDIN_ENRICHMENT_PROVIDER", "proxycurl"
        )
        self.enrichment_api_key = enrichment_api_key or os.getenv(
            "LINKEDIN_ENRICHMENT_API_KEY"
        )

        # Rate limiter
        self.rate_limiter = rate_limiter or get_rate_limiter()

        # In-memory cache
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

        # HTTP client
        self._http_client: Optional[httpx.AsyncClient] = None

        # API endpoints
        self.LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
        self.PROXYCURL_API_BASE = "https://nubela.co/proxycurl/api"
        self.APOLLO_API_BASE = "https://api.apollo.io/v1"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _get_cache_key(self, key_type: str, identifier: str) -> str:
        """Generate a cache key"""
        return hashlib.md5(f"{key_type}:{identifier}".encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache if not expired"""
        if not self.cache_enabled:
            return None

        cached = self._cache.get(key)
        if cached:
            if time.time() < cached.get("expires_at", 0):
                return cached.get("data")
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Dict[str, Any]):
        """Set item in cache"""
        if self.cache_enabled:
            self._cache[key] = {
                "data": data,
                "expires_at": time.time() + self.cache_ttl,
                "cached_at": time.time(),
            }

    async def get_profile(
        self,
        linkedin_url: str,
        force_refresh: bool = False,
        include_experiences: bool = True,
        include_education: bool = True,
        include_skills: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch a LinkedIn profile.

        Args:
            linkedin_url: LinkedIn profile URL
            force_refresh: Bypass cache
            include_experiences: Include work history
            include_education: Include education
            include_skills: Include skills

        Returns:
            Profile data dictionary
        """
        # Parse and normalize URL
        parsed = LinkedInURLParser.parse(linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            raise LinkedInNotFoundError(
                f"Invalid LinkedIn profile URL: {linkedin_url}",
                resource_type="profile",
                resource_id=linkedin_url,
            )

        # Check cache
        cache_key = self._get_cache_key("profile", parsed.identifier)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for profile: {parsed.identifier}")
                return {**cached, "_cached": True}

        # Rate limit
        await self.rate_limiter.acquire("profile_enrichment")

        # Fetch from appropriate provider
        profile_data = await self._fetch_profile(
            parsed.normalized_url or linkedin_url,
            include_experiences=include_experiences,
            include_education=include_education,
            include_skills=include_skills,
        )

        # Cache result
        self._set_cache(cache_key, profile_data)

        return profile_data

    async def _fetch_profile(
        self,
        linkedin_url: str,
        include_experiences: bool = True,
        include_education: bool = True,
        include_skills: bool = True,
    ) -> Dict[str, Any]:
        """Fetch profile from configured provider"""

        if self.enrichment_provider == "proxycurl":
            return await self._fetch_profile_proxycurl(
                linkedin_url,
                include_experiences,
                include_education,
                include_skills,
            )
        elif self.enrichment_provider == "apollo":
            return await self._fetch_profile_apollo(linkedin_url)
        elif self.enrichment_provider == "linkedin_api":
            return await self._fetch_profile_linkedin_api(linkedin_url)
        else:
            # Default to mock data for development
            return self._get_mock_profile(linkedin_url)

    async def _fetch_profile_proxycurl(
        self,
        linkedin_url: str,
        include_experiences: bool,
        include_education: bool,
        include_skills: bool,
    ) -> Dict[str, Any]:
        """Fetch profile using Proxycurl API"""
        if not self.enrichment_api_key:
            raise LinkedInAuthError("Proxycurl API key not configured")

        client = await self._get_http_client()

        params = {
            "linkedin_profile_url": linkedin_url,
            "extra": "include",
            "github_profile_id": "include",
            "facebook_profile_id": "include",
            "twitter_profile_id": "include",
            "personal_contact_number": "include",
            "personal_email": "include",
            "inferred_salary": "include",
            "skills": "include" if include_skills else "exclude",
            "use_cache": "if-present",
            "fallback_to_cache": "on-error",
        }

        try:
            response = await client.get(
                f"{self.PROXYCURL_API_BASE}/v2/linkedin",
                params=params,
                headers={"Authorization": f"Bearer {self.enrichment_api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                return self._normalize_proxycurl_profile(data)
            elif response.status_code == 404:
                raise LinkedInNotFoundError(
                    "Profile not found",
                    resource_type="profile",
                    resource_id=linkedin_url,
                )
            elif response.status_code == 429:
                raise LinkedInRateLimitError(
                    "Proxycurl rate limit exceeded",
                    retry_after=60,
                )
            elif response.status_code == 401:
                raise LinkedInAuthError("Invalid Proxycurl API key")
            else:
                raise LinkedInAPIError(
                    f"Proxycurl API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to Proxycurl: {str(e)}")

    def _normalize_proxycurl_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Proxycurl response to our schema"""
        experiences = []
        for exp in data.get("experiences", []):
            experiences.append({
                "title": exp.get("title"),
                "company_name": exp.get("company"),
                "company_linkedin_url": exp.get("company_linkedin_profile_url"),
                "location": exp.get("location"),
                "start_date": self._parse_date(exp.get("starts_at")),
                "end_date": self._parse_date(exp.get("ends_at")),
                "is_current": exp.get("ends_at") is None,
                "description": exp.get("description"),
            })

        education = []
        for edu in data.get("education", []):
            education.append({
                "school_name": edu.get("school"),
                "school_linkedin_url": edu.get("school_linkedin_profile_url"),
                "degree": edu.get("degree_name"),
                "field_of_study": edu.get("field_of_study"),
                "start_year": edu.get("starts_at", {}).get("year") if edu.get("starts_at") else None,
                "end_year": edu.get("ends_at", {}).get("year") if edu.get("ends_at") else None,
                "description": edu.get("description"),
                "activities": edu.get("activities_and_societies"),
            })

        skills = [{"name": s, "endorsement_count": 0} for s in data.get("skills", [])]

        return {
            "linkedin_id": data.get("public_identifier"),
            "linkedin_url": f"https://www.linkedin.com/in/{data.get('public_identifier', '')}",
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "headline": data.get("headline"),
            "summary": data.get("summary"),
            "location": data.get("city"),
            "country": data.get("country_full_name"),
            "industry": data.get("industry"),
            "profile_picture_url": data.get("profile_pic_url"),
            "banner_image_url": data.get("background_cover_image_url"),
            "current_title": data.get("occupation"),
            "current_company": experiences[0]["company_name"] if experiences else None,
            "current_company_linkedin_url": experiences[0]["company_linkedin_url"] if experiences else None,
            "email": data.get("personal_emails", [None])[0] if data.get("personal_emails") else None,
            "phone": data.get("personal_numbers", [None])[0] if data.get("personal_numbers") else None,
            "connections_count": data.get("connections"),
            "followers_count": data.get("follower_count"),
            "experiences": experiences,
            "education": education,
            "skills": skills,
            "languages": data.get("languages", []),
            "is_open_to_work": data.get("is_open_to_work", False),
            "is_hiring": data.get("is_hiring", False),
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "proxycurl",
        }

    async def _fetch_profile_apollo(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch profile using Apollo API"""
        if not self.enrichment_api_key:
            raise LinkedInAuthError("Apollo API key not configured")

        client = await self._get_http_client()

        try:
            response = await client.post(
                f"{self.APOLLO_API_BASE}/people/match",
                json={
                    "api_key": self.enrichment_api_key,
                    "linkedin_url": linkedin_url,
                },
            )

            if response.status_code == 200:
                data = response.json()
                person = data.get("person", {})
                return self._normalize_apollo_profile(person, linkedin_url)
            elif response.status_code == 404:
                raise LinkedInNotFoundError(
                    "Profile not found",
                    resource_type="profile",
                    resource_id=linkedin_url,
                )
            elif response.status_code == 429:
                raise LinkedInRateLimitError("Apollo rate limit exceeded")
            else:
                raise LinkedInAPIError(
                    f"Apollo API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to Apollo: {str(e)}")

    def _normalize_apollo_profile(
        self, data: Dict[str, Any], linkedin_url: str
    ) -> Dict[str, Any]:
        """Normalize Apollo response to our schema"""
        employment = data.get("employment_history", [])
        experiences = []
        for emp in employment:
            experiences.append({
                "title": emp.get("title"),
                "company_name": emp.get("organization_name"),
                "start_date": emp.get("start_date"),
                "end_date": emp.get("end_date"),
                "is_current": emp.get("current", False),
            })

        return {
            "linkedin_url": linkedin_url,
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "headline": data.get("headline"),
            "location": data.get("city"),
            "country": data.get("country"),
            "current_title": data.get("title"),
            "current_company": data.get("organization", {}).get("name"),
            "email": data.get("email"),
            "phone": data.get("phone_numbers", [{}])[0].get("raw_number")
            if data.get("phone_numbers")
            else None,
            "experiences": experiences,
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "apollo",
        }

    async def _fetch_profile_linkedin_api(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch profile using official LinkedIn API"""
        if not self.access_token:
            raise LinkedInAuthError("LinkedIn access token not configured")

        client = await self._get_http_client()

        # Extract username from URL
        username = LinkedInURLParser.extract_username(linkedin_url)
        if not username:
            raise LinkedInNotFoundError(
                "Could not extract username from URL",
                resource_type="profile",
                resource_id=linkedin_url,
            )

        try:
            # Note: Official API requires specific permissions and different endpoints
            response = await client.get(
                f"{self.LINKEDIN_API_BASE}/me",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            )

            if response.status_code == 200:
                return self._normalize_linkedin_api_profile(
                    response.json(), linkedin_url
                )
            elif response.status_code == 401:
                raise LinkedInAuthError("LinkedIn access token expired or invalid")
            else:
                raise LinkedInAPIError(
                    f"LinkedIn API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to LinkedIn API: {str(e)}")

    def _normalize_linkedin_api_profile(
        self, data: Dict[str, Any], linkedin_url: str
    ) -> Dict[str, Any]:
        """Normalize official LinkedIn API response"""
        return {
            "linkedin_url": linkedin_url,
            "first_name": data.get("localizedFirstName", ""),
            "last_name": data.get("localizedLastName", ""),
            "headline": data.get("localizedHeadline"),
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "linkedin_api",
        }

    def _get_mock_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Return mock profile data for development"""
        username = LinkedInURLParser.extract_username(linkedin_url) or "unknown"

        return {
            "linkedin_id": username,
            "linkedin_url": f"https://www.linkedin.com/in/{username}",
            "first_name": "John",
            "last_name": "Doe",
            "headline": "VP of Sales | Helping companies grow revenue",
            "summary": "Experienced sales leader with 15+ years driving growth at enterprise companies.",
            "location": "San Francisco, CA",
            "country": "United States",
            "industry": "Software",
            "profile_picture_url": None,
            "current_title": "VP of Sales",
            "current_company": "Acme Corp",
            "email": None,
            "connections_count": 500,
            "followers_count": 1200,
            "experiences": [
                {
                    "title": "VP of Sales",
                    "company_name": "Acme Corp",
                    "location": "San Francisco, CA",
                    "start_date": "2020-01-01",
                    "end_date": None,
                    "is_current": True,
                    "description": "Leading global sales team of 50+ reps.",
                }
            ],
            "education": [
                {
                    "school_name": "Stanford University",
                    "degree": "MBA",
                    "field_of_study": "Business Administration",
                    "start_year": 2008,
                    "end_year": 2010,
                }
            ],
            "skills": [
                {"name": "Sales Strategy", "endorsement_count": 99},
                {"name": "Enterprise Sales", "endorsement_count": 75},
                {"name": "Team Leadership", "endorsement_count": 50},
            ],
            "languages": ["English", "Spanish"],
            "is_open_to_work": False,
            "is_hiring": True,
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "mock",
            "_is_mock": True,
        }

    async def get_company(
        self,
        linkedin_url: str,
        force_refresh: bool = False,
        include_key_employees: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch a LinkedIn company page.

        Args:
            linkedin_url: LinkedIn company URL
            force_refresh: Bypass cache
            include_key_employees: Include top employees

        Returns:
            Company data dictionary
        """
        # Parse and normalize URL
        parsed = LinkedInURLParser.parse(linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            raise LinkedInNotFoundError(
                f"Invalid LinkedIn company URL: {linkedin_url}",
                resource_type="company",
                resource_id=linkedin_url,
            )

        # Check cache
        cache_key = self._get_cache_key("company", parsed.identifier)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for company: {parsed.identifier}")
                return {**cached, "_cached": True}

        # Rate limit
        await self.rate_limiter.acquire("company_enrichment")

        # Fetch from provider
        company_data = await self._fetch_company(
            parsed.normalized_url or linkedin_url,
            include_key_employees,
        )

        # Cache result
        self._set_cache(cache_key, company_data)

        return company_data

    async def _fetch_company(
        self,
        linkedin_url: str,
        include_key_employees: bool = False,
    ) -> Dict[str, Any]:
        """Fetch company from configured provider"""

        if self.enrichment_provider == "proxycurl":
            return await self._fetch_company_proxycurl(
                linkedin_url, include_key_employees
            )
        elif self.enrichment_provider == "apollo":
            return await self._fetch_company_apollo(linkedin_url)
        else:
            return self._get_mock_company(linkedin_url)

    async def _fetch_company_proxycurl(
        self,
        linkedin_url: str,
        include_key_employees: bool = False,
    ) -> Dict[str, Any]:
        """Fetch company using Proxycurl API"""
        if not self.enrichment_api_key:
            raise LinkedInAuthError("Proxycurl API key not configured")

        client = await self._get_http_client()

        params = {
            "linkedin_company_profile_url": linkedin_url,
            "categories": "include",
            "funding_data": "include",
            "extra": "include",
            "exit_data": "include",
            "acquisitions": "include",
            "use_cache": "if-present",
        }

        try:
            response = await client.get(
                f"{self.PROXYCURL_API_BASE}/linkedin/company",
                params=params,
                headers={"Authorization": f"Bearer {self.enrichment_api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                return self._normalize_proxycurl_company(data)
            elif response.status_code == 404:
                raise LinkedInNotFoundError(
                    "Company not found",
                    resource_type="company",
                    resource_id=linkedin_url,
                )
            elif response.status_code == 429:
                raise LinkedInRateLimitError("Proxycurl rate limit exceeded")
            else:
                raise LinkedInAPIError(
                    f"Proxycurl API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to Proxycurl: {str(e)}")

    def _normalize_proxycurl_company(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Proxycurl company response"""
        return {
            "linkedin_id": data.get("universal_name_id"),
            "linkedin_url": data.get("linkedin_internal_id")
            and f"https://www.linkedin.com/company/{data.get('universal_name_id')}",
            "name": data.get("name", ""),
            "tagline": data.get("tagline"),
            "description": data.get("description"),
            "website": data.get("website"),
            "industry": data.get("industry"),
            "company_size": data.get("company_size_on_linkedin"),
            "employee_count": data.get("company_size_on_linkedin"),
            "headquarters_location": ", ".join(
                filter(
                    None,
                    [
                        data.get("hq", {}).get("city"),
                        data.get("hq", {}).get("state"),
                        data.get("hq", {}).get("country"),
                    ],
                )
            ),
            "headquarters_city": data.get("hq", {}).get("city"),
            "headquarters_country": data.get("hq", {}).get("country"),
            "founded_year": data.get("founded_year"),
            "company_type": data.get("company_type"),
            "specialties": data.get("specialities", []),
            "logo_url": data.get("profile_pic_url"),
            "followers_count": data.get("follower_count"),
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "proxycurl",
        }

    async def _fetch_company_apollo(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch company using Apollo API"""
        if not self.enrichment_api_key:
            raise LinkedInAuthError("Apollo API key not configured")

        client = await self._get_http_client()

        try:
            response = await client.post(
                f"{self.APOLLO_API_BASE}/organizations/enrich",
                json={
                    "api_key": self.enrichment_api_key,
                    "linkedin_url": linkedin_url,
                },
            )

            if response.status_code == 200:
                data = response.json()
                org = data.get("organization", {})
                return self._normalize_apollo_company(org, linkedin_url)
            else:
                raise LinkedInAPIError(
                    f"Apollo API error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to Apollo: {str(e)}")

    def _normalize_apollo_company(
        self, data: Dict[str, Any], linkedin_url: str
    ) -> Dict[str, Any]:
        """Normalize Apollo company response"""
        return {
            "linkedin_url": linkedin_url,
            "name": data.get("name", ""),
            "description": data.get("short_description"),
            "website": data.get("website_url"),
            "industry": data.get("industry"),
            "employee_count": data.get("estimated_num_employees"),
            "founded_year": data.get("founded_year"),
            "logo_url": data.get("logo_url"),
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "apollo",
        }

    def _get_mock_company(self, linkedin_url: str) -> Dict[str, Any]:
        """Return mock company data for development"""
        slug = LinkedInURLParser.extract_company_slug(linkedin_url) or "unknown"

        return {
            "linkedin_id": slug,
            "linkedin_url": f"https://www.linkedin.com/company/{slug}",
            "name": "Acme Corporation",
            "tagline": "Building the future, today",
            "description": "Acme Corporation is a leading provider of innovative solutions for enterprise customers worldwide.",
            "website": "https://www.acme.com",
            "industry": "Computer Software",
            "company_size": "201-500",
            "employee_count": 350,
            "headquarters_location": "San Francisco, CA, United States",
            "headquarters_city": "San Francisco",
            "headquarters_country": "United States",
            "founded_year": 2010,
            "company_type": "Privately Held",
            "specialties": ["Enterprise Software", "Cloud Computing", "AI/ML"],
            "logo_url": None,
            "followers_count": 15000,
            "last_enriched_at": datetime.now().isoformat(),
            "enrichment_source": "mock",
            "_is_mock": True,
        }

    async def search_profiles(
        self,
        query: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for LinkedIn profiles.

        Args:
            query: Free-text search query
            first_name: Filter by first name
            last_name: Filter by last name
            company: Filter by company name
            title: Filter by job title
            location: Filter by location
            limit: Max results to return

        Returns:
            List of matching profiles
        """
        await self.rate_limiter.acquire("profile_search")

        # Implementation depends on provider
        if self.enrichment_provider == "proxycurl":
            return await self._search_profiles_proxycurl(
                query, first_name, last_name, company, title, location, limit
            )
        else:
            # Return empty for unsupported providers
            return []

    async def _search_profiles_proxycurl(
        self,
        query: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        company: Optional[str],
        title: Optional[str],
        location: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search profiles using Proxycurl Person Search API"""
        if not self.enrichment_api_key:
            raise LinkedInAuthError("Proxycurl API key not configured")

        client = await self._get_http_client()

        params = {
            "page_size": min(limit, 100),
        }

        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if company:
            params["current_company_name"] = company
        if title:
            params["current_role_title"] = title
        if location:
            params["city"] = location

        try:
            response = await client.get(
                f"{self.PROXYCURL_API_BASE}/search/person",
                params=params,
                headers={"Authorization": f"Bearer {self.enrichment_api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "linkedin_url": result.get("linkedin_profile_url"),
                        "first_name": result.get("first_name"),
                        "last_name": result.get("last_name"),
                        "headline": result.get("headline"),
                        "location": result.get("city"),
                        "profile_picture_url": result.get("profile_pic_url"),
                    }
                    for result in data.get("results", [])
                ]
            else:
                raise LinkedInAPIError(
                    f"Proxycurl search error: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.RequestError as e:
            raise LinkedInConnectionError(f"Failed to connect to Proxycurl: {str(e)}")

    def _parse_date(self, date_dict: Optional[Dict]) -> Optional[str]:
        """Parse date dictionary to ISO string"""
        if not date_dict:
            return None

        year = date_dict.get("year")
        month = date_dict.get("month", 1)
        day = date_dict.get("day", 1)

        if year:
            try:
                return datetime(year, month, day).isoformat()
            except ValueError:
                return f"{year}-01-01"
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
