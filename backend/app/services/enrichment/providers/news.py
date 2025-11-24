"""News API provider for company and prospect news."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from app.schemas.enrichment import EnrichmentSource
from app.models.company import NewsArticle

from .base import EnrichmentProvider

logger = logging.getLogger(__name__)


class NewsProvider(EnrichmentProvider):
    """News API provider for fetching recent news about companies and people."""

    name = "news"
    source = EnrichmentSource.NEWS_API
    BASE_URL = "https://newsapi.org/v2"

    def _get_headers(self) -> dict[str, str]:
        """Get headers with News API key."""
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
        """Find recent news mentions of a prospect."""
        if not self.is_configured:
            logger.warning("News API not configured, skipping")
            return None

        if not name:
            return None

        articles = await self.search_news(
            query=f'"{name}"',
            days_back=90,
            limit=5,
        )

        if articles:
            return {
                "recent_news_mentions": articles,
                "source": self.source,
            }
        return None

    async def enrich_company(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Find recent news about a company."""
        if not self.is_configured:
            logger.warning("News API not configured, skipping")
            return None

        search_term = name or domain
        if not search_term:
            return None

        articles = await self.search_news(
            query=f'"{search_term}"',
            days_back=90,
            limit=10,
        )

        if articles:
            return {
                "recent_news": articles,
                "source": self.source,
            }
        return None

    async def search_news(
        self,
        query: str,
        days_back: int = 30,
        limit: int = 10,
        language: str = "en",
        sort_by: str = "relevancy",
    ) -> list[dict[str, Any]]:
        """Search for news articles matching query."""
        if not self.is_configured:
            return []

        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/everything"
        params = {
            "q": query,
            "from": from_date,
            "language": language,
            "sortBy": sort_by,
            "pageSize": limit,
        }

        data = await self._make_request("GET", url, params=params)
        if data and data.get("articles"):
            return [self._map_article(a) for a in data["articles"]]
        return []

    async def get_top_headlines(
        self,
        category: Optional[str] = None,
        country: str = "us",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get top headlines, optionally filtered by category."""
        if not self.is_configured:
            return []

        url = f"{self.BASE_URL}/top-headlines"
        params = {
            "country": country,
            "pageSize": limit,
        }

        if category:
            params["category"] = category

        data = await self._make_request("GET", url, params=params)
        if data and data.get("articles"):
            return [self._map_article(a) for a in data["articles"]]
        return []

    async def get_company_news(
        self,
        company_name: str,
        include_competitors: bool = False,
        competitors: Optional[list[str]] = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """Get comprehensive news about a company and optionally competitors."""
        result = {
            "company_news": [],
            "competitor_news": {},
            "industry_trends": [],
        }

        # Get company news
        company_articles = await self.search_news(
            query=f'"{company_name}"',
            days_back=days_back,
            limit=10,
        )
        result["company_news"] = company_articles

        # Get competitor news if requested
        if include_competitors and competitors:
            for competitor in competitors[:3]:  # Limit to 3 competitors
                competitor_articles = await self.search_news(
                    query=f'"{competitor}"',
                    days_back=days_back,
                    limit=5,
                )
                result["competitor_news"][competitor] = competitor_articles

        return result

    def _map_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """Map News API article to our model."""
        published_at = None
        if article.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return {
            "title": article.get("title"),
            "url": article.get("url"),
            "source": article.get("source", {}).get("name"),
            "published_at": published_at.isoformat() if published_at else None,
            "summary": article.get("description"),
            "content_preview": article.get("content", "")[:500] if article.get("content") else None,
            "image_url": article.get("urlToImage"),
            "author": article.get("author"),
        }

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis placeholder.

        In production, use NLP service or Claude for sentiment analysis.
        """
        positive_words = ["growth", "success", "profit", "launch", "partnership", "innovation"]
        negative_words = ["loss", "layoff", "decline", "lawsuit", "scandal", "breach"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
