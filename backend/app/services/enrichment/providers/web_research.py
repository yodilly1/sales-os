"""Web Research Provider using Serper API for Google search."""

import logging
from typing import Any, Optional

from app.models.prospect import EnrichmentSource
from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class WebResearchProvider(EnrichmentProvider):
    """Provider for web research using Serper API (Google Search)."""

    name = "web_research"
    source = EnrichmentSource.WEB_RESEARCH

    SERPER_API_URL = "https://google.serper.dev/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 60,
        timeout: float = 30.0,
    ):
        super().__init__(api_key=api_key, rate_limit=rate_limit, timeout=timeout)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Serper API."""
        return {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key or "",
        }

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> Optional[dict[str, Any]]:
        """
        Perform a Google search via Serper API.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            Search results including organic results, news, etc.
        """
        if not self.is_configured:
            logger.warning("Web research provider not configured (missing API key)")
            return None

        payload = {
            "q": query,
            "num": num_results,
        }

        return await self._make_request(
            method="POST",
            url=self.SERPER_API_URL,
            json=payload,
        )

    async def research_company(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Research a company using multiple targeted searches.

        Args:
            company_name: Company name to research
            domain: Company domain (optional, improves accuracy)

        Returns:
            Aggregated research data about the company
        """
        if not self.is_configured:
            return None

        research_data = {
            "company_name": company_name,
            "domain": domain,
            "web_results": [],
            "news_results": [],
            "funding_info": None,
            "key_people": [],
            "recent_news": [],
            "competitors": [],
            "technologies": [],
        }

        # Search for general company info
        general_query = f"{company_name} company"
        if domain:
            general_query += f" site:{domain}"

        general_results = await self.search(general_query)
        if general_results and "organic" in general_results:
            research_data["web_results"] = general_results.get("organic", [])[:5]
            if general_results.get("knowledgeGraph"):
                kg = general_results["knowledgeGraph"]
                research_data["knowledge_graph"] = {
                    "title": kg.get("title"),
                    "description": kg.get("description"),
                    "type": kg.get("type"),
                    "website": kg.get("website"),
                    "attributes": kg.get("attributes", {}),
                }

        # Search for recent news
        news_query = f"{company_name} news"
        news_results = await self.search(news_query)
        if news_results:
            research_data["news_results"] = news_results.get("news", [])[:5]

        # Search for funding information
        funding_query = f"{company_name} funding raised investment"
        funding_results = await self.search(funding_query)
        if funding_results and "organic" in funding_results:
            research_data["funding_snippets"] = [
                {
                    "title": r.get("title"),
                    "snippet": r.get("snippet"),
                    "link": r.get("link"),
                }
                for r in funding_results.get("organic", [])[:3]
            ]

        # Search for key people / leadership
        people_query = f"{company_name} CEO founder leadership team"
        people_results = await self.search(people_query)
        if people_results and "organic" in people_results:
            research_data["leadership_snippets"] = [
                {
                    "title": r.get("title"),
                    "snippet": r.get("snippet"),
                    "link": r.get("link"),
                }
                for r in people_results.get("organic", [])[:3]
            ]

        return research_data

    async def research_person(
        self,
        name: str,
        company: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Research a person using web search.

        Args:
            name: Person's full name
            company: Company name (optional)
            title: Job title (optional)

        Returns:
            Research data about the person
        """
        if not self.is_configured:
            return None

        research_data = {
            "name": name,
            "company": company,
            "web_results": [],
            "linkedin_info": None,
            "publications": [],
            "speaking_engagements": [],
        }

        # Build search query
        query_parts = [name]
        if company:
            query_parts.append(company)
        if title:
            query_parts.append(title)

        query = " ".join(query_parts)
        results = await self.search(query)

        if results and "organic" in results:
            research_data["web_results"] = results.get("organic", [])[:5]

        # Search for LinkedIn profile
        linkedin_query = f"{name} {company or ''} site:linkedin.com/in"
        linkedin_results = await self.search(linkedin_query, num_results=3)
        if linkedin_results and "organic" in linkedin_results:
            for result in linkedin_results.get("organic", []):
                if "linkedin.com/in/" in result.get("link", ""):
                    research_data["linkedin_info"] = {
                        "url": result.get("link"),
                        "title": result.get("title"),
                        "snippet": result.get("snippet"),
                    }
                    break

        return research_data

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich prospect data using web research.

        Args:
            email: Prospect email address
            name: Prospect full name
            company: Company name
            domain: Company domain

        Returns:
            Enriched prospect data from web research
        """
        if not name:
            return None

        research = await self.research_person(name, company)
        if not research:
            return None

        return {
            "web_research": research,
            "source": "web_research",
        }

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Enrich company data using web research.

        Args:
            domain: Company domain
            name: Company name

        Returns:
            Enriched company data from web research
        """
        if not name and not domain:
            return None

        company_name = name or domain.split(".")[0] if domain else ""
        research = await self.research_company(company_name, domain)
        if not research:
            return None

        return {
            "web_research": research,
            "source": "web_research",
        }
