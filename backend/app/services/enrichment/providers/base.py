"""Base class for enrichment data providers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

import httpx

from app.models.prospect import ProspectEnriched, EnrichmentSource
from app.models.company import CompanyEnriched

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls: list[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if rate limit would be exceeded."""
        async with self._lock:
            now = datetime.utcnow()
            # Remove calls older than 1 minute
            self.calls = [c for c in self.calls if (now - c).total_seconds() < 60]

            if len(self.calls) >= self.calls_per_minute:
                # Wait until oldest call expires
                wait_time = 60 - (now - self.calls[0]).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = datetime.utcnow()
                    self.calls = [c for c in self.calls if (now - c).total_seconds() < 60]

            self.calls.append(now)


class EnrichmentProvider(ABC):
    """Abstract base class for enrichment data providers."""

    name: str = "base"
    source: EnrichmentSource = EnrichmentSource.MANUAL

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 60,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return self.api_key is not None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Optional[dict[str, Any]]:
        """Make rate-limited HTTP request."""
        await self.rate_limiter.acquire()

        try:
            client = await self.get_client()
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name} HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                # Rate limited by provider
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(f"{self.name} rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._make_request(method, url, **kwargs)
            return None
        except httpx.RequestError as e:
            logger.error(f"{self.name} request error: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name} unexpected error: {e}")
            return None

    @abstractmethod
    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich prospect data.

        Args:
            email: Prospect email address
            name: Prospect full name
            company: Company name
            domain: Company domain

        Returns:
            Enriched prospect data or None if not found
        """
        pass

    @abstractmethod
    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich company data.

        Args:
            domain: Company domain
            name: Company name

        Returns:
            Enriched company data or None if not found
        """
        pass

    async def verify_email(self, email: str) -> dict[str, Any]:
        """
        Verify if email address is valid and deliverable.

        Args:
            email: Email address to verify

        Returns:
            Verification result with status and confidence
        """
        return {
            "email": email,
            "verified": False,
            "deliverable": None,
            "confidence": 0.0,
        }

    def map_to_prospect(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map provider response to prospect model fields."""
        return {}

    def map_to_company(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map provider response to company model fields."""
        return {}
