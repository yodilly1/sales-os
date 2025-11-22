"""API Key management utilities."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.models.api_key import APIKey


class APIKeyManager:
    """Manager for API key operations."""

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: uuid.UUID,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.

        Args:
            db: Database session
            user_id: Owner user ID
            name: Key name/description
            scopes: Optional list of allowed scopes
            expires_at: Optional expiration datetime

        Returns:
            Tuple of (APIKey model, raw_key)
            Note: raw_key is only returned once and must be stored by the user
        """
        # Generate the raw key
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        key_prefix = raw_key[:12] + "..."

        # Create the API key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes or [],
            expires_at=expires_at,
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key, raw_key

    @staticmethod
    async def verify_and_get_key(
        db: AsyncSession,
        raw_key: str,
    ) -> Optional[APIKey]:
        """
        Verify an API key and return the model if valid.

        Args:
            db: Database session
            raw_key: The raw API key to verify

        Returns:
            APIKey model if valid, None otherwise
        """
        key_hash = hash_api_key(raw_key)

        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check if expired
        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            return None

        # Update last used timestamp
        await db.execute(
            update(APIKey)
            .where(APIKey.id == api_key.id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await db.commit()

        return api_key

    @staticmethod
    async def get_user_api_keys(
        db: AsyncSession,
        user_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> List[APIKey]:
        """
        Get all API keys for a user.

        Args:
            db: Database session
            user_id: User ID
            include_inactive: Include revoked/inactive keys

        Returns:
            List of APIKey models
        """
        query = select(APIKey).where(APIKey.user_id == user_id)

        if not include_inactive:
            query = query.where(APIKey.is_active == True)

        result = await db.execute(query.order_by(APIKey.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def revoke_api_key(
        db: AsyncSession,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Revoke an API key.

        Args:
            db: Database session
            key_id: API key ID
            user_id: Owner user ID (for authorization)

        Returns:
            True if revoked, False if not found
        """
        result = await db.execute(
            update(APIKey)
            .where(
                APIKey.id == key_id,
                APIKey.user_id == user_id,
            )
            .values(is_active=False)
        )
        await db.commit()

        return result.rowcount > 0

    @staticmethod
    async def delete_api_key(
        db: AsyncSession,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Permanently delete an API key.

        Args:
            db: Database session
            key_id: API key ID
            user_id: Owner user ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id,
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        await db.delete(api_key)
        await db.commit()

        return True

    @staticmethod
    def has_scope(api_key: APIKey, required_scope: str) -> bool:
        """
        Check if an API key has a required scope.

        Args:
            api_key: The API key model
            required_scope: The scope to check

        Returns:
            True if scope is present or no scopes defined (full access)
        """
        # No scopes means full access
        if not api_key.scopes:
            return True

        # Check for wildcard
        if "*" in api_key.scopes:
            return True

        # Check for exact match or prefix match
        for scope in api_key.scopes:
            if scope == required_scope:
                return True
            # Support wildcard suffix (e.g., "read:*" matches "read:users")
            if scope.endswith("*") and required_scope.startswith(scope[:-1]):
                return True

        return False
