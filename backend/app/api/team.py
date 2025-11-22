"""Team API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession, CurrentUser, AdminUser, ManagerUser
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamWithMembersResponse,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamPerformanceResponse,
)
from app.schemas.user import UserResponse, UserListResponse, UserUpdate
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationAccept,
    InvitationListResponse,
)
from app.services.team.team_service import TeamService
from app.services.team.user_service import UserService
from app.services.team.invitation_service import InvitationService
from app.models.user import UserRole

router = APIRouter()


# ============ Team CRUD ============

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    current_user: AdminUser,
    db: DbSession,
):
    """Create a new team (admin only)."""
    team_service = TeamService(db)

    try:
        team = await team_service.create_team(
            organization_id=current_user.organization_id,
            data=data,
        )
        return team
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = True,
):
    """List teams in the current organization."""
    team_service = TeamService(db)

    # Admins and managers see all teams; reps only see their teams
    if current_user.is_manager:
        teams, total = await team_service.list_teams(
            organization_id=current_user.organization_id,
            page=page,
            per_page=per_page,
            active_only=active_only,
        )
    else:
        teams = await team_service.get_user_teams(
            user_id=current_user.id,
            active_only=active_only,
        )
        total = len(teams)
        # Apply pagination manually
        start = (page - 1) * per_page
        teams = teams[start : start + per_page]

    return TeamListResponse(
        items=[TeamResponse.model_validate(t) for t in teams],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{team_id}", response_model=TeamWithMembersResponse)
async def get_team(
    team_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a team by ID."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id, include_members=True)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Check access
    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access teams from other organizations",
        )

    # Non-managers can only view teams they belong to
    if not current_user.is_manager:
        is_member = any(
            m.team_id == team_id and m.is_active
            for m in current_user.team_memberships
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this team",
            )

    # Build response with member details
    members = []
    for m in team.members:
        if m.is_active:
            members.append(
                TeamMemberResponse(
                    id=m.id,
                    user_id=m.user_id,
                    team_id=m.team_id,
                    is_team_lead=m.is_team_lead,
                    is_active=m.is_active,
                    created_at=m.created_at,
                    user_email=m.user.email if m.user else None,
                    user_name=m.user.full_name if m.user else None,
                )
            )

    return TeamWithMembersResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        organization_id=team.organization_id,
        settings=team.settings,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=len(members),
        members=members,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    data: TeamUpdate,
    current_user: ManagerUser,
    db: DbSession,
):
    """Update a team (manager/admin only)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update teams from other organizations",
        )

    # Managers can only update teams they lead (unless admin)
    if not current_user.is_admin:
        if not current_user.can_manage_team(team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team leads can update this team",
            )

    updated_team = await team_service.update_team(team_id, data)
    return updated_team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Delete a team (admin only, soft delete)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete teams from other organizations",
        )

    await team_service.delete_team(team_id)


# ============ Team Members ============

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: str,
    data: TeamMemberAdd,
    current_user: ManagerUser,
    db: DbSession,
):
    """Add a member to a team (manager/admin only)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify teams from other organizations",
        )

    try:
        member = await team_service.add_member(team_id, data)

        # Load user details
        user_service = UserService(db)
        user = await user_service.get_by_id(member.user_id)

        return TeamMemberResponse(
            id=member.id,
            user_id=member.user_id,
            team_id=member.team_id,
            is_team_lead=member.is_team_lead,
            is_active=member.is_active,
            created_at=member.created_at,
            user_email=user.email if user else None,
            user_name=user.full_name if user else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: ManagerUser,
    db: DbSession,
):
    """Remove a member from a team (manager/admin only)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify teams from other organizations",
        )

    success = await team_service.remove_member(team_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member(
    team_id: str,
    user_id: str,
    data: TeamMemberUpdate,
    current_user: ManagerUser,
    db: DbSession,
):
    """Update a team member's role (manager/admin only)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify teams from other organizations",
        )

    member = await team_service.update_member(team_id, user_id, data)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )

    # Load user details
    user_service = UserService(db)
    user = await user_service.get_by_id(member.user_id)

    return TeamMemberResponse(
        id=member.id,
        user_id=member.user_id,
        team_id=member.team_id,
        is_team_lead=member.is_team_lead,
        is_active=member.is_active,
        created_at=member.created_at,
        user_email=user.email if user else None,
        user_name=user.full_name if user else None,
    )


@router.get("/{team_id}/performance", response_model=TeamPerformanceResponse)
async def get_team_performance(
    team_id: str,
    current_user: ManagerUser,
    db: DbSession,
):
    """Get team performance metrics (manager/admin only)."""
    team_service = TeamService(db)
    team = await team_service.get_by_id(team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if team.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access teams from other organizations",
        )

    performance = await team_service.get_team_performance(team_id)
    return performance


# ============ Users Management ============

@router.get("/users/all", response_model=UserListResponse)
async def list_organization_users(
    current_user: ManagerUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = True,
    role: UserRole | None = None,
    search: str | None = None,
):
    """List all users in the organization (manager/admin only)."""
    user_service = UserService(db)

    users, total = await user_service.list_users(
        organization_id=current_user.organization_id,
        page=page,
        per_page=per_page,
        active_only=active_only,
        role=role,
        search=search,
    )

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a user by ID."""
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access users from other organizations",
        )

    # Check access permissions
    if not current_user.can_view_user_data(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this user",
        )

    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a user. Users can update themselves; admins can update anyone."""
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update users from other organizations",
        )

    # Only admins can update other users
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update other users",
        )

    try:
        updated_user = await user_service.update_user(
            user_id,
            data,
            requesting_user=current_user,
        )
        return updated_user
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/users/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Deactivate a user (admin only)."""
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate users from other organizations",
        )

    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    await user_service.deactivate_user(user_id)
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/reactivate", response_model=dict)
async def reactivate_user(
    user_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Reactivate a deactivated user (admin only)."""
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reactivate users from other organizations",
        )

    await user_service.reactivate_user(user_id)
    return {"message": "User reactivated successfully"}


# ============ Invitations ============

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    data: InvitationCreate,
    current_user: AdminUser,
    db: DbSession,
):
    """Create an invitation (admin only)."""
    invitation_service = InvitationService(db)

    try:
        invitation = await invitation_service.create_invitation(
            organization_id=current_user.organization_id,
            data=data,
            invited_by_id=current_user.id,
        )

        return InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            organization_id=invitation.organization_id,
            team_id=invitation.team_id,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            invited_by_email=current_user.email,
            invited_by_name=current_user.full_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    current_user: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    """List invitations (admin only)."""
    invitation_service = InvitationService(db)

    from app.models.invitation import InvitationStatus
    status_enum = InvitationStatus(status) if status else None

    invitations, total = await invitation_service.list_invitations(
        organization_id=current_user.organization_id,
        page=page,
        per_page=per_page,
        status=status_enum,
    )

    items = []
    for inv in invitations:
        items.append(
            InvitationResponse(
                id=inv.id,
                email=inv.email,
                role=inv.role,
                organization_id=inv.organization_id,
                team_id=inv.team_id,
                status=inv.status,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
                invited_by_email=inv.invited_by.email if inv.invited_by else None,
                invited_by_name=inv.invited_by.full_name if inv.invited_by else None,
            )
        )

    return InvitationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/invitations/accept", response_model=dict)
async def accept_invitation(
    data: InvitationAccept,
    db: DbSession,
):
    """Accept an invitation (public endpoint)."""
    invitation_service = InvitationService(db)

    try:
        user = await invitation_service.accept_invitation(
            token=data.token,
            full_name=data.full_name,
            password=data.password,
        )

        # Generate tokens for the new user
        from app.core.security import create_access_token, create_refresh_token

        token_data = {
            "sub": user.id,
            "org_id": user.organization_id,
            "role": user.role,
        }

        return {
            "message": "Invitation accepted successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Revoke an invitation (admin only)."""
    invitation_service = InvitationService(db)
    invitation = await invitation_service.get_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke invitations from other organizations",
        )

    try:
        await invitation_service.revoke_invitation(invitation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationResponse)
async def resend_invitation(
    invitation_id: str,
    current_user: AdminUser,
    db: DbSession,
):
    """Resend an invitation (admin only)."""
    invitation_service = InvitationService(db)
    invitation = await invitation_service.get_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot resend invitations from other organizations",
        )

    try:
        updated_invitation = await invitation_service.resend_invitation(invitation_id)

        return InvitationResponse(
            id=updated_invitation.id,
            email=updated_invitation.email,
            role=updated_invitation.role,
            organization_id=updated_invitation.organization_id,
            team_id=updated_invitation.team_id,
            status=updated_invitation.status,
            expires_at=updated_invitation.expires_at,
            created_at=updated_invitation.created_at,
            invited_by_email=current_user.email,
            invited_by_name=current_user.full_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
