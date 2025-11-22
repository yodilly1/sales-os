"""OAuth2 implementation for external integrations."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import OAuthProvider
from app.core.security import generate_state_token


class OAuthTokenResponse(BaseModel):
    """OAuth token response schema."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    scope: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """OAuth user info schema."""

    provider_user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    raw_data: Dict[str, Any] = {}


class OAuthClient(ABC):
    """Abstract base class for OAuth2 clients."""

    provider: OAuthProvider

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Get the OAuth authorization URL."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthTokenResponse:
        """Exchange authorization code for tokens."""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Refresh an access token."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from the provider."""
        pass

    @abstractmethod
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke an access token."""
        pass


class HubSpotOAuthClient(OAuthClient):
    """OAuth2 client for HubSpot integration."""

    provider = OAuthProvider.HUBSPOT
    authorization_url = "https://app.hubspot.com/oauth/authorize"
    token_url = "https://api.hubapi.com/oauth/v1/token"
    user_info_url = "https://api.hubapi.com/oauth/v1/access-tokens"

    def __init__(self):
        self.client_id = settings.hubspot_client_id
        self.client_secret = settings.hubspot_client_secret
        self.redirect_uri = settings.hubspot_redirect_uri
        self.scopes = settings.hubspot_scopes

    def get_authorization_url(self, state: str) -> str:
        """Get HubSpot OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "state": state,
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokenResponse:
        """Exchange authorization code for HubSpot tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            data = response.json()

            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in"),
            )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Refresh HubSpot access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            data = response.json()

            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in"),
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get HubSpot token/user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.user_info_url}/{access_token}",
            )
            response.raise_for_status()
            data = response.json()

            return OAuthUserInfo(
                provider_user_id=str(data.get("user_id", data.get("hub_id", ""))),
                email=data.get("user"),
                raw_data=data,
            )

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke HubSpot access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/refresh-tokens/{token}".format(
                    token=access_token
                ),
                data={"token": access_token},
            )
            return response.status_code == 200


class AvomaOAuthClient(OAuthClient):
    """OAuth2 client for Avoma integration."""

    provider = OAuthProvider.AVOMA
    base_url = "https://api.avoma.com"
    authorization_url = "https://app.avoma.com/oauth/authorize"
    token_url = "https://api.avoma.com/oauth/token"

    def __init__(self):
        self.client_id = settings.avoma_client_id
        self.client_secret = settings.avoma_client_secret
        self.redirect_uri = settings.avoma_redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Get Avoma OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokenResponse:
        """Exchange authorization code for Avoma tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            data = response.json()

            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in"),
            )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Refresh Avoma access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            data = response.json()

            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in"),
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get Avoma user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return OAuthUserInfo(
                provider_user_id=str(data.get("id", "")),
                email=data.get("email"),
                name=data.get("name"),
                raw_data=data,
            )

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke Avoma access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/revoke",
                json={"token": access_token},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.status_code == 200


def get_oauth_client(provider: OAuthProvider) -> OAuthClient:
    """
    Factory function to get OAuth client by provider.

    Args:
        provider: The OAuth provider

    Returns:
        OAuth client instance

    Raises:
        ValueError: If provider is not supported
    """
    clients = {
        OAuthProvider.HUBSPOT: HubSpotOAuthClient,
        OAuthProvider.AVOMA: AvomaOAuthClient,
    }

    client_class = clients.get(provider)
    if not client_class:
        raise ValueError(f"Unsupported OAuth provider: {provider}")

    return client_class()


class OAuthStateManager:
    """Manager for OAuth state tokens (should use Redis in production)."""

    # In-memory storage for development (use Redis in production)
    _states: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_state(
        cls,
        user_id: uuid.UUID,
        provider: OAuthProvider,
        redirect_uri: Optional[str] = None,
    ) -> str:
        """
        Create and store an OAuth state token.

        Args:
            user_id: The user initiating OAuth
            provider: The OAuth provider
            redirect_uri: Optional custom redirect after OAuth

        Returns:
            Generated state token
        """
        state = generate_state_token()
        cls._states[state] = {
            "user_id": str(user_id),
            "provider": provider.value,
            "redirect_uri": redirect_uri,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return state

    @classmethod
    def verify_state(cls, state: str) -> Optional[Dict[str, Any]]:
        """
        Verify and consume an OAuth state token.

        Args:
            state: The state token to verify

        Returns:
            State data if valid, None otherwise
        """
        state_data = cls._states.pop(state, None)
        if not state_data:
            return None

        # Check expiration (15 minutes)
        created_at = datetime.fromisoformat(state_data["created_at"])
        if datetime.now(timezone.utc) - created_at > timedelta(minutes=15):
            return None

        return state_data

    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Remove expired state tokens.

        Returns:
            Number of removed tokens
        """
        now = datetime.now(timezone.utc)
        expired = []

        for state, data in cls._states.items():
            created_at = datetime.fromisoformat(data["created_at"])
            if now - created_at > timedelta(minutes=15):
                expired.append(state)

        for state in expired:
            del cls._states[state]

        return len(expired)
