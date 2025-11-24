"""Web research provider using Serper API for Google search."""

import logging
from datetime import datetime
from typing import Any, Optional

from app.models.prospect import EnrichmentSource

from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class WebResearchProvider(EnrichmentProvider):
    """Web research provider using Serper API for Google search enrichment.

    This provider performs Google searches via the Serper API to gather
    real-time company intelligence including news, funding info, and
    business insights.
    """

    name = "web_research"
    source = EnrichmentSource.WEB_RESEARCH
    BASE_URL = "https://google.serper.dev"

    def _get_headers(self) -> dict[str, str]:
        """Get headers with Serper API key."""
        headers = super()._get_headers()
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    async def enrich_prospect(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich prospect using web research.

        Searches for information about the person and their company.
        """
        if not self.is_configured:
            logger.warning("Serper API not configured, skipping web research")
            return None

        if not (name or company):
            logger.info("Name or company required for web research")
            return None

        result = {
            "web_research": {
                "news": [],
                "insights": [],
                "last_updated": datetime.utcnow().isoformat(),
            },
            "source": self.source,
        }

        # Search for person if name provided
        if name and company:
            person_results = await self.search_google(f'"{name}" "{company}"')
            if person_results:
                result["web_research"]["person_mentions"] = person_results[:5]

        return result if result["web_research"].get("person_mentions") else None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Enrich company using comprehensive web research.

        Performs multiple searches to gather:
        - Recent news and press releases
        - Funding information
        - Company description and overview
        - Key business insights
        """
        if not self.is_configured:
            logger.warning("Serper API not configured, skipping web research")
            return None

        company_name = name or domain
        if not company_name:
            logger.info("Company name or domain required for web research")
            return None

        result = {
            "web_research": {
                "news": [],
                "funding": None,
                "description": None,
                "insights": [],
                "search_results": [],
                "last_updated": datetime.utcnow().isoformat(),
            },
            "source": self.source,
        }

        # Perform multiple targeted searches
        search_queries = [
            f'"{company_name}" company news',
            f'"{company_name}" funding raise',
            f'"{company_name}" about company overview',
        ]

        for query in search_queries:
            try:
                search_results = await self.search_google(query, num_results=5)
                if search_results:
                    result["web_research"]["search_results"].extend(search_results)
            except Exception as e:
                logger.error(f"Search error for query '{query}': {e}")

        # Categorize and process search results
        news_items = []
        for item in result["web_research"]["search_results"]:
            # Check if it's a news article
            if self._is_news_article(item):
                news_items.append(self._map_to_news(item))

            # Check for funding information
            if self._contains_funding_info(item):
                funding_info = self._extract_funding_info(item)
                if funding_info and not result["web_research"]["funding"]:
                    result["web_research"]["funding"] = funding_info

        result["web_research"]["news"] = news_items[:10]

        # Get company description from search if available
        if not result["web_research"]["description"]:
            for item in result["web_research"]["search_results"]:
                if item.get("snippet") and len(item["snippet"]) > 50:
                    result["web_research"]["description"] = item["snippet"]
                    break

        return result if result["web_research"]["search_results"] else None

    async def search_google(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
    ) -> list[dict[str, Any]]:
        """Perform a Google search using Serper API.

        Args:
            query: Search query string
            num_results: Number of results to return
            search_type: Type of search ('search', 'news', 'images')

        Returns:
            List of search results
        """
        if not self.is_configured:
            return []

        url = f"{self.BASE_URL}/{search_type}"
        payload = {
            "q": query,
            "num": num_results,
        }

        try:
            data = await self._make_request("POST", url, json=payload)

            if not data:
                return []

            results = []

            # Extract organic results
            organic = data.get("organic", [])
            for item in organic:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "position": item.get("position"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                })

            # Extract news results if present
            news = data.get("news", [])
            for item in news:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "is_news": True,
                })

            # Extract knowledge graph if present
            knowledge_graph = data.get("knowledgeGraph", {})
            if knowledge_graph:
                results.append({
                    "title": knowledge_graph.get("title"),
                    "type": "knowledge_graph",
                    "description": knowledge_graph.get("description"),
                    "website": knowledge_graph.get("website"),
                    "attributes": knowledge_graph.get("attributes", {}),
                })

            return results

        except Exception as e:
            logger.error(f"Serper API error: {e}")
            return []

    async def search_news(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for news articles specifically.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of news articles
        """
        if not self.is_configured:
            return []

        url = f"{self.BASE_URL}/news"
        payload = {
            "q": query,
            "num": num_results,
        }

        try:
            data = await self._make_request("POST", url, json=payload)

            if not data:
                return []

            results = []
            news = data.get("news", [])

            for item in news:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "image_url": item.get("imageUrl"),
                })

            return results

        except Exception as e:
            logger.error(f"Serper news API error: {e}")
            return []

    async def research_company_comprehensive(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> dict[str, Any]:
        """Perform comprehensive company research.

        This is the main research function that gathers all available
        information about a company from web sources.

        Args:
            company_name: Company name to research
            domain: Optional company domain

        Returns:
            Comprehensive research results including news, funding,
            description, and insights
        """
        result = {
            "company_name": company_name,
            "domain": domain,
            "news": [],
            "funding_info": None,
            "company_description": None,
            "key_insights": [],
            "competitors": [],
            "recent_events": [],
            "search_timestamp": datetime.utcnow().isoformat(),
        }

        if not self.is_configured:
            logger.warning("Serper API not configured")
            return result

        # 1. General company search
        general_results = await self.search_google(
            f'"{company_name}" company', num_results=10
        )

        # 2. News search
        news_results = await self.search_news(
            f'"{company_name}"', num_results=10
        )
        result["news"] = [self._map_to_news(n) for n in news_results]

        # 3. Funding search
        funding_results = await self.search_google(
            f'"{company_name}" funding raise series', num_results=5
        )
        for item in funding_results:
            if self._contains_funding_info(item):
                result["funding_info"] = self._extract_funding_info(item)
                break

        # 4. Extract description from knowledge graph or snippets
        for item in general_results:
            if item.get("type") == "knowledge_graph":
                result["company_description"] = item.get("description")
                break
            elif item.get("snippet") and not result["company_description"]:
                result["company_description"] = item["snippet"]

        # 5. Recent events/announcements search
        events_results = await self.search_google(
            f'"{company_name}" announcement launch', num_results=5
        )
        result["recent_events"] = [
            {
                "title": e.get("title"),
                "url": e.get("url"),
                "date": e.get("date"),
                "snippet": e.get("snippet"),
            }
            for e in events_results[:5]
        ]

        return result

    def _is_news_article(self, item: dict[str, Any]) -> bool:
        """Check if a search result is likely a news article."""
        if item.get("is_news"):
            return True

        news_sources = [
            "techcrunch", "bloomberg", "reuters", "cnbc", "forbes",
            "wsj", "nytimes", "venturebeat", "businessinsider",
            "crunchbase", "prnewswire", "businesswire", "yahoo",
        ]

        url = (item.get("url") or "").lower()
        source = (item.get("source") or "").lower()

        return any(ns in url or ns in source for ns in news_sources)

    def _contains_funding_info(self, item: dict[str, Any]) -> bool:
        """Check if a search result contains funding information."""
        funding_keywords = [
            "raise", "funding", "series", "seed", "investment",
            "million", "billion", "valuation", "investor",
        ]

        text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
        return any(kw in text for kw in funding_keywords)

    def _extract_funding_info(self, item: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Extract funding information from a search result."""
        import re

        text = f"{item.get('title', '')} {item.get('snippet', '')}"

        # Try to extract funding amount
        amount_pattern = r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)'
        amount_match = re.search(amount_pattern, text, re.IGNORECASE)

        # Try to extract funding stage
        stage_pattern = r'(seed|series\s*[a-g]|pre-seed|bridge|ipo)'
        stage_match = re.search(stage_pattern, text, re.IGNORECASE)

        if amount_match or stage_match:
            return {
                "amount": amount_match.group(0) if amount_match else None,
                "stage": stage_match.group(1).title() if stage_match else None,
                "source_url": item.get("url"),
                "source_title": item.get("title"),
                "source_date": item.get("date"),
            }

        return None

    def _map_to_news(self, item: dict[str, Any]) -> dict[str, Any]:
        """Map a search result to a news article format."""
        return {
            "title": item.get("title"),
            "url": item.get("url"),
            "source": item.get("source"),
            "published_at": item.get("date"),
            "summary": item.get("snippet"),
            "image_url": item.get("image_url"),
        }
