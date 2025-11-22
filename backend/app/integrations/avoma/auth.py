"""
Avoma authentication and token management.

Handles OAuth2 token refresh and API key authentication for the Avoma API.
"""

import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.models.avoma import AvomaTokenResponse

logger = logging.getLogger(__name__)


class AvomaAuthError(Exception):
    """Exception raised for Avoma authentication errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AvomaAuthManager:
    """
    Manages authentication and token lifecycle for Avoma API.

    Supports both OAuth2 token-based auth and API key authentication.
    Handles automatic token refresh before expiration.
    """

    AVOMA_AUTH_URL = "https://api.avoma.com/oauth/token"
    TOKEN_REFRESH_BUFFER_SECONDS = 300  # Refresh 5 minutes before expiry

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize the Avoma auth manager.

        Args:
            client_id: OAuth2 client ID for token-based auth
            client_secret: OAuth2 client secret for token-based auth
            api_key: API key for simple authentication
            webhook_secret: Secret for validating webhook signatures
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.webhook_secret = webhook_secret

        # Token state
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # HTTP client for token requests
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def set_tokens(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> None:
        """
        Set the current tokens.

        Args:
            access_token: The OAuth2 access token
            refresh_token: The OAuth2 refresh token (optional)
            expires_in: Token expiration time in seconds (optional)
        """
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        if expires_in:
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire."""
        if not self._access_token or not self._token_expires_at:
            return True

        buffer = timedelta(seconds=self.TOKEN_REFRESH_BUFFER_SECONDS)
        return datetime.now(timezone.utc) >= (self._token_expires_at - buffer)

    async def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            A valid access token string

        Raises:
            AvomaAuthError: If unable to obtain a valid token
        """
        # If using API key auth, return it directly
        if self.api_key:
            return self.api_key

        # Check if we need to refresh
        if self.is_token_expired():
            if self._refresh_token:
                await self.refresh_access_token()
            else:
                raise AvomaAuthError(
                    "Access token expired and no refresh token available",
                    error_code="token_expired",
                )

        if not self._access_token:
            raise AvomaAuthError(
                "No access token available",
                error_code="no_token",
            )

        return self._access_token

    async def refresh_access_token(self) -> AvomaTokenResponse:
        """
        Refresh the access token using the refresh token.

        Returns:
            AvomaTokenResponse with new tokens

        Raises:
            AvomaAuthError: If token refresh fails
        """
        if not self._refresh_token:
            raise AvomaAuthError(
                "No refresh token available",
                error_code="no_refresh_token",
            )

        if not self.client_id or not self.client_secret:
            raise AvomaAuthError(
                "Client credentials required for token refresh",
                error_code="missing_credentials",
            )

        client = await self._get_http_client()

        try:
            response = await client.post(
                self.AVOMA_AUTH_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise AvomaAuthError(
                    f"Token refresh failed: {error_data.get('error_description', response.text)}",
                    error_code=error_data.get("error", "refresh_failed"),
                )

            token_data = response.json()
            token_response = AvomaTokenResponse(**token_data)

            # Update stored tokens
            self.set_tokens(
                access_token=token_response.access_token,
                refresh_token=token_response.refresh_token,
                expires_in=token_response.expires_in,
            )

            logger.info("Successfully refreshed Avoma access token")
            return token_response

        except httpx.RequestError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise AvomaAuthError(
                f"Network error during token refresh: {str(e)}",
                error_code="network_error",
            )

    async def exchange_authorization_code(
        self,
        authorization_code: str,
        redirect_uri: str,
    ) -> AvomaTokenResponse:
        """
        Exchange an authorization code for access and refresh tokens.

        Args:
            authorization_code: The OAuth2 authorization code
            redirect_uri: The redirect URI used in the authorization request

        Returns:
            AvomaTokenResponse with tokens

        Raises:
            AvomaAuthError: If code exchange fails
        """
        if not self.client_id or not self.client_secret:
            raise AvomaAuthError(
                "Client credentials required for code exchange",
                error_code="missing_credentials",
            )

        client = await self._get_http_client()

        try:
            response = await client.post(
                self.AVOMA_AUTH_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise AvomaAuthError(
                    f"Code exchange failed: {error_data.get('error_description', response.text)}",
                    error_code=error_data.get("error", "exchange_failed"),
                )

            token_data = response.json()
            token_response = AvomaTokenResponse(**token_data)

            # Store the tokens
            self.set_tokens(
                access_token=token_response.access_token,
                refresh_token=token_response.refresh_token,
                expires_in=token_response.expires_in,
            )

            logger.info("Successfully exchanged authorization code for tokens")
            return token_response

        except httpx.RequestError as e:
            logger.error(f"Network error during code exchange: {e}")
            raise AvomaAuthError(
                f"Network error during code exchange: {str(e)}",
                error_code="network_error",
            )

    def get_authorization_url(self, redirect_uri: str, state: str, scopes: Optional[list[str]] = None) -> str:
        """
        Generate the OAuth2 authorization URL for user consent.

        Args:
            redirect_uri: The URI to redirect to after authorization
            state: A random state string for CSRF protection
            scopes: List of requested scopes (optional)

        Returns:
            The full authorization URL
        """
        if not self.client_id:
            raise AvomaAuthError(
                "Client ID required for authorization URL",
                error_code="missing_client_id",
            )

        base_url = "https://app.avoma.com/oauth/authorize"
        scope_str = " ".join(scopes) if scopes else "recordings:read transcripts:read meetings:read"

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": scope_str,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify the signature of an incoming webhook request.

        Args:
            payload: The raw request body bytes
            signature: The signature from the X-Avoma-Signature header
            timestamp: The timestamp from the X-Avoma-Timestamp header (optional)

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True

        # If timestamp provided, check it's not too old (prevent replay attacks)
        if timestamp:
            try:
                request_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - request_time) > 300:  # 5 minute tolerance
                    logger.warning("Webhook timestamp too old, possible replay attack")
                    return False
            except ValueError:
                logger.warning("Invalid webhook timestamp format")
                return False

        # Compute expected signature
        if timestamp:
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        else:
            signed_payload = payload.decode("utf-8")

        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary of headers to include in API requests

        Note:
            This is a synchronous method that uses cached tokens.
            For async token refresh, call get_access_token() first.
        """
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}

        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}

        return {}
