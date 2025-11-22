"""
Battlecard API Routes

FastAPI routes for battlecard generation, management, and competitive intelligence.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from ..models.battlecard import (
    BattlecardType,
    BattlecardStatus,
    BattlecardGenerateRequest,
    BattlecardUpdateRequest,
    BattlecardResponse,
    BattlecardListResponse,
    BattlecardSearchRequest,
    BattlecardExportRequest,
    BattlecardExportFormat,
    FavoriteRequest,
    Competitor,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorStrength,
    CompetitorWeakness,
    CompetitorListResponse,
)
from ..services.battlecards import BattlecardService, CompetitorService


router = APIRouter(prefix="/battlecards", tags=["battlecards"])

# Initialize services
battlecard_service = BattlecardService()
competitor_service = CompetitorService()


# -----------------------------------------------------------------------------
# Battlecard CRUD Operations
# -----------------------------------------------------------------------------

@router.post("/generate", response_model=BattlecardResponse)
async def generate_battlecard(
    request: BattlecardGenerateRequest,
    user_id: Optional[str] = Query(None, description="User ID creating the battlecard"),
    team_id: Optional[str] = Query(None, description="Team ID for the battlecard"),
):
    """
    Generate a new battlecard using AI.

    Supports four battlecard types:
    - **competitive**: Battlecard against a specific competitor
    - **objection_handling**: Objection handling responses
    - **feature_comparison**: Feature comparison matrix
    - **win_loss_analysis**: Win/loss analysis insights

    The generated content is tailored based on the battlecard type and
    any competitor or context information provided.
    """
    return await battlecard_service.generate(request, user_id, team_id)


@router.get("/{battlecard_id}", response_model=BattlecardResponse)
async def get_battlecard(battlecard_id: str):
    """
    Get a battlecard by ID.

    Returns the full battlecard including content and metadata.
    Increments the view count on each request.
    """
    battlecard = battlecard_service.get(battlecard_id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")

    return BattlecardResponse(
        success=True,
        battlecard=battlecard,
    )


@router.get("/", response_model=BattlecardListResponse)
async def list_battlecards(
    query: Optional[str] = Query(None, description="Search query"),
    type: Optional[BattlecardType] = Query(None, description="Filter by type"),
    status: Optional[BattlecardStatus] = Query(None, description="Filter by status"),
    competitor_id: Optional[str] = Query(None, description="Filter by competitor"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    favorites_only: bool = Query(False, description="Show only favorites"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    List battlecards with optional filtering.

    Supports filtering by:
    - Text search (title, description)
    - Battlecard type
    - Status (draft, published, archived)
    - Competitor
    - Tags
    - Team (includes shared battlecards)

    Results are paginated.
    """
    search_request = BattlecardSearchRequest(
        query=query,
        type=type,
        status=status,
        competitor_id=competitor_id,
        tags=tags.split(",") if tags else None,
        team_id=team_id,
        favorites_only=favorites_only,
        page=page,
        page_size=page_size,
    )

    return battlecard_service.list(search_request)


@router.put("/{battlecard_id}", response_model=BattlecardResponse)
async def update_battlecard(
    battlecard_id: str,
    request: BattlecardUpdateRequest,
    user_id: Optional[str] = Query(None, description="User ID making the update"),
):
    """
    Update an existing battlecard.

    Creates a new version and preserves the previous version in history.
    Only provided fields will be updated.
    """
    response = battlecard_service.update(battlecard_id, request, user_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.delete("/{battlecard_id}")
async def delete_battlecard(battlecard_id: str):
    """
    Delete a battlecard.

    This is a permanent deletion. Consider archiving instead for
    important battlecards.
    """
    if not battlecard_service.delete(battlecard_id):
        raise HTTPException(status_code=404, detail="Battlecard not found")

    return {"success": True, "message": "Battlecard deleted"}


# -----------------------------------------------------------------------------
# Sharing and Favorites
# -----------------------------------------------------------------------------

@router.post("/{battlecard_id}/share", response_model=BattlecardResponse)
async def share_battlecard(
    battlecard_id: str,
    team_ids: list[str],
):
    """
    Share a battlecard with one or more teams.

    Shared battlecards appear in the team's battlecard list.
    """
    response = battlecard_service.share(battlecard_id, team_ids)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.post("/{battlecard_id}/unshare", response_model=BattlecardResponse)
async def unshare_battlecard(
    battlecard_id: str,
    team_ids: list[str],
):
    """
    Remove sharing from one or more teams.
    """
    response = battlecard_service.unshare(battlecard_id, team_ids)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.post("/{battlecard_id}/favorite", response_model=BattlecardResponse)
async def toggle_favorite(
    battlecard_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """
    Toggle favorite status for a battlecard.

    If currently favorited, removes from favorites.
    If not favorited, adds to favorites.
    """
    response = battlecard_service.toggle_favorite(battlecard_id, user_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.get("/favorites/list", response_model=BattlecardListResponse)
async def get_favorites(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get a user's favorite battlecards.
    """
    return battlecard_service.get_favorites(user_id, page, page_size)


# -----------------------------------------------------------------------------
# Version History
# -----------------------------------------------------------------------------

@router.get("/{battlecard_id}/versions")
async def get_version_history(battlecard_id: str):
    """
    Get version history for a battlecard.

    Returns all previous versions with timestamps and change summaries.
    """
    battlecard = battlecard_service.get(battlecard_id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")

    return {
        "success": True,
        "current_version": battlecard.version,
        "versions": battlecard_service.get_version_history(battlecard_id),
    }


@router.post("/{battlecard_id}/versions/{version_number}/restore", response_model=BattlecardResponse)
async def restore_version(
    battlecard_id: str,
    version_number: int,
    user_id: Optional[str] = Query(None),
):
    """
    Restore a battlecard to a previous version.

    Creates a new version with the restored content.
    The current version is preserved in history.
    """
    response = battlecard_service.restore_version(battlecard_id, version_number, user_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)
    return response


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------

@router.post("/{battlecard_id}/export")
async def export_battlecard(
    battlecard_id: str,
    format: BattlecardExportFormat = Query(BattlecardExportFormat.MARKDOWN),
    include_version_history: bool = Query(False),
):
    """
    Export a battlecard in the specified format.

    Supported formats:
    - **markdown**: Markdown text (print-friendly)
    - **html**: HTML document with styling
    - **json**: Full JSON representation
    - **pdf**: PDF document (requires rendering service)
    """
    request = BattlecardExportRequest(
        battlecard_id=battlecard_id,
        format=format,
        include_version_history=include_version_history,
    )

    result = battlecard_service.export(request)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# -----------------------------------------------------------------------------
# Win/Loss Data Refresh
# -----------------------------------------------------------------------------

@router.post("/{battlecard_id}/refresh", response_model=BattlecardResponse)
async def refresh_from_data(
    battlecard_id: str,
    win_loss_data: list[dict] = [],
):
    """
    Refresh battlecard content with new win/loss data.

    Updates the battlecard's insights based on the latest
    deal outcomes and patterns.
    """
    response = await battlecard_service.refresh_from_win_loss(battlecard_id, win_loss_data)
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response


# -----------------------------------------------------------------------------
# Competitor Management
# -----------------------------------------------------------------------------

competitor_router = APIRouter(prefix="/competitors", tags=["competitors"])


@competitor_router.post("/", response_model=Competitor)
async def create_competitor(request: CompetitorCreate):
    """
    Create a new competitor.

    Add a competitor to the competitive intelligence database.
    """
    try:
        return competitor_service.create(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@competitor_router.get("/{competitor_id}", response_model=Competitor)
async def get_competitor(competitor_id: str):
    """
    Get a competitor by ID.
    """
    competitor = competitor_service.get(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@competitor_router.get("/", response_model=CompetitorListResponse)
async def list_competitors(
    search: Optional[str] = Query(None, description="Search by name or description"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all competitors.

    Optionally filter by search term.
    """
    return competitor_service.list(search=search, limit=limit, offset=offset)


@competitor_router.put("/{competitor_id}", response_model=Competitor)
async def update_competitor(
    competitor_id: str,
    request: CompetitorUpdate,
):
    """
    Update a competitor.
    """
    competitor = competitor_service.update(competitor_id, request)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@competitor_router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: str):
    """
    Delete a competitor.
    """
    if not competitor_service.delete(competitor_id):
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"success": True, "message": "Competitor deleted"}


@competitor_router.post("/{competitor_id}/strengths", response_model=Competitor)
async def add_strength(
    competitor_id: str,
    strength: CompetitorStrength,
):
    """
    Add a strength to a competitor.
    """
    competitor = competitor_service.add_strength(competitor_id, strength)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@competitor_router.post("/{competitor_id}/weaknesses", response_model=Competitor)
async def add_weakness(
    competitor_id: str,
    weakness: CompetitorWeakness,
):
    """
    Add a weakness to a competitor.
    """
    competitor = competitor_service.add_weakness(competitor_id, weakness)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@competitor_router.put("/{competitor_id}/win-rate")
async def update_win_rate(
    competitor_id: str,
    win_rate: float = Query(..., ge=0, le=100, description="Win rate percentage"),
):
    """
    Update win rate against a competitor.
    """
    try:
        competitor = competitor_service.update_win_rate(competitor_id, win_rate)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        return competitor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@competitor_router.post("/{competitor_id}/objections", response_model=Competitor)
async def add_objection(
    competitor_id: str,
    objection: str = Query(..., description="Objection text"),
):
    """
    Add a common objection when competing against this competitor.
    """
    competitor = competitor_service.add_objection(competitor_id, objection)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@competitor_router.get("/market/{market}")
async def search_by_market(market: str):
    """
    Find competitors targeting a specific market.
    """
    competitors = competitor_service.search_by_market(market)
    return {
        "success": True,
        "market": market,
        "competitors": competitors,
        "total": len(competitors),
    }


# Include competitor router in main router
router.include_router(competitor_router)
