"""
Pydantic models for Sales OS API.
"""

from .battlecard import (
    Battlecard,
    BattlecardType,
    BattlecardStatus,
    BattlecardContent,
    BattlecardGenerateRequest,
    BattlecardUpdateRequest,
    BattlecardResponse,
    BattlecardListResponse,
    Competitor,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorListResponse,
)

__all__ = [
    "Battlecard",
    "BattlecardType",
    "BattlecardStatus",
    "BattlecardContent",
    "BattlecardGenerateRequest",
    "BattlecardUpdateRequest",
    "BattlecardResponse",
    "BattlecardListResponse",
    "Competitor",
    "CompetitorCreate",
    "CompetitorUpdate",
    "CompetitorListResponse",
]
