"""
Talk Track Generation Service

Provides WbD methodology-aligned talk track and script generation
for various sales scenarios including discovery calls, demos,
objection handling, closing conversations, and follow-ups.
"""

from .generator import TalkTrackGenerator
from .templates import ScriptTemplates
from .performance import TalkTrackPerformanceTracker

__all__ = [
    "TalkTrackGenerator",
    "ScriptTemplates",
    "TalkTrackPerformanceTracker",
]
