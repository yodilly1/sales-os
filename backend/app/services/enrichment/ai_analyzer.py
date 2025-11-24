"""AI-powered company analysis using Claude."""

import json
import logging
from typing import Any, Optional

from app.core.config import settings
from app.services.claude_client import ClaudeClient, get_claude_client
from app.models.prospect import AIInsights

logger = logging.getLogger(__name__)


# System prompt for company analysis
COMPANY_ANALYSIS_SYSTEM_PROMPT = """You are a business intelligence analyst specializing in company research.
Your role is to analyze search results and web data to extract meaningful business insights.

Focus on identifying:
1. Revenue model (SaaS, marketplace, services, etc.)
2. Business model (B2B, B2C, B2B2C, etc.)
3. Target market and customer segments
4. Growth stage (early-stage, growth, mature)
5. Key competitive advantages
6. Potential pain points and challenges
7. Market opportunities

Be concise and data-driven in your analysis. Only include insights that are supported by the provided data.
If information is not available, indicate "Unknown" rather than speculating."""


ANALYSIS_PROMPT_TEMPLATE = """Analyze the following company data and provide business intelligence insights.

Company: {company_name}
Domain: {domain}

Search Results:
{search_results}

News Articles:
{news_articles}

Funding Information:
{funding_info}

Based on this data, provide a JSON response with the following structure:
{{
    "revenue_model": "primary revenue model (e.g., SaaS, Marketplace, Services, Freemium, etc.)",
    "business_model": "business model type (e.g., B2B, B2C, B2B2C, D2C)",
    "target_market": "primary target market or customer segment",
    "key_findings": ["list of 3-5 key business insights"],
    "pain_points": ["potential pain points or challenges (2-3)"],
    "opportunities": ["potential opportunities for engagement (2-3)"],
    "competitive_position": "brief description of competitive position",
    "growth_stage": "estimated growth stage (seed, early, growth, mature, declining)",
    "confidence_score": 0.0 to 1.0 based on data quality and completeness
}}

Only include information that is supported by the provided data. Use "Unknown" for fields where data is insufficient."""


class AIAnalyzer:
    """AI-powered analyzer for company and prospect intelligence."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize the AI analyzer.

        Args:
            claude_client: Optional Claude client. If not provided, uses default.
        """
        self.claude_client = claude_client or get_claude_client()

    @property
    def is_configured(self) -> bool:
        """Check if the analyzer is properly configured."""
        return bool(settings.claude_api_key or settings.anthropic_api_key)

    async def analyze_company(
        self,
        company_name: str,
        domain: Optional[str] = None,
        search_results: Optional[list[dict]] = None,
        news_articles: Optional[list[dict]] = None,
        funding_info: Optional[dict] = None,
    ) -> AIInsights:
        """Analyze company data and generate AI insights.

        Args:
            company_name: Name of the company
            domain: Company domain
            search_results: List of search results from web research
            news_articles: List of news articles
            funding_info: Funding information if available

        Returns:
            AIInsights with analysis results
        """
        if not self.is_configured:
            logger.warning("Claude API not configured, returning empty insights")
            return AIInsights()

        # Format search results for the prompt
        formatted_search = self._format_search_results(search_results or [])
        formatted_news = self._format_news_articles(news_articles or [])
        formatted_funding = self._format_funding_info(funding_info)

        # Build the analysis prompt
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            company_name=company_name,
            domain=domain or "Not provided",
            search_results=formatted_search,
            news_articles=formatted_news,
            funding_info=formatted_funding,
        )

        try:
            # Generate analysis using Claude
            result, response = await self.claude_client.generate_json(
                prompt=prompt,
                system_prompt=COMPANY_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            logger.info(
                f"Company analysis completed for {company_name}. "
                f"Tokens: {response.input_tokens} in, {response.output_tokens} out"
            )

            return AIInsights(
                revenue_model=result.get("revenue_model"),
                business_model=result.get("business_model"),
                target_market=result.get("target_market"),
                key_findings=result.get("key_findings", []),
                pain_points=result.get("pain_points", []),
                opportunities=result.get("opportunities", []),
                competitive_position=result.get("competitive_position"),
                growth_stage=result.get("growth_stage"),
                confidence_score=min(max(result.get("confidence_score", 0.0), 0.0), 1.0),
            )

        except Exception as e:
            logger.error(f"Error analyzing company {company_name}: {e}")
            return AIInsights()

    async def classify_revenue_model(
        self,
        company_name: str,
        description: Optional[str] = None,
        website_content: Optional[str] = None,
    ) -> str:
        """Classify a company's revenue model.

        Args:
            company_name: Name of the company
            description: Company description
            website_content: Content from company website

        Returns:
            Revenue model classification string
        """
        if not self.is_configured:
            return "Unknown"

        prompt = f"""Classify the revenue model for this company:

Company: {company_name}
Description: {description or "Not provided"}
Website Content: {website_content[:2000] if website_content else "Not provided"}

Classify as one of:
- SaaS (Software as a Service)
- Marketplace
- E-commerce
- Services/Consulting
- Freemium
- Subscription
- Transaction-based
- Advertising
- Hardware
- Licensing
- Hybrid
- Unknown

Return only the classification name, nothing else."""

        try:
            response = await self.claude_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=50,
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error classifying revenue model: {e}")
            return "Unknown"

    async def extract_key_insights(
        self,
        company_name: str,
        text_content: str,
        max_insights: int = 5,
    ) -> list[str]:
        """Extract key business insights from text content.

        Args:
            company_name: Name of the company
            text_content: Text content to analyze
            max_insights: Maximum number of insights to return

        Returns:
            List of key insight strings
        """
        if not self.is_configured or not text_content:
            return []

        prompt = f"""Extract the {max_insights} most important business insights about {company_name} from this text:

{text_content[:4000]}

Return a JSON array of strings, each being a concise insight (1-2 sentences max).
Focus on: growth, funding, product updates, partnerships, challenges, and market position.

Example format:
["Insight 1", "Insight 2", "Insight 3"]"""

        try:
            result, _ = await self.claude_client.generate_json(
                prompt=prompt,
                temperature=0.3,
            )

            if isinstance(result, list):
                return result[:max_insights]
            return []

        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return []

    async def analyze_with_fresh_data(
        self,
        company_name: str,
        web_research_data: dict[str, Any],
    ) -> AIInsights:
        """Analyze company using fresh web research data.

        This is the main entry point for analyzing a company with
        data from the WebResearchProvider.

        Args:
            company_name: Name of the company
            web_research_data: Data from WebResearchProvider

        Returns:
            AIInsights with comprehensive analysis
        """
        return await self.analyze_company(
            company_name=company_name,
            domain=web_research_data.get("domain"),
            search_results=web_research_data.get("search_results", []),
            news_articles=web_research_data.get("news", []),
            funding_info=web_research_data.get("funding"),
        )

    def _format_search_results(self, results: list[dict]) -> str:
        """Format search results for the prompt."""
        if not results:
            return "No search results available"

        formatted = []
        for i, result in enumerate(results[:10], 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No description")
            url = result.get("url", "")
            formatted.append(f"{i}. {title}\n   {snippet}\n   Source: {url}")

        return "\n\n".join(formatted)

    def _format_news_articles(self, articles: list[dict]) -> str:
        """Format news articles for the prompt."""
        if not articles:
            return "No news articles available"

        formatted = []
        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            date = article.get("published_at") or article.get("date", "Unknown date")
            summary = article.get("summary") or article.get("snippet", "No summary")
            formatted.append(f"{i}. [{date}] {title}\n   Source: {source}\n   {summary}")

        return "\n\n".join(formatted)

    def _format_funding_info(self, funding: Optional[dict]) -> str:
        """Format funding information for the prompt."""
        if not funding:
            return "No funding information available"

        parts = []
        if funding.get("amount"):
            parts.append(f"Amount: {funding['amount']}")
        if funding.get("stage"):
            parts.append(f"Stage: {funding['stage']}")
        if funding.get("source_title"):
            parts.append(f"Source: {funding['source_title']}")
        if funding.get("source_date"):
            parts.append(f"Date: {funding['source_date']}")

        return "\n".join(parts) if parts else "No funding details available"


def get_ai_analyzer() -> AIAnalyzer:
    """Get AI analyzer instance."""
    return AIAnalyzer()
