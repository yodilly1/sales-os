"""Authentication service."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.password import hash_password, verify_password
from app.core.auth.tokens import create_token_pair, TokenPair, verify_token
from app.core.constants import TokenType, UserRole
from app.models.user import User


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        organization_id: Optional[uuid.UUID] = None,
        team_id: Optional[uuid.UUID] = None,
    ) -> User:
        """
        Register a new user.

        Args:
            email: User email
            username: Username
            password: Plain text password
            full_name: Optional full name
            roles: Optional roles (defaults to REP)
            organization_id: Optional organization ID
            team_id: Optional team ID

        Returns:
            Created User model

        Raises:
            ValueError: If email or username already exists
        """
        # Check if email exists
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Check if username exists
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        if result.scalar_one_or_none():
            raise ValueError("Username already taken")

        # Create user
        user = User(
            email=email.lower(),
            username=username.lower(),
            password_hash=hash_password(password),
            full_name=full_name,
            roles=roles or [UserRole.REP.value],
            organization_id=organization_id,
            team_id=team_id,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate(
        self,
        email_or_username: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate a user by email/username and password.

        Args:
            email_or_username: Email or username
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        # Try email first
        result = await self.db.execute(
            select(User).where(User.email == email_or_username.lower())
        )
        user = result.scalar_one_or_none()

        # Try username if email not found
        if not user:
            result = await self.db.execute(
                select(User).where(User.username == email_or_username.lower())
            )
            user = result.scalar_one_or_none()

        if not user:
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            return None

        # Check if user is active
        if not user.is_active:
            return None

        return user

    async def login(
        self,
        email_or_username: str,
        password: str,
    ) -> Optional[tuple[User, TokenPair]]:
        """
        Login a user and return tokens.

        Args:
            email_or_username: Email or username
            password: Plain text password

        Returns:
            Tuple of (User, TokenPair) if successful, None otherwise
        """
        user = await self.authenticate(email_or_username, password)
        if not user:
            return None

        # Update last login
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=datetime.now(timezone.utc))
        )
        await self.db.commit()

        # Create tokens
        token_pair = create_token_pair(
            user_id=user.id,
            roles=user.roles,
            organization_id=user.organization_id,
            team_id=user.team_id,
        )

        return user, token_pair

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> Optional[TokenPair]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            New TokenPair if successful, None otherwise
        """
        try:
            token_data = verify_token(refresh_token, TokenType.REFRESH)
        except Exception:
            return None

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        # Create new tokens
        return create_token_pair(
            user_id=user.id,
            roles=user.roles,
            organization_id=user.organization_id,
            team_id=user.team_id,
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if successful, False if current password incorrect
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            return False

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                password_hash=hash_password(new_password),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.commit()

        return True

    async def update_user(
        self,
        user_id: uuid.UUID,
        **updates,
    ) -> Optional[User]:
        """
        Update user fields.

        Args:
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated User if found, None otherwise
        """
        # Filter allowed updates
        allowed_fields = {"full_name", "is_active", "is_verified", "roles", "team_id"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return await self.get_user_by_id(user_id)

        filtered_updates["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(User).where(User.id == user_id).values(**filtered_updates)
        )
        await self.db.commit()

        return await self.get_user_by_id(user_id)
