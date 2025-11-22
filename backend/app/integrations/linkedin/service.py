"""
LinkedIn Service

Business logic layer for LinkedIn integration.
Handles profile enrichment, company data extraction, connection tracking,
activity monitoring, and outreach tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .client import LinkedInClient
from .exceptions import (
    LinkedInError,
    LinkedInNotFoundError,
    LinkedInValidationError,
)
from .parser import LinkedInURLParser, LinkedInResourceType
from .rate_limiter import get_rate_limiter

# Import models
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.linkedin import (
    LinkedInProfile,
    LinkedInProfileSummary,
    LinkedInCompany,
    OutreachActivity,
    OutreachCampaign,
    LinkedInActivity,
    ConnectionRecord,
    ConnectionStatus,
    OutreachType,
    OutreachStatus,
    ActivityType,
    ProfileEnrichmentRequest,
    CompanyEnrichmentRequest,
    BulkEnrichmentRequest,
    EnrichmentResponse,
    BulkEnrichmentResponse,
    ProfileMatchRequest,
    ProfileMatchResponse,
)

logger = logging.getLogger(__name__)


class LinkedInService:
    """
    LinkedIn Service

    Provides high-level operations for:
    - Profile data enrichment
    - Company page data extraction
    - Connection status tracking
    - Activity monitoring (posts, engagement)
    - Outreach tracking (InMail, connection requests)
    - Sales Navigator integration
    - Profile-to-prospect matching
    """

    def __init__(
        self,
        client: Optional[LinkedInClient] = None,
        # In-memory storage for demo - replace with database in production
        enable_activity_monitoring: bool = True,
    ):
        self.client = client or LinkedInClient()
        self.enable_activity_monitoring = enable_activity_monitoring

        # In-memory storage (replace with database in production)
        self._outreach_activities: Dict[str, OutreachActivity] = {}
        self._campaigns: Dict[str, OutreachCampaign] = {}
        self._connection_records: Dict[str, List[ConnectionRecord]] = {}
        self._activities: Dict[str, List[LinkedInActivity]] = {}
        self._profile_cache: Dict[str, LinkedInProfile] = {}
        self._company_cache: Dict[str, LinkedInCompany] = {}

    async def close(self):
        """Close the service and cleanup resources"""
        await self.client.close()

    # ==================== Profile Enrichment ====================

    async def enrich_profile(
        self,
        request: ProfileEnrichmentRequest,
    ) -> EnrichmentResponse:
        """
        Enrich a LinkedIn profile with full data.

        Args:
            request: Profile enrichment request

        Returns:
            EnrichmentResponse with profile data or error
        """
        try:
            # Validate URL
            parsed = LinkedInURLParser.parse(request.linkedin_url)
            if not parsed.is_valid:
                return EnrichmentResponse(
                    success=False,
                    error_message=parsed.error_message or "Invalid LinkedIn URL",
                )

            if parsed.resource_type != LinkedInResourceType.PROFILE:
                return EnrichmentResponse(
                    success=False,
                    error_message=f"URL is not a profile URL (detected: {parsed.resource_type})",
                )

            # Fetch profile data
            profile_data = await self.client.get_profile(
                linkedin_url=request.linkedin_url,
                force_refresh=request.force_refresh,
                include_experiences=request.include_experiences,
                include_education=request.include_education,
                include_skills=request.include_skills,
            )

            # Convert to Pydantic model
            profile = LinkedInProfile(**profile_data)

            # Cache the profile
            self._profile_cache[parsed.identifier] = profile

            return EnrichmentResponse(
                success=True,
                profile=profile,
                cached=profile_data.get("_cached", False),
                enrichment_source=profile_data.get("enrichment_source"),
            )

        except LinkedInNotFoundError as e:
            return EnrichmentResponse(
                success=False,
                error_message=f"Profile not found: {str(e)}",
            )
        except LinkedInError as e:
            logger.error(f"LinkedIn error enriching profile: {e}")
            return EnrichmentResponse(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception(f"Unexpected error enriching profile: {e}")
            return EnrichmentResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
            )

    async def bulk_enrich_profiles(
        self,
        request: BulkEnrichmentRequest,
    ) -> BulkEnrichmentResponse:
        """
        Enrich multiple LinkedIn profiles.

        Processes profiles with rate limiting and error handling.
        """
        results: List[EnrichmentResponse] = []
        successful = 0
        failed = 0

        # Process in batches to respect rate limits
        batch_size = 5
        for i in range(0, len(request.linkedin_urls), batch_size):
            batch = request.linkedin_urls[i : i + batch_size]

            # Process batch concurrently
            tasks = [
                self.enrich_profile(
                    ProfileEnrichmentRequest(
                        linkedin_url=url,
                        force_refresh=request.force_refresh,
                    )
                )
                for url in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(
                        EnrichmentResponse(
                            success=False,
                            error_message=str(result),
                        )
                    )
                    failed += 1
                elif result.success:
                    results.append(result)
                    successful += 1
                else:
                    results.append(result)
                    failed += 1

            # Small delay between batches
            if i + batch_size < len(request.linkedin_urls):
                await asyncio.sleep(1)

        return BulkEnrichmentResponse(
            total_requested=len(request.linkedin_urls),
            successful=successful,
            failed=failed,
            results=results,
        )

    # ==================== Company Enrichment ====================

    async def enrich_company(
        self,
        request: CompanyEnrichmentRequest,
    ) -> EnrichmentResponse:
        """
        Enrich a LinkedIn company page with full data.
        """
        try:
            # Validate URL
            parsed = LinkedInURLParser.parse(request.linkedin_url)
            if not parsed.is_valid:
                return EnrichmentResponse(
                    success=False,
                    error_message=parsed.error_message or "Invalid LinkedIn URL",
                )

            if parsed.resource_type not in (
                LinkedInResourceType.COMPANY,
                LinkedInResourceType.SCHOOL,
            ):
                return EnrichmentResponse(
                    success=False,
                    error_message=f"URL is not a company URL (detected: {parsed.resource_type})",
                )

            # Fetch company data
            company_data = await self.client.get_company(
                linkedin_url=request.linkedin_url,
                force_refresh=request.force_refresh,
                include_key_employees=request.include_key_employees,
            )

            # Convert to Pydantic model
            company = LinkedInCompany(**company_data)

            # Cache the company
            self._company_cache[parsed.identifier] = company

            return EnrichmentResponse(
                success=True,
                company=company,
                cached=company_data.get("_cached", False),
                enrichment_source=company_data.get("enrichment_source"),
            )

        except LinkedInNotFoundError as e:
            return EnrichmentResponse(
                success=False,
                error_message=f"Company not found: {str(e)}",
            )
        except LinkedInError as e:
            logger.error(f"LinkedIn error enriching company: {e}")
            return EnrichmentResponse(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception(f"Unexpected error enriching company: {e}")
            return EnrichmentResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
            )

    # ==================== Connection Tracking ====================

    async def get_connection_status(
        self,
        prospect_linkedin_url: str,
    ) -> ConnectionStatus:
        """
        Get the connection status with a prospect.

        Note: This requires either:
        - Cached data from previous enrichment
        - Manual update via update_connection_status
        - Sales Navigator API access
        """
        parsed = LinkedInURLParser.parse(prospect_linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            raise LinkedInValidationError(f"Invalid LinkedIn URL: {prospect_linkedin_url}")

        # Check cached profile
        profile = self._profile_cache.get(parsed.identifier)
        if profile:
            return profile.connection_status

        # Check connection records
        records = self._connection_records.get(parsed.identifier, [])
        if records:
            return records[-1].new_status

        return ConnectionStatus.NOT_CONNECTED

    async def update_connection_status(
        self,
        prospect_linkedin_url: str,
        new_status: ConnectionStatus,
        note: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ConnectionRecord:
        """
        Update connection status with a prospect.

        Creates a record of the status change for tracking.
        """
        parsed = LinkedInURLParser.parse(prospect_linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            raise LinkedInValidationError(f"Invalid LinkedIn URL: {prospect_linkedin_url}")

        # Get previous status
        previous_status = await self.get_connection_status(prospect_linkedin_url)

        # Create record
        record = ConnectionRecord(
            id=str(uuid4()),
            prospect_linkedin_url=parsed.normalized_url or prospect_linkedin_url,
            previous_status=previous_status,
            new_status=new_status,
            connection_note=note,
            user_id=user_id,
        )

        # Store record
        if parsed.identifier not in self._connection_records:
            self._connection_records[parsed.identifier] = []
        self._connection_records[parsed.identifier].append(record)

        # Update cached profile if exists
        if parsed.identifier in self._profile_cache:
            self._profile_cache[parsed.identifier].connection_status = new_status

        logger.info(
            f"Connection status updated: {parsed.identifier} "
            f"{previous_status} -> {new_status}"
        )

        return record

    async def get_connection_history(
        self,
        prospect_linkedin_url: str,
    ) -> List[ConnectionRecord]:
        """Get connection status history for a prospect"""
        parsed = LinkedInURLParser.parse(prospect_linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            return []

        return self._connection_records.get(parsed.identifier, [])

    # ==================== Outreach Tracking ====================

    async def track_outreach(
        self,
        prospect_linkedin_url: str,
        outreach_type: OutreachType,
        message_content: Optional[str] = None,
        subject: Optional[str] = None,
        campaign_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_sales_navigator: bool = False,
    ) -> OutreachActivity:
        """
        Track a new outreach activity.

        Args:
            prospect_linkedin_url: LinkedIn URL of the prospect
            outreach_type: Type of outreach (InMail, connection request, etc.)
            message_content: Content of the message
            subject: Subject line (for InMails)
            campaign_id: Optional campaign association
            user_id: User who performed the outreach
            is_sales_navigator: Whether outreach was via Sales Navigator

        Returns:
            Created OutreachActivity
        """
        parsed = LinkedInURLParser.parse(prospect_linkedin_url)
        if not parsed.is_valid:
            raise LinkedInValidationError(f"Invalid LinkedIn URL: {prospect_linkedin_url}")

        activity = OutreachActivity(
            id=str(uuid4()),
            prospect_linkedin_url=parsed.normalized_url or prospect_linkedin_url,
            outreach_type=outreach_type,
            status=OutreachStatus.SENT,
            message_content=message_content,
            subject=subject,
            campaign_id=campaign_id,
            user_id=user_id,
            is_sales_navigator=is_sales_navigator,
            sent_at=datetime.now(),
        )

        # Store activity
        self._outreach_activities[activity.id] = activity

        # Update campaign stats if applicable
        if campaign_id and campaign_id in self._campaigns:
            self._campaigns[campaign_id].sent_count += 1
            self._campaigns[campaign_id].updated_at = datetime.now()

        logger.info(
            f"Outreach tracked: {outreach_type.value} to {parsed.identifier}"
        )

        return activity

    async def update_outreach_status(
        self,
        activity_id: str,
        new_status: OutreachStatus,
        response_content: Optional[str] = None,
    ) -> Optional[OutreachActivity]:
        """
        Update the status of an outreach activity.

        Args:
            activity_id: ID of the outreach activity
            new_status: New status to set
            response_content: Response content if replied

        Returns:
            Updated OutreachActivity or None if not found
        """
        activity = self._outreach_activities.get(activity_id)
        if not activity:
            return None

        activity.status = new_status

        # Update timestamps based on status
        now = datetime.now()
        if new_status == OutreachStatus.DELIVERED:
            activity.delivered_at = now
        elif new_status == OutreachStatus.READ:
            activity.read_at = now
        elif new_status == OutreachStatus.REPLIED:
            activity.replied_at = now
            activity.response_content = response_content

            # Update campaign stats
            if activity.campaign_id and activity.campaign_id in self._campaigns:
                self._campaigns[activity.campaign_id].replied_count += 1
        elif new_status == OutreachStatus.ACCEPTED:
            # For connection requests
            if activity.campaign_id and activity.campaign_id in self._campaigns:
                self._campaigns[activity.campaign_id].accepted_count += 1

        return activity

    async def get_outreach_history(
        self,
        prospect_linkedin_url: Optional[str] = None,
        campaign_id: Optional[str] = None,
        user_id: Optional[str] = None,
        outreach_type: Optional[OutreachType] = None,
        limit: int = 100,
    ) -> List[OutreachActivity]:
        """
        Get outreach history with optional filters.

        Args:
            prospect_linkedin_url: Filter by prospect
            campaign_id: Filter by campaign
            user_id: Filter by user
            outreach_type: Filter by type
            limit: Max results

        Returns:
            List of matching outreach activities
        """
        activities = list(self._outreach_activities.values())

        # Apply filters
        if prospect_linkedin_url:
            normalized = LinkedInURLParser.normalize_profile_url(prospect_linkedin_url)
            activities = [
                a for a in activities
                if a.prospect_linkedin_url == normalized
            ]

        if campaign_id:
            activities = [a for a in activities if a.campaign_id == campaign_id]

        if user_id:
            activities = [a for a in activities if a.user_id == user_id]

        if outreach_type:
            activities = [a for a in activities if a.outreach_type == outreach_type]

        # Sort by created_at descending
        activities.sort(key=lambda a: a.created_at, reverse=True)

        return activities[:limit]

    # ==================== Campaign Management ====================

    async def create_campaign(
        self,
        name: str,
        description: Optional[str] = None,
        target_profiles: Optional[List[str]] = None,
        message_templates: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> OutreachCampaign:
        """
        Create a new outreach campaign.
        """
        campaign = OutreachCampaign(
            id=str(uuid4()),
            name=name,
            description=description,
            target_profiles=target_profiles or [],
            message_templates=message_templates or [],
            total_prospects=len(target_profiles) if target_profiles else 0,
            user_id=user_id,
        )

        self._campaigns[campaign.id] = campaign

        logger.info(f"Campaign created: {campaign.name} (ID: {campaign.id})")

        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[OutreachCampaign]:
        """Get a campaign by ID"""
        return self._campaigns.get(campaign_id)

    async def list_campaigns(
        self,
        user_id: Optional[str] = None,
        active_only: bool = False,
    ) -> List[OutreachCampaign]:
        """List campaigns with optional filters"""
        campaigns = list(self._campaigns.values())

        if user_id:
            campaigns = [c for c in campaigns if c.user_id == user_id]

        if active_only:
            campaigns = [c for c in campaigns if c.is_active]

        campaigns.sort(key=lambda c: c.created_at, reverse=True)

        return campaigns

    async def update_campaign(
        self,
        campaign_id: str,
        **updates,
    ) -> Optional[OutreachCampaign]:
        """Update campaign fields"""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return None

        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        campaign.updated_at = datetime.now()

        return campaign

    # ==================== Activity Monitoring ====================

    async def record_activity(
        self,
        profile_linkedin_url: str,
        activity_type: ActivityType,
        content_text: Optional[str] = None,
        activity_url: Optional[str] = None,
        activity_date: Optional[datetime] = None,
        **metadata,
    ) -> LinkedInActivity:
        """
        Record a LinkedIn activity from a prospect.

        This can be used to track:
        - Posts and articles
        - Job changes and promotions
        - Work anniversaries
        - Engagement on content
        """
        parsed = LinkedInURLParser.parse(profile_linkedin_url)
        if not parsed.is_valid:
            raise LinkedInValidationError(f"Invalid LinkedIn URL: {profile_linkedin_url}")

        activity = LinkedInActivity(
            id=str(uuid4()),
            profile_linkedin_url=parsed.normalized_url or profile_linkedin_url,
            activity_type=activity_type,
            content_text=content_text,
            activity_url=activity_url,
            activity_date=activity_date or datetime.now(),
            likes_count=metadata.get("likes_count", 0),
            comments_count=metadata.get("comments_count", 0),
            shares_count=metadata.get("shares_count", 0),
            old_title=metadata.get("old_title"),
            old_company=metadata.get("old_company"),
            new_title=metadata.get("new_title"),
            new_company=metadata.get("new_company"),
        )

        # Store activity
        if parsed.identifier not in self._activities:
            self._activities[parsed.identifier] = []
        self._activities[parsed.identifier].append(activity)

        logger.info(
            f"Activity recorded: {activity_type.value} from {parsed.identifier}"
        )

        return activity

    async def get_prospect_activities(
        self,
        profile_linkedin_url: str,
        activity_types: Optional[List[ActivityType]] = None,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[LinkedInActivity]:
        """
        Get recorded activities for a prospect.

        Args:
            profile_linkedin_url: LinkedIn URL of the prospect
            activity_types: Filter by activity types
            since: Filter activities after this date
            limit: Max results

        Returns:
            List of activities
        """
        parsed = LinkedInURLParser.parse(profile_linkedin_url)
        if not parsed.is_valid or not parsed.identifier:
            return []

        activities = self._activities.get(parsed.identifier, [])

        # Apply filters
        if activity_types:
            activities = [a for a in activities if a.activity_type in activity_types]

        if since:
            activities = [a for a in activities if a.activity_date >= since]

        # Sort by date descending
        activities.sort(key=lambda a: a.activity_date, reverse=True)

        return activities[:limit]

    async def get_job_changes(
        self,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[LinkedInActivity]:
        """
        Get job change activities across all tracked prospects.

        Useful for identifying prospects who recently changed jobs
        (a good time to reach out).
        """
        job_change_types = {ActivityType.JOB_CHANGE, ActivityType.PROMOTION}

        all_activities = []
        for activities in self._activities.values():
            for activity in activities:
                if activity.activity_type in job_change_types:
                    if since is None or activity.activity_date >= since:
                        all_activities.append(activity)

        all_activities.sort(key=lambda a: a.activity_date, reverse=True)

        return all_activities[:limit]

    # ==================== Profile-to-Prospect Matching ====================

    async def match_profile_to_prospect(
        self,
        request: ProfileMatchRequest,
    ) -> ProfileMatchResponse:
        """
        Attempt to match a LinkedIn profile to an existing prospect.

        Uses various matching strategies:
        - Exact email match
        - Name + Company match
        - LinkedIn URL match

        Returns:
            ProfileMatchResponse with match details
        """
        parsed = LinkedInURLParser.parse(request.linkedin_url)
        if not parsed.is_valid:
            return ProfileMatchResponse(
                matched=False,
                confidence_score=0.0,
                match_reasons=["Invalid LinkedIn URL"],
            )

        # Get profile data if not already cached
        profile_response = await self.enrich_profile(
            ProfileEnrichmentRequest(
                linkedin_url=request.linkedin_url,
                force_refresh=False,
            )
        )

        if not profile_response.success or not profile_response.profile:
            return ProfileMatchResponse(
                matched=False,
                confidence_score=0.0,
                match_reasons=["Could not fetch profile data"],
            )

        profile = profile_response.profile
        match_reasons: List[str] = []
        confidence_score = 0.0

        # Email match (highest confidence)
        if request.email and profile.email:
            if request.email.lower() == profile.email.lower():
                match_reasons.append("Email match")
                confidence_score += 0.5

        # Name match
        if request.first_name and request.last_name:
            if (
                request.first_name.lower() == profile.first_name.lower()
                and request.last_name.lower() == profile.last_name.lower()
            ):
                match_reasons.append("Name match")
                confidence_score += 0.3

        # Company match
        if request.company and profile.current_company:
            if request.company.lower() in profile.current_company.lower():
                match_reasons.append("Company match")
                confidence_score += 0.2

        # Determine if matched
        matched = confidence_score >= 0.3  # Threshold for considering a match

        return ProfileMatchResponse(
            matched=matched,
            confidence_score=min(1.0, confidence_score),
            prospect_id=request.prospect_id if matched else None,
            profile=LinkedInProfileSummary(
                linkedin_url=profile.linkedin_url,
                first_name=profile.first_name,
                last_name=profile.last_name,
                headline=profile.headline,
                current_company=profile.current_company,
                location=profile.location,
                profile_picture_url=profile.profile_picture_url,
                connection_status=profile.connection_status,
            ),
            match_reasons=match_reasons,
        )

    # ==================== Sales Navigator ====================

    async def get_sales_navigator_lead(
        self,
        sales_nav_url: str,
    ) -> EnrichmentResponse:
        """
        Fetch a lead from Sales Navigator.

        Note: Requires Sales Navigator API access or converts to regular profile.
        """
        parsed = LinkedInURLParser.parse(sales_nav_url)

        if parsed.resource_type not in (
            LinkedInResourceType.SALES_NAVIGATOR_PROFILE,
            LinkedInResourceType.SALES_NAVIGATOR_LEAD,
        ):
            return EnrichmentResponse(
                success=False,
                error_message="URL is not a Sales Navigator profile URL",
            )

        # Try to convert to regular LinkedIn URL and enrich
        # Note: This is a simplified implementation
        # Full Sales Navigator integration would require their API
        return EnrichmentResponse(
            success=False,
            error_message="Sales Navigator API not fully implemented. Use regular LinkedIn URLs.",
        )

    # ==================== Analytics ====================

    async def get_outreach_analytics(
        self,
        campaign_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get outreach analytics and metrics.

        Returns:
            Dictionary with analytics data
        """
        activities = await self.get_outreach_history(
            campaign_id=campaign_id,
            user_id=user_id,
            limit=10000,
        )

        # Filter by date
        cutoff = datetime.now() - timedelta(days=days)
        activities = [a for a in activities if a.created_at >= cutoff]

        if not activities:
            return {
                "total_outreach": 0,
                "by_type": {},
                "by_status": {},
                "reply_rate": 0.0,
                "acceptance_rate": 0.0,
            }

        # Calculate metrics
        by_type = {}
        by_status = {}

        for activity in activities:
            # Count by type
            type_key = activity.outreach_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by status
            status_key = activity.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

        total = len(activities)
        replied = by_status.get(OutreachStatus.REPLIED.value, 0)
        accepted = by_status.get(OutreachStatus.ACCEPTED.value, 0)

        return {
            "total_outreach": total,
            "by_type": by_type,
            "by_status": by_status,
            "reply_rate": round((replied / total) * 100, 2) if total > 0 else 0.0,
            "acceptance_rate": round((accepted / total) * 100, 2) if total > 0 else 0.0,
            "period_days": days,
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Create singleton service instance
_service_instance: Optional[LinkedInService] = None


def get_linkedin_service() -> LinkedInService:
    """Get or create the LinkedIn service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = LinkedInService()
    return _service_instance
