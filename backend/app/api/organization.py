"""Organization API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession, CurrentUser, AdminUser
from app.schemas.organization import (
    OrganizationUpdate,
    OrganizationResponse,
)
from app.services.team.organization_service import OrganizationService

router = APIRouter()


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get the current user's organization."""
    org_service = OrganizationService(db)
    org = await org_service.get_by_id(current_user.organization_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get an organization by ID."""
    # Users can only view their own organization
    if org_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other organizations",
        )

    org_service = OrganizationService(db)
    org = await org_service.get_by_id(org_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    current_user: AdminUser,
    db: DbSession,
):
    """Update an organization (admin only)."""
    # Users can only update their own organization
    if org_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other organizations",
        )

    org_service = OrganizationService(db)
    org = await org_service.update_organization(org_id, data)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.get("/{org_id}/stats")
async def get_organization_stats(
    org_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Get organization statistics (admin only)."""
    if org_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other organizations",
        )

    org_service = OrganizationService(db)
    stats = await org_service.get_organization_stats(org_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return stats


@router.patch("/{org_id}/settings")
async def update_organization_settings(
    org_id: str,
    settings: dict,
    current_user: AdminUser,
    db: DbSession,
):
    """Update organization settings (admin only)."""
    if org_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other organizations",
        )

    org_service = OrganizationService(db)
    data = OrganizationUpdate(settings=settings)
    org = await org_service.update_organization(org_id, data)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return {"message": "Settings updated successfully", "settings": org.settings}
