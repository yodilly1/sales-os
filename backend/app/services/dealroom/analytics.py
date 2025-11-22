"""
Deal Room Analytics Service

Tracks and analyzes viewer engagement with deal rooms.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, distinct

from backend.app.models.dealroom import (
    DealRoom, DealRoomContent, DealRoomViewEvent, ContentViewEvent,
    ViewEventResponse, ContentViewResponse, AnalyticsSummaryResponse,
)
from backend.app.services.dealroom.utils import parse_user_agent, generate_random_string

logger = logging.getLogger(__name__)


class DealRoomAnalyticsService:
    """
    Service for tracking and analyzing deal room engagement.
    """

    def __init__(self, db: Session):
        """
        Initialize the analytics service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # =========================================================================
    # VIEW TRACKING
    # =========================================================================

    def record_view(
        self,
        deal_room_id: UUID,
        viewer_email: Optional[str] = None,
        viewer_name: Optional[str] = None,
        viewer_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> DealRoomViewEvent:
        """
        Record a view event for a deal room.

        Args:
            deal_room_id: UUID of the deal room
            viewer_email: Optional email of the viewer
            viewer_name: Optional name of the viewer
            viewer_ip: IP address of the viewer
            user_agent: User agent string
            session_id: Session identifier for tracking

        Returns:
            Created view event
        """
        # Parse user agent
        device_info = parse_user_agent(user_agent) if user_agent else {}

        # Create or get session ID
        if not session_id:
            session_id = generate_random_string(16)

        # Check for existing session (within last 30 minutes)
        existing = self.db.query(DealRoomViewEvent).filter(
            and_(
                DealRoomViewEvent.deal_room_id == deal_room_id,
                DealRoomViewEvent.session_id == session_id,
                DealRoomViewEvent.last_activity_at > datetime.utcnow() - timedelta(minutes=30),
            )
        ).first()

        if existing:
            # Update existing session
            existing.last_activity_at = datetime.utcnow()
            existing.pages_viewed += 1
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new view event
        view_event = DealRoomViewEvent(
            deal_room_id=deal_room_id,
            viewer_email=viewer_email,
            viewer_name=viewer_name,
            viewer_ip=viewer_ip,
            viewer_user_agent=user_agent,
            session_id=session_id,
            device_type=device_info.get('device_type'),
            browser=device_info.get('browser'),
            os=device_info.get('os'),
            pages_viewed=1,
        )

        self.db.add(view_event)
        self.db.commit()
        self.db.refresh(view_event)

        # Update deal room last viewed
        deal_room = self.db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
        if deal_room:
            deal_room.last_viewed_at = datetime.utcnow()
            self.db.commit()

        logger.info(f"Recorded view for deal room {deal_room_id} from {viewer_email or 'anonymous'}")
        return view_event

    def record_content_view(
        self,
        view_event_id: UUID,
        content_id: UUID,
        time_spent_seconds: int = 0,
        scroll_depth_percent: int = 0,
        downloaded: bool = False,
    ) -> ContentViewEvent:
        """
        Record a view event for specific content.

        Args:
            view_event_id: UUID of the parent view event
            content_id: UUID of the content viewed
            time_spent_seconds: Time spent viewing
            scroll_depth_percent: How far they scrolled (0-100)
            downloaded: Whether they downloaded the content

        Returns:
            Created content view event
        """
        # Check for existing content view in this session
        existing = self.db.query(ContentViewEvent).filter(
            and_(
                ContentViewEvent.view_event_id == view_event_id,
                ContentViewEvent.content_id == content_id,
            )
        ).first()

        if existing:
            # Update existing
            existing.time_spent_seconds += time_spent_seconds
            existing.scroll_depth_percent = max(existing.scroll_depth_percent, scroll_depth_percent)
            existing.downloaded = existing.downloaded or downloaded
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new
        content_view = ContentViewEvent(
            view_event_id=view_event_id,
            content_id=content_id,
            time_spent_seconds=time_spent_seconds,
            scroll_depth_percent=scroll_depth_percent,
            downloaded=downloaded,
        )

        self.db.add(content_view)
        self.db.commit()
        self.db.refresh(content_view)

        return content_view

    def update_session_time(
        self,
        session_id: str,
        time_spent_seconds: int,
    ) -> Optional[DealRoomViewEvent]:
        """
        Update the total time spent in a session.

        Args:
            session_id: Session identifier
            time_spent_seconds: Total time spent

        Returns:
            Updated view event or None
        """
        view_event = self.db.query(DealRoomViewEvent).filter(
            DealRoomViewEvent.session_id == session_id
        ).first()

        if view_event:
            view_event.time_spent_seconds = time_spent_seconds
            view_event.last_activity_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(view_event)

        return view_event

    # =========================================================================
    # ANALYTICS QUERIES
    # =========================================================================

    def get_analytics_summary(
        self,
        deal_room_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnalyticsSummaryResponse:
        """
        Get comprehensive analytics summary for a deal room.

        Args:
            deal_room_id: UUID of the deal room
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Analytics summary
        """
        # Build base query
        query = self.db.query(DealRoomViewEvent).filter(
            DealRoomViewEvent.deal_room_id == deal_room_id
        )

        if start_date:
            query = query.filter(DealRoomViewEvent.viewed_at >= start_date)
        if end_date:
            query = query.filter(DealRoomViewEvent.viewed_at <= end_date)

        view_events = query.all()

        # Calculate metrics
        total_views = len(view_events)
        unique_emails = set(e.viewer_email for e in view_events if e.viewer_email)
        unique_viewers = len(unique_emails)

        total_time = sum(e.time_spent_seconds for e in view_events)
        avg_time = total_time / total_views if total_views > 0 else 0

        # Views by day
        views_by_day = defaultdict(int)
        for event in view_events:
            day_key = event.viewed_at.strftime('%Y-%m-%d')
            views_by_day[day_key] += 1

        # Views by device
        views_by_device = defaultdict(int)
        for event in view_events:
            device = event.device_type or 'unknown'
            views_by_device[device] += 1

        # Most viewed content
        most_viewed = self.get_content_analytics(deal_room_id, start_date, end_date)

        # Recent views (last 10)
        recent_views = [
            ViewEventResponse(
                id=e.id,
                deal_room_id=e.deal_room_id,
                viewer_email=e.viewer_email,
                viewer_name=e.viewer_name,
                device_type=e.device_type,
                browser=e.browser,
                country=e.country,
                city=e.city,
                time_spent_seconds=e.time_spent_seconds,
                pages_viewed=e.pages_viewed,
                viewed_at=e.viewed_at,
                last_activity_at=e.last_activity_at,
            )
            for e in sorted(view_events, key=lambda x: x.viewed_at, reverse=True)[:10]
        ]

        return AnalyticsSummaryResponse(
            deal_room_id=deal_room_id,
            total_views=total_views,
            unique_viewers=unique_viewers,
            total_time_spent_seconds=total_time,
            avg_time_per_visit_seconds=avg_time,
            most_viewed_content=most_viewed[:5],
            recent_views=recent_views,
            views_by_day=dict(views_by_day),
            views_by_device=dict(views_by_device),
        )

    def get_content_analytics(
        self,
        deal_room_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ContentViewResponse]:
        """
        Get analytics for all content in a deal room.

        Args:
            deal_room_id: UUID of the deal room
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of content analytics
        """
        # Get all content in the deal room
        contents = self.db.query(DealRoomContent).filter(
            DealRoomContent.deal_room_id == deal_room_id
        ).all()

        result = []
        for content in contents:
            # Get view events for this content
            query = self.db.query(ContentViewEvent).filter(
                ContentViewEvent.content_id == content.id
            )

            if start_date or end_date:
                query = query.join(DealRoomViewEvent)
                if start_date:
                    query = query.filter(DealRoomViewEvent.viewed_at >= start_date)
                if end_date:
                    query = query.filter(DealRoomViewEvent.viewed_at <= end_date)

            content_views = query.all()

            view_count = len(content_views)
            unique_viewers = len(set(
                self.db.query(DealRoomViewEvent.viewer_email)
                .filter(DealRoomViewEvent.id.in_([cv.view_event_id for cv in content_views]))
                .all()
            ))
            total_time = sum(cv.time_spent_seconds for cv in content_views)
            avg_scroll = (
                sum(cv.scroll_depth_percent for cv in content_views) / view_count
                if view_count > 0 else 0
            )
            downloads = sum(1 for cv in content_views if cv.downloaded)

            result.append(ContentViewResponse(
                content_id=content.id,
                content_title=content.title,
                view_count=view_count,
                unique_viewers=unique_viewers,
                total_time_spent=total_time,
                avg_scroll_depth=avg_scroll,
                download_count=downloads,
            ))

        # Sort by view count descending
        result.sort(key=lambda x: x.view_count, reverse=True)
        return result

    def get_viewer_journey(
        self,
        deal_room_id: UUID,
        viewer_email: str,
    ) -> List[Dict]:
        """
        Get the viewing journey for a specific viewer.

        Args:
            deal_room_id: UUID of the deal room
            viewer_email: Email of the viewer

        Returns:
            List of viewing sessions with content views
        """
        sessions = self.db.query(DealRoomViewEvent).filter(
            and_(
                DealRoomViewEvent.deal_room_id == deal_room_id,
                DealRoomViewEvent.viewer_email == viewer_email,
            )
        ).order_by(DealRoomViewEvent.viewed_at.desc()).all()

        journey = []
        for session in sessions:
            content_views = self.db.query(ContentViewEvent).filter(
                ContentViewEvent.view_event_id == session.id
            ).all()

            # Get content details
            content_details = []
            for cv in content_views:
                content = self.db.query(DealRoomContent).filter(
                    DealRoomContent.id == cv.content_id
                ).first()
                if content:
                    content_details.append({
                        'content_id': str(cv.content_id),
                        'content_title': content.title,
                        'content_type': content.content_type.value,
                        'time_spent_seconds': cv.time_spent_seconds,
                        'scroll_depth_percent': cv.scroll_depth_percent,
                        'downloaded': cv.downloaded,
                        'viewed_at': cv.viewed_at.isoformat(),
                    })

            journey.append({
                'session_id': session.session_id,
                'viewed_at': session.viewed_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat(),
                'device_type': session.device_type,
                'browser': session.browser,
                'time_spent_seconds': session.time_spent_seconds,
                'pages_viewed': session.pages_viewed,
                'content_views': content_details,
            })

        return journey

    def get_engagement_score(self, deal_room_id: UUID) -> Dict:
        """
        Calculate an engagement score for a deal room.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            Engagement metrics and score
        """
        summary = self.get_analytics_summary(deal_room_id)

        # Scoring factors (0-100 each)
        view_score = min(100, summary.total_views * 10)  # 10 views = 100
        viewer_score = min(100, summary.unique_viewers * 20)  # 5 unique viewers = 100
        time_score = min(100, summary.avg_time_per_visit_seconds / 3)  # 5 min avg = 100

        # Calculate content engagement
        content_analytics = summary.most_viewed_content
        if content_analytics:
            avg_scroll = sum(c.avg_scroll_depth for c in content_analytics) / len(content_analytics)
            scroll_score = avg_scroll  # 100% scroll = 100
            download_rate = (
                sum(c.download_count for c in content_analytics) /
                max(1, sum(c.view_count for c in content_analytics))
            ) * 100
            download_score = min(100, download_rate * 2)  # 50% download rate = 100
        else:
            scroll_score = 0
            download_score = 0

        # Overall score (weighted average)
        overall_score = (
            view_score * 0.15 +
            viewer_score * 0.20 +
            time_score * 0.25 +
            scroll_score * 0.25 +
            download_score * 0.15
        )

        return {
            'overall_score': round(overall_score, 1),
            'breakdown': {
                'view_score': round(view_score, 1),
                'viewer_score': round(viewer_score, 1),
                'time_score': round(time_score, 1),
                'scroll_score': round(scroll_score, 1),
                'download_score': round(download_score, 1),
            },
            'interpretation': self._interpret_score(overall_score),
        }

    def _interpret_score(self, score: float) -> str:
        """Interpret an engagement score."""
        if score >= 80:
            return "Excellent - High buyer intent"
        elif score >= 60:
            return "Good - Active engagement"
        elif score >= 40:
            return "Moderate - Some interest"
        elif score >= 20:
            return "Low - Limited engagement"
        else:
            return "Very Low - Needs follow-up"

    # =========================================================================
    # REPORTS
    # =========================================================================

    def get_weekly_report(
        self,
        deal_room_id: UUID,
    ) -> Dict:
        """
        Generate a weekly engagement report.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            Weekly report data
        """
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # This week's data
        this_week = self.get_analytics_summary(deal_room_id, week_ago, now)

        # Last week's data for comparison
        last_week = self.get_analytics_summary(deal_room_id, two_weeks_ago, week_ago)

        # Calculate trends
        def calculate_change(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100

        return {
            'period': {
                'start': week_ago.isoformat(),
                'end': now.isoformat(),
            },
            'metrics': {
                'total_views': this_week.total_views,
                'unique_viewers': this_week.unique_viewers,
                'avg_time_spent': this_week.avg_time_per_visit_seconds,
            },
            'trends': {
                'views_change': round(
                    calculate_change(this_week.total_views, last_week.total_views), 1
                ),
                'viewers_change': round(
                    calculate_change(this_week.unique_viewers, last_week.unique_viewers), 1
                ),
                'time_change': round(
                    calculate_change(
                        this_week.avg_time_per_visit_seconds,
                        last_week.avg_time_per_visit_seconds
                    ), 1
                ),
            },
            'top_content': [
                {
                    'title': c.content_title,
                    'views': c.view_count,
                }
                for c in this_week.most_viewed_content[:3]
            ],
            'engagement_score': self.get_engagement_score(deal_room_id),
        }

    def export_analytics_csv(
        self,
        deal_room_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Export analytics data as CSV.

        Args:
            deal_room_id: UUID of the deal room
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            CSV string
        """
        query = self.db.query(DealRoomViewEvent).filter(
            DealRoomViewEvent.deal_room_id == deal_room_id
        )

        if start_date:
            query = query.filter(DealRoomViewEvent.viewed_at >= start_date)
        if end_date:
            query = query.filter(DealRoomViewEvent.viewed_at <= end_date)

        view_events = query.order_by(DealRoomViewEvent.viewed_at.desc()).all()

        # Build CSV
        lines = [
            'Date,Email,Name,Device,Browser,Country,Time Spent (s),Pages Viewed'
        ]

        for event in view_events:
            lines.append(','.join([
                event.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                event.viewer_email or '',
                event.viewer_name or '',
                event.device_type or '',
                event.browser or '',
                event.country or '',
                str(event.time_spent_seconds),
                str(event.pages_viewed),
            ]))

        return '\n'.join(lines)
