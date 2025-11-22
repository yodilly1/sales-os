"""
Follow-up automation service package.

This package provides automated follow-up generation and scheduling capabilities
based on SPICED analysis from sales calls.

Components:
- generator: AI-powered follow-up content generation
- scheduler: Scheduling and timing optimization
- workflow: Approval workflow management
- sequence: Multi-touch sequence orchestration
- crm_sync: CRM task synchronization
"""

from .generator import FollowUpGenerator
from .scheduler import FollowUpScheduler
from .workflow import ApprovalWorkflow
from .sequence import SequenceManager
from .crm_sync import CRMSyncService

__all__ = [
    "FollowUpGenerator",
    "FollowUpScheduler",
    "ApprovalWorkflow",
    "SequenceManager",
    "CRMSyncService",
]
