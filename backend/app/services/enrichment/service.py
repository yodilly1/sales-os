"""Main enrichment service orchestrating all providers."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from app.core.config import settings
from app.models.prospect import (
    ProspectCreate,
    ProspectEnriched,
    EnrichmentRequest,
    EnrichmentResult,
    EnrichmentSource,
    ContactInfo,
    SocialProfiles,
    LinkedInInsights,
)
from app.models.company import CompanyEnriched, CompanyCreate

from .providers.base import EnrichmentProvider
from .providers.clearbit import ClearbitProvider
from .providers.apollo import ApolloProvider
from .providers.hunter import HunterProvider
from .providers.linkedin import LinkedInProvider
from .providers.news import NewsProvider

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for enriching prospect and company data from multiple sources."""

    def __init__(self):
        """Initialize enrichment service with configured providers."""
        self.providers: dict[str, EnrichmentProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize all configured providers."""
        # Clearbit
        if settings.clearbit_api_key:
            self.providers["clearbit"] = ClearbitProvider(
                api_key=settings.clearbit_api_key,
                rate_limit=settings.rate_limit_per_minute,
            )

        # Apollo
        if settings.apollo_api_key:
            self.providers["apollo"] = ApolloProvider(
                api_key=settings.apollo_api_key,
                rate_limit=settings.rate_limit_per_minute,
            )

        # Hunter
        if settings.hunter_api_key:
            self.providers["hunter"] = HunterProvider(
                api_key=settings.hunter_api_key,
                rate_limit=settings.rate_limit_per_minute,
            )

        # LinkedIn
        if settings.linkedin_api_key:
            self.providers["linkedin"] = LinkedInProvider(
                api_key=settings.linkedin_api_key,
                rate_limit=settings.rate_limit_per_minute,
            )

        # News
        if settings.news_api_key:
            self.providers["news"] = NewsProvider(
                api_key=settings.news_api_key,
                rate_limit=settings.rate_limit_per_minute,
            )

        logger.info(f"Initialized {len(self.providers)} enrichment providers: {list(self.providers.keys())}")

    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self.providers.values():
            await provider.close()

    async def enrich_prospect(
        self,
        prospect: ProspectCreate,
        include_company: bool = True,
        include_linkedin: bool = True,
        include_news: bool = True,
        include_contact_verification: bool = True,
    ) -> EnrichmentResult:
        """
        Enrich a prospect with data from all available sources.

        Args:
            prospect: Basic prospect information
            include_company: Whether to enrich company data
            include_linkedin: Whether to include LinkedIn insights
            include_news: Whether to include recent news
            include_contact_verification: Whether to verify email

        Returns:
            EnrichmentResult with enriched prospect and company data
        """
        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []
        sources_used: list[EnrichmentSource] = []

        # Create base enriched prospect
        enriched = ProspectEnriched(
            id=str(uuid4()),
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            full_name=prospect.full_name,
            email=prospect.email,
            title=prospect.title,
            company_name=prospect.company_name,
            company_domain=prospect.company_domain,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Gather enrichment data from all providers concurrently
        tasks = []

        for name, provider in self.providers.items():
            if name == "linkedin" and not include_linkedin:
                continue
            if name == "news" and not include_news:
                continue

            tasks.append(
                self._enrich_from_provider(
                    provider=provider,
                    email=prospect.email,
                    name=prospect.full_name or f"{prospect.first_name or ''} {prospect.last_name or ''}".strip(),
                    company=prospect.company_name,
                    domain=prospect.company_domain,
                )
            )

        # Execute all provider calls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results into enriched prospect
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                continue
            if result:
                data, source = result
                self._merge_prospect_data(enriched, data)
                sources_used.append(source)

        # Verify email if requested
        if include_contact_verification and prospect.email:
            verification = await self._verify_email(prospect.email)
            if verification:
                enriched.contact_info.email_verified = verification.get("verified", False)
                enriched.contact_info.email_verification_date = datetime.utcnow()

        # Enrich company data
        company_data = None
        if include_company and (prospect.company_domain or prospect.company_name):
            company_data = await self.enrich_company(
                CompanyCreate(
                    name=prospect.company_name or "",
                    domain=prospect.company_domain,
                )
            )
            if company_data:
                enriched.company_id = company_data.id

        # Calculate data quality scores
        enriched.enrichment_sources = sources_used
        enriched.enriched_at = datetime.utcnow()
        enriched.data_completeness = self._calculate_completeness(enriched)
        enriched.enrichment_confidence = self._calculate_confidence(enriched, len(sources_used))
        enriched.last_verified = datetime.utcnow()

        duration_ms = int((time.time() - start_time) * 1000)

        return EnrichmentResult(
            success=len(errors) == 0,
            prospect=enriched,
            company=company_data.model_dump() if company_data else None,
            errors=errors,
            warnings=warnings,
            sources_used=sources_used,
            enrichment_duration_ms=duration_ms,
        )

    async def enrich_company(
        self,
        company: CompanyCreate,
        include_news: bool = True,
    ) -> Optional[CompanyEnriched]:
        """
        Enrich company data from all available sources.

        Args:
            company: Basic company information
            include_news: Whether to include recent news

        Returns:
            Enriched company data or None if no data found
        """
        # Create base enriched company
        enriched = CompanyEnriched(
            id=str(uuid4()),
            name=company.name,
            domain=company.domain,
            website=company.website,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Gather company data from providers
        tasks = []
        for name, provider in self.providers.items():
            if name == "news" and not include_news:
                continue
            if name == "hunter":
                # Hunter doesn't provide much company data
                continue

            tasks.append(
                self._enrich_company_from_provider(
                    provider=provider,
                    domain=company.domain,
                    name=company.name,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data_sources = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Company enrichment error: {result}")
                continue
            if result:
                data, source = result
                self._merge_company_data(enriched, data)
                data_sources.append(source.value)

        enriched.data_sources = data_sources
        enriched.enriched_at = datetime.utcnow()
        enriched.data_completeness = self._calculate_company_completeness(enriched)
        enriched.enrichment_confidence = self._calculate_confidence(enriched, len(data_sources))

        return enriched if data_sources else None

    async def _enrich_from_provider(
        self,
        provider: EnrichmentProvider,
        email: Optional[str],
        name: Optional[str],
        company: Optional[str],
        domain: Optional[str],
    ) -> Optional[tuple[dict[str, Any], EnrichmentSource]]:
        """Enrich prospect from a single provider."""
        try:
            data = await provider.enrich_prospect(
                email=email,
                name=name,
                company=company,
                domain=domain,
            )
            if data:
                return data, provider.source
        except Exception as e:
            logger.error(f"Error enriching from {provider.name}: {e}")
        return None

    async def _enrich_company_from_provider(
        self,
        provider: EnrichmentProvider,
        domain: Optional[str],
        name: Optional[str],
    ) -> Optional[tuple[dict[str, Any], EnrichmentSource]]:
        """Enrich company from a single provider."""
        try:
            data = await provider.enrich_company(domain=domain, name=name)
            if data:
                return data, provider.source
        except Exception as e:
            logger.error(f"Error enriching company from {provider.name}: {e}")
        return None

    async def _verify_email(self, email: str) -> Optional[dict[str, Any]]:
        """Verify email using Hunter provider."""
        hunter = self.providers.get("hunter")
        if hunter:
            return await hunter.verify_email(email)
        return None

    def _merge_prospect_data(
        self,
        enriched: ProspectEnriched,
        data: dict[str, Any],
    ) -> None:
        """Merge provider data into enriched prospect, preferring non-null values."""
        # Basic fields
        for field in ["first_name", "last_name", "full_name", "title", "company_name", "company_domain"]:
            if data.get(field) and not getattr(enriched, field):
                setattr(enriched, field, data[field])

        # Professional details
        for field in ["seniority_level", "department", "role_function"]:
            if data.get(field) and not getattr(enriched, field):
                setattr(enriched, field, data[field])

        # Contact info
        if data.get("contact_info"):
            ci = data["contact_info"]
            if ci.get("email") and not enriched.contact_info.email:
                enriched.contact_info.email = ci["email"]
            if ci.get("email_verified"):
                enriched.contact_info.email_verified = ci["email_verified"]
            if ci.get("phone") and not enriched.contact_info.phone:
                enriched.contact_info.phone = ci["phone"]

        # Social profiles
        if data.get("social_profiles"):
            sp = data["social_profiles"]
            for field in ["linkedin_url", "linkedin_username", "twitter_url", "github_url"]:
                if sp.get(field) and not getattr(enriched.social_profiles, field, None):
                    setattr(enriched.social_profiles, field, sp[field])

        # LinkedIn insights
        if data.get("linkedin_insights"):
            li = data["linkedin_insights"]
            if not enriched.linkedin_insights:
                enriched.linkedin_insights = LinkedInInsights()
            for field in ["headline", "summary", "location", "industry"]:
                if li.get(field) and not getattr(enriched.linkedin_insights, field):
                    setattr(enriched.linkedin_insights, field, li[field])
            if li.get("skills"):
                enriched.linkedin_insights.skills.extend(li["skills"])

        # News mentions
        if data.get("recent_news_mentions"):
            enriched.recent_news_mentions.extend(data["recent_news_mentions"])

    def _merge_company_data(
        self,
        enriched: CompanyEnriched,
        data: dict[str, Any],
    ) -> None:
        """Merge provider data into enriched company."""
        # Basic fields
        simple_fields = [
            "legal_name", "description", "logo_url", "founded_year",
            "industry", "industry_group", "sub_industry", "sector",
            "company_size", "employee_count", "employee_range",
            "annual_revenue", "revenue_range", "company_type",
        ]
        for field in simple_fields:
            if data.get(field) and not getattr(enriched, field, None):
                setattr(enriched, field, data[field])

        # Lists
        for list_field in ["sic_codes", "naics_codes", "tags", "competitors"]:
            if data.get(list_field):
                existing = getattr(enriched, list_field, [])
                existing.extend(data[list_field])
                setattr(enriched, list_field, list(set(existing)))

        # Headquarters
        if data.get("headquarters") and not enriched.headquarters:
            from app.models.company import CompanyLocation
            enriched.headquarters = CompanyLocation(**data["headquarters"])

        # Funding info
        if data.get("funding_info"):
            fi = data["funding_info"]
            if fi.get("total_raised") and not enriched.funding_info.total_raised:
                enriched.funding_info.total_raised = fi["total_raised"]
            if fi.get("last_funding_stage"):
                enriched.funding_info.last_funding_stage = fi["last_funding_stage"]
            if fi.get("is_funded"):
                enriched.funding_info.is_funded = fi["is_funded"]

        # Tech stack
        if data.get("tech_stack"):
            ts = data["tech_stack"]
            if ts.get("technologies"):
                enriched.tech_stack.technologies.extend(ts["technologies"])
                enriched.tech_stack.technologies = list(set(enriched.tech_stack.technologies))

        # Social profiles
        if data.get("social_profiles"):
            sp = data["social_profiles"]
            for field in ["linkedin_url", "twitter_url", "facebook_url", "crunchbase_url"]:
                if sp.get(field) and not getattr(enriched.social_profiles, field, None):
                    setattr(enriched.social_profiles, field, sp[field])

        # News
        if data.get("recent_news"):
            enriched.recent_news.extend(data["recent_news"])

    def _calculate_completeness(self, prospect: ProspectEnriched) -> float:
        """Calculate data completeness score for prospect."""
        fields_to_check = [
            prospect.first_name,
            prospect.last_name,
            prospect.email,
            prospect.title,
            prospect.company_name,
            prospect.contact_info.email_verified,
            prospect.social_profiles.linkedin_url,
            prospect.seniority_level,
        ]
        filled = sum(1 for f in fields_to_check if f)
        return round(filled / len(fields_to_check), 2)

    def _calculate_company_completeness(self, company: CompanyEnriched) -> float:
        """Calculate data completeness score for company."""
        fields_to_check = [
            company.name,
            company.domain,
            company.description,
            company.industry,
            company.employee_count,
            company.headquarters,
            company.funding_info.total_raised,
            bool(company.tech_stack.technologies),
        ]
        filled = sum(1 for f in fields_to_check if f)
        return round(filled / len(fields_to_check), 2)

    def _calculate_confidence(self, obj: Any, source_count: int) -> float:
        """Calculate confidence score based on data sources."""
        # More sources = higher confidence
        base_confidence = min(source_count * 0.25, 0.75)
        # Add bonus for verified data
        if hasattr(obj, "contact_info") and obj.contact_info.email_verified:
            base_confidence += 0.15
        return round(min(base_confidence + 0.1, 1.0), 2)
