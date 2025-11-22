"""
Deal Room Service Package

Provides digital deal rooms for sharing content with prospects.
Features:
- Branded shareable links
- Content organization (folders, sections)
- Viewer analytics (who viewed what, when)
- Access controls (password, expiry)
- Mutual action plans
"""

from backend.app.services.dealroom.service import DealRoomService
from backend.app.services.dealroom.analytics import DealRoomAnalyticsService
from backend.app.services.dealroom.access import DealRoomAccessService

__all__ = [
    "DealRoomService",
    "DealRoomAnalyticsService",
    "DealRoomAccessService",
]
