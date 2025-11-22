"""Authentication API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.tokens import TokenPair
from app.core.auth.oauth2 import (
    OAuthStateManager,
    get_oauth_client,
    OAuthTokenResponse,
)
from app.core.auth.api_key import APIKeyManager
from app.core.constants import OAuthProvider, AuditAction
from app.db.session import get_db
from app.middleware.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_permissions,
)
from app.middleware.audit import AuditLogger
from app.middleware.rate_limit import limiter, AUTH_RATE_LIMIT
from app.models.oauth_token import OAuthToken
from app.services.auth_service import AuthService

router = APIRouter()


# Request/Response schemas
class LoginRequest(BaseModel):
    """Login request schema."""

    email_or_username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: "UserResponse"


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    roles: List[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class APIKeyCreateRequest(BaseModel):
    """API key creation request schema."""

    name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response schema."""

    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: Optional[List[str]]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response (includes raw key)."""

    key: str  # Only returned once on creation


class OAuthInitiateResponse(BaseModel):
    """OAuth initiation response."""

    authorization_url: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""

    code: str
    state: str


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# Auth endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    auth_service = AuthService(db)

    try:
        user = await auth_service.register_user(
            email=data.email,
            username=data.username,
            password=data.password,
            full_name=data.full_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return UserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Login with email/username and password."""
    auth_service = AuthService(db)
    audit_logger = AuditLogger(db)

    result = await auth_service.login(data.email_or_username, data.password)

    if not result:
        # Log failed login attempt
        # Note: We don't have user_id for failed attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, tokens = result

    # Log successful login
    await audit_logger.log_login(user.id, request, success=True)

    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)

    tokens = await auth_service.refresh_tokens(data.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tokens


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Logout current user (invalidates tokens on client side)."""
    audit_logger = AuditLogger(db)
    await audit_logger.log_logout(current_user.user_id, request)

    # Note: For true token invalidation, implement a token blacklist
    # using Redis or similar in production
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user.user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Change current user's password."""
    auth_service = AuthService(db)

    success = await auth_service.change_password(
        user_id=current_user.user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return MessageResponse(message="Password changed successfully")


# API Key endpoints
@router.post("/api-keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: Request,
    data: APIKeyCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreatedResponse:
    """Create a new API key."""
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

    api_key, raw_key = await APIKeyManager.create_api_key(
        db=db,
        user_id=current_user.user_id,
        name=data.name,
        scopes=data.scopes,
        expires_at=expires_at,
    )

    # Log API key creation
    audit_logger = AuditLogger(db)
    await audit_logger.log_api_key_created(
        current_user.user_id,
        api_key.id,
        request,
        data.name,
    )

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=raw_key,  # Only returned once!
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> List[APIKeyResponse]:
    """List all API keys for current user."""
    api_keys = await APIKeyManager.get_user_api_keys(db, current_user.user_id)
    return [APIKeyResponse.model_validate(key) for key in api_keys]


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: uuid.UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke an API key."""
    success = await APIKeyManager.revoke_api_key(db, key_id, current_user.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Log API key revocation
    audit_logger = AuditLogger(db)
    await audit_logger.log_api_key_revoked(current_user.user_id, key_id, request)

    return MessageResponse(message="API key revoked successfully")


# OAuth endpoints
@router.get("/oauth/{provider}/authorize", response_model=OAuthInitiateResponse)
async def oauth_authorize(
    provider: OAuthProvider,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
) -> OAuthInitiateResponse:
    """Initiate OAuth flow for a provider."""
    oauth_client = get_oauth_client(provider)

    # Create and store state
    state = OAuthStateManager.create_state(
        user_id=current_user.user_id,
        provider=provider,
    )

    authorization_url = oauth_client.get_authorization_url(state)

    return OAuthInitiateResponse(authorization_url=authorization_url)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: OAuthProvider,
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Handle OAuth callback from provider."""
    # Verify state
    state_data = OAuthStateManager.verify_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    if state_data["provider"] != provider.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider mismatch",
        )

    user_id = uuid.UUID(state_data["user_id"])

    # Exchange code for tokens
    oauth_client = get_oauth_client(provider)
    try:
        token_response = await oauth_client.exchange_code(code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {str(e)}",
        )

    # Calculate expiration
    expires_at = None
    if token_response.expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_response.expires_in)

    # Store tokens
    oauth_token = OAuthToken(
        user_id=user_id,
        provider=provider.value,
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        scope=token_response.scope,
        expires_at=expires_at,
    )

    db.add(oauth_token)
    await db.commit()

    # Log OAuth connection
    audit_logger = AuditLogger(db)
    await audit_logger.log_oauth_connected(user_id, provider.value, request)

    return MessageResponse(message=f"Successfully connected to {provider.value}")


@router.delete("/oauth/{provider}", response_model=MessageResponse)
async def oauth_disconnect(
    provider: OAuthProvider,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Disconnect OAuth provider."""
    from sqlalchemy import select, delete

    # Find and delete OAuth token
    result = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == current_user.user_id,
            OAuthToken.provider == provider.value,
        )
    )
    oauth_token = result.scalar_one_or_none()

    if not oauth_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {provider.value} connection found",
        )

    # Optionally revoke token at provider
    oauth_client = get_oauth_client(provider)
    try:
        await oauth_client.revoke_token(oauth_token.access_token)
    except Exception:
        pass  # Best effort revocation

    # Delete from database
    await db.delete(oauth_token)
    await db.commit()

    # Log disconnection
    audit_logger = AuditLogger(db)
    await audit_logger.log_oauth_disconnected(current_user.user_id, provider.value, request)

    return MessageResponse(message=f"Successfully disconnected from {provider.value}")


@router.get("/oauth/connections", response_model=List[str])
async def list_oauth_connections(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """List connected OAuth providers for current user."""
    from sqlalchemy import select

    result = await db.execute(
        select(OAuthToken.provider).where(OAuthToken.user_id == current_user.user_id)
    )
    providers = result.scalars().all()

    return list(providers)
