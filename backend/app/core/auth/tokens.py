"""JWT token generation and validation."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from jose import jwt, JWTError
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.constants import TokenType


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str  # Subject (user ID)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    jti: str  # JWT ID (unique identifier)
    type: TokenType  # Token type (access or refresh)
    roles: List[str] = Field(default_factory=list)
    organization_id: Optional[str] = None
    team_id: Optional[str] = None


class TokenData(BaseModel):
    """Decoded token data."""

    user_id: uuid.UUID
    token_type: TokenType
    roles: List[str] = Field(default_factory=list)
    organization_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    jti: str


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # Access token expiry in seconds


def create_access_token(
    user_id: uuid.UUID,
    roles: List[str],
    organization_id: Optional[uuid.UUID] = None,
    team_id: Optional[uuid.UUID] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a new JWT access token.

    Args:
        user_id: The user's UUID
        roles: List of user roles
        organization_id: Optional organization UUID
        team_id: Optional team UUID
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT access token
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = TokenPayload(
        sub=str(user_id),
        exp=expire,
        iat=now,
        jti=str(uuid.uuid4()),
        type=TokenType.ACCESS,
        roles=roles,
        organization_id=str(organization_id) if organization_id else None,
        team_id=str(team_id) if team_id else None,
    )

    return jwt.encode(
        payload.model_dump(mode="json"),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a new JWT refresh token.

    Args:
        user_id: The user's UUID
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = TokenPayload(
        sub=str(user_id),
        exp=expire,
        iat=now,
        jti=str(uuid.uuid4()),
        type=TokenType.REFRESH,
        roles=[],  # Refresh tokens don't include roles
    )

    return jwt.encode(
        payload.model_dump(mode="json"),
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_pair(
    user_id: uuid.UUID,
    roles: List[str],
    organization_id: Optional[uuid.UUID] = None,
    team_id: Optional[uuid.UUID] = None,
) -> TokenPair:
    """
    Create both access and refresh tokens.

    Args:
        user_id: The user's UUID
        roles: List of user roles
        organization_id: Optional organization UUID
        team_id: Optional team UUID

    Returns:
        TokenPair with access and refresh tokens
    """
    access_token = create_access_token(
        user_id=user_id,
        roles=roles,
        organization_id=organization_id,
        team_id=team_id,
    )
    refresh_token = create_refresh_token(user_id=user_id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        TokenPayload with decoded data

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise e


def verify_token(
    token: str,
    expected_type: TokenType = TokenType.ACCESS,
) -> TokenData:
    """
    Verify a JWT token and return parsed data.

    Args:
        token: The JWT token to verify
        expected_type: Expected token type (access or refresh)

    Returns:
        TokenData with parsed user information

    Raises:
    Raises:
        JWTError: If token is invalid or expired
        ValueError: If token type doesn't match expected type
    """
    payload = decode_token(token)

    if payload.type != expected_type:
        raise ValueError(f"Invalid token type. Expected {expected_type.value}, got {payload.type.value}")

    return TokenData(
        user_id=uuid.UUID(payload.sub),
        token_type=payload.type,
        roles=payload.roles,
        organization_id=uuid.UUID(payload.organization_id) if payload.organization_id else None,
        team_id=uuid.UUID(payload.team_id) if payload.team_id else None,
        jti=payload.jti,
    )


def extract_token_from_header(authorization: str) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: The Authorization header value (e.g., "Bearer <token>")

    Returns:
        The extracted JWT token

    Raises:
        ValueError: If header format is invalid
    """
    if not authorization:
        raise ValueError("Authorization header is missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header format. Expected 'Bearer <token>'")

    return parts[1]
