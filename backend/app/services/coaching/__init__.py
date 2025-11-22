"""
SPICED Coaching Service

This module provides comprehensive coaching functionality aligned with
the Winning by Design (WbD) methodology, including:
- Per-call SPICED scoring and feedback
- Gap analysis and missed opportunity detection
- Trend analysis over time
- Team benchmarking
"""

from .coaching_service import CoachingService
from .analyzer import SPICEDAnalyzer
from .benchmarking import TeamBenchmarkingService
from .trends import TrendAnalysisService

__all__ = [
    "CoachingService",
    "SPICEDAnalyzer",
    "TeamBenchmarkingService",
    "TrendAnalysisService",
]
