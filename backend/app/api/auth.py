"""Authentication API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession, CurrentUser
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordChangeRequest,
)
from app.schemas.user import UserResponse
from app.schemas.organization import OrganizationCreate
from app.services.team.organization_service import OrganizationService
from app.services.team.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(
    data: RegisterRequest,
    db: DbSession,
):
    """Register a new organization with an admin user."""
    org_service = OrganizationService(db)

    try:
        org_data = OrganizationCreate(
            name=data.organization_name,
            slug=data.organization_slug,
        )
        org, user = await org_service.create_organization(
            data=org_data,
            admin_email=data.email,
            admin_password=data.password,
            admin_name=data.full_name,
        )

        # Generate tokens
        token_data = {
            "sub": user.id,
            "org_id": org.id,
            "role": user.role,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "message": "Registration successful",
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    """Login with email and password."""
    user_service = UserService(db)

    user = await user_service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": user.id,
        "org_id": user.organization_id,
        "role": user.role,
    }

    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DbSession,
):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_service = UserService(db)
    user = await user_service.get_by_id(payload.get("sub"))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {
        "sub": user.id,
        "org_id": user.organization_id,
        "role": user.role,
    }

    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """Get current user information."""
    return current_user


@router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Change current user's password."""
    user_service = UserService(db)

    try:
        success = await user_service.change_password(
            user_id=current_user.id,
            current_password=data.current_password,
            new_password=data.new_password,
        )
        if success:
            return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to change password",
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard tokens)."""
    return {"message": "Successfully logged out"}
