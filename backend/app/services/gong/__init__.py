"""
Gong Service Package

Services for Gong integration business logic including
sync operations and call processing.
"""

from .sync_service import GongSyncService

__all__ = ["GongSyncService"]
