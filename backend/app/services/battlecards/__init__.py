"""
Battlecard Services Module

Provides battlecard generation and management capabilities:
- Competitive battlecards
- Objection handling cards
- Feature comparison matrices
- Win/loss analysis cards
"""

from .battlecard_service import BattlecardService
from .competitor_service import CompetitorService
from .generator import BattlecardGenerator

__all__ = [
    "BattlecardService",
    "CompetitorService",
    "BattlecardGenerator",
]
