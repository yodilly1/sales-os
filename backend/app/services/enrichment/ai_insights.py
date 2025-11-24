"""AI Insights Generator for company analysis using Claude."""

import json
import logging
from typing import Any, Optional

from app.services.claude_client import ClaudeClient, create_claude_client

logger = logging.getLogger(__name__)


class AIInsightsGenerator:
    """Generate AI-powered insights from enrichment data."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize with Claude client."""
        self.claude_client = claude_client or create_claude_client()

    async def analyze_company(
        self,
        company_name: str,
        web_research: Optional[dict[str, Any]] = None,
        enrichment_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate AI insights for a company based on web research and enrichment data.

        Args:
            company_name: Name of the company
            web_research: Web research data from Serper
            enrichment_data: Data from other enrichment providers

        Returns:
            AI-generated insights about the company
        """
        # Build context from available data
        context_parts = [f"Company: {company_name}"]

        if web_research:
            # Add knowledge graph info
            if web_research.get("knowledge_graph"):
                kg = web_research["knowledge_graph"]
                context_parts.append(f"\nKnowledge Graph Info:")
                if kg.get("description"):
                    context_parts.append(f"Description: {kg['description']}")
                if kg.get("attributes"):
                    for key, value in kg["attributes"].items():
                        context_parts.append(f"{key}: {value}")

            # Add web results snippets
            if web_research.get("web_results"):
                context_parts.append("\nWeb Search Results:")
                for result in web_research["web_results"][:3]:
                    if result.get("snippet"):
                        context_parts.append(f"- {result['snippet']}")

            # Add news snippets
            if web_research.get("news_results"):
                context_parts.append("\nRecent News:")
                for news in web_research["news_results"][:3]:
                    if news.get("title"):
                        context_parts.append(f"- {news['title']}")

            # Add funding info
            if web_research.get("funding_snippets"):
                context_parts.append("\nFunding Information:")
                for snippet in web_research["funding_snippets"]:
                    if snippet.get("snippet"):
                        context_parts.append(f"- {snippet['snippet']}")

        if enrichment_data:
            if enrichment_data.get("description"):
                context_parts.append(f"\nCompany Description: {enrichment_data['description']}")
            if enrichment_data.get("industry"):
                context_parts.append(f"Industry: {enrichment_data['industry']}")
            if enrichment_data.get("employee_count"):
                context_parts.append(f"Employee Count: {enrichment_data['employee_count']}")

        context = "\n".join(context_parts)

        prompt = f"""Based on the following information about {company_name}, provide a comprehensive business analysis.

{context}

Please provide your analysis in the following JSON format:
{{
    "revenue_model": "Description of how the company generates revenue",
    "target_market": "Who are their primary customers/target market",
    "key_products_services": ["List of main products or services"],
    "competitive_advantages": ["Key competitive advantages"],
    "potential_challenges": ["Potential business challenges"],
    "funding_stage": "Estimated funding stage (Seed, Series A, B, C, etc.) or 'Bootstrapped' if not venture-backed",
    "estimated_revenue_range": "Estimated annual revenue range if determinable",
    "key_findings": ["3-5 most important findings about this company"],
    "sales_approach_recommendations": ["Recommendations for how to approach this company in a sales context"],
    "decision_makers": ["Likely job titles of decision makers to target"]
}}

Provide only the JSON response, no additional text."""

        try:
            response = await self.claude_client.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,
            )

            # Parse JSON response
            if response:
                # Clean up response if needed
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                insights = json.loads(response_text.strip())
                insights["analysis_complete"] = True
                return insights

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI insights JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")

        # Return empty insights on failure
        return {
            "revenue_model": None,
            "target_market": None,
            "key_products_services": [],
            "competitive_advantages": [],
            "potential_challenges": [],
            "funding_stage": None,
            "estimated_revenue_range": None,
            "key_findings": [],
            "sales_approach_recommendations": [],
            "decision_makers": [],
            "analysis_complete": False,
            "error": "Failed to generate AI insights",
        }

    async def analyze_prospect(
        self,
        prospect_name: str,
        prospect_title: Optional[str] = None,
        company_name: Optional[str] = None,
        web_research: Optional[dict[str, Any]] = None,
        enrichment_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate AI insights for a prospect.

        Args:
            prospect_name: Name of the prospect
            prospect_title: Job title
            company_name: Company name
            web_research: Web research data
            enrichment_data: Data from other enrichment providers

        Returns:
            AI-generated insights about the prospect
        """
        context_parts = [f"Prospect: {prospect_name}"]
        if prospect_title:
            context_parts.append(f"Title: {prospect_title}")
        if company_name:
            context_parts.append(f"Company: {company_name}")

        if web_research:
            if web_research.get("linkedin_info"):
                li = web_research["linkedin_info"]
                context_parts.append(f"\nLinkedIn: {li.get('url', '')}")
                if li.get("snippet"):
                    context_parts.append(f"Profile: {li['snippet']}")

            if web_research.get("web_results"):
                context_parts.append("\nWeb Presence:")
                for result in web_research["web_results"][:3]:
                    if result.get("snippet"):
                        context_parts.append(f"- {result['snippet']}")

        context = "\n".join(context_parts)

        prompt = f"""Based on the following information about {prospect_name}, provide insights useful for sales outreach.

{context}

Please provide your analysis in the following JSON format:
{{
    "role_responsibilities": "Likely responsibilities based on title and company",
    "buying_authority": "low/medium/high - likelihood they have purchasing authority",
    "interests_priorities": ["Likely professional interests and priorities"],
    "pain_points": ["Potential pain points based on role"],
    "conversation_starters": ["Personalized conversation starters for outreach"],
    "best_approach": "Recommended approach for engaging this prospect",
    "content_recommendations": ["Types of content that would resonate"]
}}

Provide only the JSON response, no additional text."""

        try:
            response = await self.claude_client.generate_text(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3,
            )

            if response:
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                insights = json.loads(response_text.strip())
                insights["analysis_complete"] = True
                return insights

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI insights JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")

        return {
            "role_responsibilities": None,
            "buying_authority": None,
            "interests_priorities": [],
            "pain_points": [],
            "conversation_starters": [],
            "best_approach": None,
            "content_recommendations": [],
            "analysis_complete": False,
            "error": "Failed to generate AI insights",
        }


# Singleton instance
_insights_generator: Optional[AIInsightsGenerator] = None


def get_insights_generator() -> AIInsightsGenerator:
    """Get or create AI insights generator instance."""
    global _insights_generator
    if _insights_generator is None:
        _insights_generator = AIInsightsGenerator()
    return _insights_generator
