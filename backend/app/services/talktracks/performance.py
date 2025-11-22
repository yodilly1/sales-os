"""
Talk Track Performance Tracking

Tracks usage and performance metrics for talk tracks to enable
A/B testing and continuous improvement of scripts.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from backend.app.models.talktrack import (
    ScriptUsageEvent,
    ScriptPerformanceMetrics,
    TalkTrackLibraryItem,
    TalkTrackLibrary,
    ScriptType,
    PersonaType,
    Industry,
)

logger = logging.getLogger(__name__)


class TalkTrackPerformanceTracker:
    """
    Tracks and analyzes talk track performance.

    Features:
    - Usage event recording
    - Performance metric calculation
    - A/B test analysis
    - Trend identification
    - Best performer recommendations
    """

    def __init__(self, db_session=None):
        """
        Initialize the performance tracker.

        Args:
            db_session: Database session for persistence (optional)
        """
        self.db_session = db_session
        # In-memory storage for when DB is not available
        self._usage_events: List[ScriptUsageEvent] = []
        self._talk_tracks: Dict[UUID, Dict] = {}

    async def record_usage(self, event: ScriptUsageEvent) -> ScriptUsageEvent:
        """
        Record a talk track usage event.

        Args:
            event: The usage event to record

        Returns:
            The recorded event with ID
        """
        logger.info(f"Recording usage event for talk track {event.talktrack_id}")

        if self.db_session:
            # Persist to database
            await self._persist_usage_event(event)
        else:
            # Store in memory
            self._usage_events.append(event)

        return event

    async def get_performance_metrics(
        self,
        talktrack_id: UUID,
        period_days: int = 30,
    ) -> ScriptPerformanceMetrics:
        """
        Calculate performance metrics for a talk track.

        Args:
            talktrack_id: ID of the talk track
            period_days: Number of days to analyze

        Returns:
            Performance metrics for the talk track
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)

        # Get usage events for the period
        events = await self._get_usage_events(talktrack_id, period_start, period_end)

        if not events:
            return ScriptPerformanceMetrics(
                talktrack_id=talktrack_id,
                period_start=period_start,
                period_end=period_end,
            )

        # Calculate metrics
        total_uses = len(events)
        unique_users = len(set(e.user_id for e in events))

        meetings_scheduled = sum(1 for e in events if e.next_step_scheduled)
        meetings_scheduled_rate = meetings_scheduled / total_uses if total_uses > 0 else 0.0

        deals_advanced = sum(1 for e in events if e.deal_advanced)
        deal_advancement_rate = deals_advanced / total_uses if total_uses > 0 else 0.0

        durations = [e.call_duration_minutes for e in events if e.call_duration_minutes]
        average_duration = sum(durations) / len(durations) if durations else None

        ratings = [e.user_rating for e in events if e.user_rating]
        average_rating = sum(ratings) / len(ratings) if ratings else None

        # A/B variant analysis
        variant_performance = await self._analyze_variants(events)

        return ScriptPerformanceMetrics(
            talktrack_id=talktrack_id,
            total_uses=total_uses,
            unique_users=unique_users,
            meetings_scheduled_rate=meetings_scheduled_rate,
            deal_advancement_rate=deal_advancement_rate,
            average_call_duration=average_duration,
            variant_performance=variant_performance,
            average_rating=average_rating,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_best_performers(
        self,
        script_type: Optional[ScriptType] = None,
        persona: Optional[PersonaType] = None,
        industry: Optional[Industry] = None,
        limit: int = 10,
    ) -> List[TalkTrackLibraryItem]:
        """
        Get the best performing talk tracks based on metrics.

        Args:
            script_type: Filter by script type
            persona: Filter by persona
            industry: Filter by industry
            limit: Maximum results to return

        Returns:
            List of top performing talk tracks
        """
        # Get all talk tracks matching filters
        candidates = await self._get_filtered_talktracks(script_type, persona, industry)

        # Calculate performance scores
        scored_tracks = []
        for track_id, track_data in candidates.items():
            metrics = await self.get_performance_metrics(track_id)

            # Composite score: weighted combination of metrics
            score = (
                metrics.deal_advancement_rate * 0.4 +
                metrics.meetings_scheduled_rate * 0.3 +
                (metrics.average_rating / 5 if metrics.average_rating else 0) * 0.2 +
                min(metrics.total_uses / 100, 1) * 0.1  # Usage volume capped at 100
            )

            scored_tracks.append((track_data, metrics, score))

        # Sort by score and return top performers
        scored_tracks.sort(key=lambda x: x[2], reverse=True)

        return [
            TalkTrackLibraryItem(
                id=track["id"],
                title=track["title"],
                script_type=track["script_type"],
                persona=track["persona"],
                industry=track["industry"],
                version=track.get("version", "1.0"),
                total_uses=metrics.total_uses,
                average_rating=metrics.average_rating,
                created_at=track.get("created_at", datetime.utcnow()),
                updated_at=track.get("updated_at", datetime.utcnow()),
            )
            for track, metrics, _ in scored_tracks[:limit]
        ]

    async def get_ab_test_results(
        self,
        talktrack_id: UUID,
        period_days: int = 30,
    ) -> Dict[str, Dict]:
        """
        Get A/B test results for a talk track's variants.

        Args:
            talktrack_id: ID of the talk track
            period_days: Period to analyze

        Returns:
            Performance comparison of variants
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)

        events = await self._get_usage_events(talktrack_id, period_start, period_end)
        return await self._analyze_variants(events)

    async def get_trend_analysis(
        self,
        talktrack_id: UUID,
        period_days: int = 90,
        interval_days: int = 7,
    ) -> List[Dict]:
        """
        Get performance trends over time.

        Args:
            talktrack_id: ID of the talk track
            period_days: Total period to analyze
            interval_days: Interval for data points

        Returns:
            List of metrics at each interval
        """
        trends = []
        period_end = datetime.utcnow()

        for i in range(0, period_days, interval_days):
            interval_end = period_end - timedelta(days=i)
            interval_start = interval_end - timedelta(days=interval_days)

            events = await self._get_usage_events(talktrack_id, interval_start, interval_end)

            if events:
                meetings_scheduled = sum(1 for e in events if e.next_step_scheduled)
                deals_advanced = sum(1 for e in events if e.deal_advanced)

                trends.append({
                    "period_start": interval_start.isoformat(),
                    "period_end": interval_end.isoformat(),
                    "total_uses": len(events),
                    "meetings_scheduled_rate": meetings_scheduled / len(events),
                    "deal_advancement_rate": deals_advanced / len(events),
                })

        # Reverse to show oldest first
        trends.reverse()
        return trends

    async def get_library(
        self,
        script_type: Optional[ScriptType] = None,
        persona: Optional[PersonaType] = None,
        industry: Optional[Industry] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TalkTrackLibrary:
        """
        Get paginated library of talk tracks.

        Args:
            script_type: Filter by script type
            persona: Filter by persona
            industry: Filter by industry
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated library response
        """
        candidates = await self._get_filtered_talktracks(script_type, persona, industry)

        # Build library items with metrics
        items = []
        for track_id, track_data in candidates.items():
            metrics = await self.get_performance_metrics(track_id)
            items.append(
                TalkTrackLibraryItem(
                    id=track_data["id"],
                    title=track_data["title"],
                    script_type=track_data["script_type"],
                    persona=track_data["persona"],
                    industry=track_data["industry"],
                    version=track_data.get("version", "1.0"),
                    total_uses=metrics.total_uses,
                    average_rating=metrics.average_rating,
                    created_at=track_data.get("created_at", datetime.utcnow()),
                    updated_at=track_data.get("updated_at", datetime.utcnow()),
                )
            )

        # Sort by updated_at descending
        items.sort(key=lambda x: x.updated_at, reverse=True)

        # Paginate
        total = len(items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]

        return TalkTrackLibrary(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def register_talktrack(
        self,
        talktrack_id: UUID,
        title: str,
        script_type: ScriptType,
        persona: PersonaType,
        industry: Industry,
        version: str = "1.0",
    ) -> None:
        """
        Register a talk track for tracking.

        Args:
            talktrack_id: Unique ID of the talk track
            title: Talk track title
            script_type: Type of script
            persona: Target persona
            industry: Target industry
            version: Version string
        """
        self._talk_tracks[talktrack_id] = {
            "id": talktrack_id,
            "title": title,
            "script_type": script_type,
            "persona": persona,
            "industry": industry,
            "version": version,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _persist_usage_event(self, event: ScriptUsageEvent) -> None:
        """Persist usage event to database."""
        # Implementation depends on ORM choice
        pass

    async def _get_usage_events(
        self,
        talktrack_id: UUID,
        start: datetime,
        end: datetime,
    ) -> List[ScriptUsageEvent]:
        """Get usage events for a talk track within a time range."""
        if self.db_session:
            # Query from database
            pass

        # In-memory filter
        return [
            e for e in self._usage_events
            if e.talktrack_id == talktrack_id
            and start <= e.used_at <= end
        ]

    async def _get_filtered_talktracks(
        self,
        script_type: Optional[ScriptType] = None,
        persona: Optional[PersonaType] = None,
        industry: Optional[Industry] = None,
    ) -> Dict[UUID, Dict]:
        """Get talk tracks matching filters."""
        result = {}

        for track_id, track_data in self._talk_tracks.items():
            if script_type and track_data.get("script_type") != script_type:
                continue
            if persona and track_data.get("persona") != persona:
                continue
            if industry and track_data.get("industry") != industry:
                continue
            result[track_id] = track_data

        return result

    async def _analyze_variants(
        self,
        events: List[ScriptUsageEvent],
    ) -> Optional[Dict[str, Dict]]:
        """Analyze A/B variant performance."""
        # Group events by variant
        by_variant = defaultdict(list)
        for e in events:
            variant = e.variant_used or "control"
            by_variant[variant].append(e)

        if len(by_variant) <= 1:
            return None

        result = {}
        for variant, variant_events in by_variant.items():
            total = len(variant_events)
            meetings = sum(1 for e in variant_events if e.next_step_scheduled)
            deals = sum(1 for e in variant_events if e.deal_advanced)
            ratings = [e.user_rating for e in variant_events if e.user_rating]

            result[variant] = {
                "total_uses": total,
                "meetings_scheduled_rate": meetings / total if total > 0 else 0,
                "deal_advancement_rate": deals / total if total > 0 else 0,
                "average_rating": sum(ratings) / len(ratings) if ratings else None,
            }

        # Determine winner
        if len(result) >= 2:
            sorted_variants = sorted(
                result.items(),
                key=lambda x: x[1]["deal_advancement_rate"],
                reverse=True
            )
            winner = sorted_variants[0][0]
            for variant in result:
                result[variant]["is_winner"] = variant == winner

        return result


class TalkTrackRecommender:
    """
    Recommends talk tracks based on context and performance.
    """

    def __init__(self, tracker: TalkTrackPerformanceTracker):
        self.tracker = tracker

    async def recommend(
        self,
        script_type: ScriptType,
        persona: PersonaType,
        industry: Industry,
        deal_stage: Optional[str] = None,
    ) -> List[TalkTrackLibraryItem]:
        """
        Recommend best talk tracks for given context.

        Args:
            script_type: Type of script needed
            persona: Target buyer persona
            industry: Target industry
            deal_stage: Current deal stage

        Returns:
            List of recommended talk tracks, best first
        """
        # Get best performers matching exact criteria
        exact_matches = await self.tracker.get_best_performers(
            script_type=script_type,
            persona=persona,
            industry=industry,
            limit=3,
        )

        if len(exact_matches) >= 3:
            return exact_matches

        # Fall back to script type + persona
        persona_matches = await self.tracker.get_best_performers(
            script_type=script_type,
            persona=persona,
            limit=3,
        )

        # Combine and deduplicate
        seen_ids = {item.id for item in exact_matches}
        for item in persona_matches:
            if item.id not in seen_ids and len(exact_matches) < 5:
                exact_matches.append(item)
                seen_ids.add(item.id)

        return exact_matches
