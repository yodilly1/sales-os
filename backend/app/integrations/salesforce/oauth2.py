"""
Salesforce OAuth2 authentication handler.

Supports:
- OAuth2 Authorization Code flow
- Token refresh
- Sandbox vs Production environments
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx

from backend.app.models.salesforce import (
    SalesforceAPIError,
    SalesforceAuthConfig,
    SalesforceCredentials,
    SalesforceEnvironment,
    SalesforceTokenResponse,
)


class SalesforceOAuth2Handler:
    """Handles OAuth2 authentication with Salesforce."""

    # OAuth2 scopes for Salesforce
    DEFAULT_SCOPES = [
        "api",  # Access REST API
        "refresh_token",  # Allow token refresh
        "offline_access",  # Access data while user is offline
    ]

    def __init__(self, config: SalesforceAuthConfig):
        """
        Initialize the OAuth2 handler.

        Args:
            config: OAuth2 configuration including client credentials and environment
        """
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        prompt: str = "consent",
    ) -> str:
        """
        Generate the OAuth2 authorization URL.

        Args:
            state: Optional state parameter for CSRF protection
            scopes: OAuth2 scopes to request
            prompt: OAuth2 prompt parameter (consent, login, none)

        Returns:
            The full authorization URL to redirect users to
        """
        scopes = scopes or self.DEFAULT_SCOPES

        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scopes),
            "prompt": prompt,
        }

        if state:
            params["state"] = state

        return f"{self.config.auth_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
    ) -> SalesforceTokenResponse:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: The authorization code from OAuth2 callback

        Returns:
            Token response containing access_token, refresh_token, and instance_url

        Raises:
            SalesforceAPIError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
            "code": authorization_code,
        }

        response = await self.http_client.post(
            self.config.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("error_description", "Token exchange failed"),
                status_code=response.status_code,
            )

        token_data = response.json()
        return SalesforceTokenResponse(**token_data)

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> SalesforceTokenResponse:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token from initial authentication

        Returns:
            New token response with fresh access_token

        Raises:
            SalesforceAPIError: If token refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        response = await self.http_client.post(
            self.config.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            error_data = response.json()
            raise SalesforceAPIError(
                message=error_data.get("error_description", "Token refresh failed"),
                status_code=response.status_code,
            )

        token_data = response.json()
        return SalesforceTokenResponse(**token_data)

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke an access or refresh token.

        Args:
            token: The token to revoke

        Returns:
            True if revocation was successful

        Raises:
            SalesforceAPIError: If revocation fails
        """
        base_url = (
            "https://test.salesforce.com"
            if self.config.environment == SalesforceEnvironment.SANDBOX
            else "https://login.salesforce.com"
        )
        revoke_url = f"{base_url}/services/oauth2/revoke"

        response = await self.http_client.post(
            revoke_url,
            data={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise SalesforceAPIError(
                message="Token revocation failed",
                status_code=response.status_code,
            )

        return True

    async def get_user_info(
        self,
        access_token: str,
        instance_url: str,
    ) -> dict:
        """
        Get information about the authenticated user.

        Args:
            access_token: Valid access token
            instance_url: Salesforce instance URL

        Returns:
            User info dictionary

        Raises:
            SalesforceAPIError: If request fails
        """
        response = await self.http_client.get(
            f"{instance_url}/services/oauth2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise SalesforceAPIError(
                message="Failed to get user info",
                status_code=response.status_code,
            )

        return response.json()

    def create_credentials(
        self,
        token_response: SalesforceTokenResponse,
        expires_in_seconds: int = 7200,  # Default 2 hours
    ) -> SalesforceCredentials:
        """
        Create credentials object from token response.

        Args:
            token_response: Token response from OAuth2 flow
            expires_in_seconds: Token expiration time in seconds

        Returns:
            SalesforceCredentials object
        """
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

        # Extract org ID from the id URL if available
        org_id = None
        if token_response.id:
            # ID URL format: https://login.salesforce.com/id/00Dxx0000001gPLEAY/005xx000001Sv6AAAS
            parts = token_response.id.rstrip("/").split("/")
            if len(parts) >= 2:
                org_id = parts[-2]

        return SalesforceCredentials(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token or "",
            instance_url=token_response.instance_url,
            environment=self.config.environment,
            expires_at=expires_at,
            org_id=org_id,
        )

    def is_token_expired(
        self,
        credentials: SalesforceCredentials,
        buffer_seconds: int = 300,  # 5 minute buffer
    ) -> bool:
        """
        Check if the access token is expired or about to expire.

        Args:
            credentials: Current credentials
            buffer_seconds: Buffer time before actual expiration

        Returns:
            True if token is expired or will expire within buffer period
        """
        if not credentials.expires_at:
            # If no expiration time, assume expired to be safe
            return True

        expiry_threshold = datetime.now(timezone.utc) + timedelta(seconds=buffer_seconds)
        return credentials.expires_at <= expiry_threshold


class SalesforceTokenManager:
    """
    Manages Salesforce tokens with automatic refresh.

    This class provides a higher-level interface for token management,
    handling automatic refresh and caching.
    """

    def __init__(
        self,
        oauth_handler: SalesforceOAuth2Handler,
        credentials: SalesforceCredentials,
    ):
        """
        Initialize the token manager.

        Args:
            oauth_handler: OAuth2 handler for token operations
            credentials: Current credentials
        """
        self.oauth_handler = oauth_handler
        self._credentials = credentials
        self._lock = None  # Will be initialized on first use in async context

    @property
    def credentials(self) -> SalesforceCredentials:
        """Get current credentials."""
        return self._credentials

    @property
    def instance_url(self) -> str:
        """Get the Salesforce instance URL."""
        return self._credentials.instance_url

    async def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            SalesforceAPIError: If token refresh fails
        """
        if self.oauth_handler.is_token_expired(self._credentials):
            await self._refresh_token()

        return self._credentials.access_token

    async def _refresh_token(self) -> None:
        """Refresh the access token."""
        token_response = await self.oauth_handler.refresh_access_token(
            self._credentials.refresh_token
        )

        # Update credentials with new access token
        self._credentials = SalesforceCredentials(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token or self._credentials.refresh_token,
            instance_url=token_response.instance_url,
            environment=self._credentials.environment,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
            org_id=self._credentials.org_id,
        )

    async def close(self) -> None:
        """Close underlying resources."""
        await self.oauth_handler.close()
