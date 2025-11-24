"""Authentication middleware and dependencies."""

import uuid
from typing import Annotated, List, Optional

from jose import jwt, JWTError
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.tokens import verify_token, TokenData
from app.core.auth.api_key import APIKeyManager
from app.core.auth.rbac import Permission, RBACChecker, has_permission
from app.core.constants import TokenType, API_KEY_HEADER
from app.db.session import get_db
from app.models.user import User
from app.models.api_key import APIKey


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Container for authenticated user data."""

    def __init__(
        self,
        user: User,
        token_data: Optional[TokenData] = None,
        api_key: Optional[APIKey] = None,
    ):
        self.user = user
        self.token_data = token_data
        self.api_key = api_key

    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    @property
    def roles(self) -> List[str]:
        return self.user.roles

    @property
    def is_api_key_auth(self) -> bool:
        return self.api_key is not None


async def _authenticate_jwt(
    credentials: HTTPAuthorizationCredentials,
    db: AsyncSession,
) -> Optional[AuthenticatedUser]:
    """Authenticate using JWT token."""
    try:
        token_data = verify_token(credentials.credentials, TokenType.ACCESS)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(user=user, token_data=token_data)


async def _authenticate_api_key(
    api_key_header: str,
    db: AsyncSession,
) -> Optional[AuthenticatedUser]:
    """Authenticate using API key."""
    api_key = await APIKeyManager.verify_and_get_key(db, api_key_header)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return AuthenticatedUser(user=user, api_key=api_key)


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    x_api_key: Annotated[Optional[str], Header(alias=API_KEY_HEADER)] = None,
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """
    Get the current authenticated user.

    Supports both JWT Bearer tokens and API keys.
    """
    # Try JWT authentication first
    if credentials:
        return await _authenticate_jwt(credentials, db)

    # Try API key authentication
    if x_api_key:
        return await _authenticate_api_key(x_api_key, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """Get the current user and verify they are active."""
    if not current_user.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


async def get_optional_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    x_api_key: Annotated[Optional[str], Header(alias=API_KEY_HEADER)] = None,
    db: AsyncSession = Depends(get_db),
) -> Optional[AuthenticatedUser]:
    """
    Get the current user if authenticated, or None if not.

    Useful for endpoints that work both authenticated and unauthenticated.
    """
    if not credentials and not x_api_key:
        return None

    try:
        if credentials:
            return await _authenticate_jwt(credentials, db)
        if x_api_key:
            return await _authenticate_api_key(x_api_key, db)
    except HTTPException:
        return None

    return None


def require_permissions(*permissions: Permission, require_all: bool = True):
    """
    Dependency factory for requiring specific permissions.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: AuthenticatedUser = Depends(require_permissions(Permission.USER_DELETE))
        ):
            ...
    """

    async def permission_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    ) -> AuthenticatedUser:
        checker = RBACChecker(
            required_permissions=list(permissions),
            require_all=require_all,
        )

        if not checker.check(current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return permission_checker


def require_roles(*roles: str):
    """
    Dependency factory for requiring specific roles.

    Usage:
        @router.get("/managers-only")
        async def manager_endpoint(
            user: AuthenticatedUser = Depends(require_roles("admin", "manager"))
        ):
            ...
    """

    async def role_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    ) -> AuthenticatedUser:
        user_roles = set(current_user.roles)
        required_roles = set(roles)

        if not user_roles & required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )

        return current_user

    return role_checker


def require_api_key_scope(scope: str):
    """
    Dependency factory for requiring specific API key scope.

    Only applies when authenticating with API key.

    Usage:
        @router.post("/webhooks")
        async def webhook_endpoint(
            user: AuthenticatedUser = Depends(require_api_key_scope("webhooks:write"))
        ):
            ...
    """

    async def scope_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    ) -> AuthenticatedUser:
        # If authenticated via JWT, scopes don't apply
        if not current_user.is_api_key_auth:
            return current_user

        # Check API key scope
        if not APIKeyManager.has_scope(current_user.api_key, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope: {scope}",
            )

        return current_user

    return scope_checker
