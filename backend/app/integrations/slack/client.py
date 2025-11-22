"""
Slack API client for Sales OS.

This client handles all direct interactions with the Slack API including:
- OAuth2 token exchange
- Sending messages and notifications
- Managing conversations
- User lookups
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Optional

import httpx

from app.integrations.slack.config import SlackSettings, get_slack_settings
from app.models.slack import (
    SlackNotification,
    SlackNotificationResult,
    SlackOAuthTokenResponse,
    SlackWorkspaceConnection,
)

logger = logging.getLogger(__name__)


class SlackAPIError(Exception):
    """Exception raised for Slack API errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class SlackClient:
    """
    Client for interacting with the Slack API.

    Handles authentication, message sending, and other Slack operations.
    """

    BASE_URL = "https://slack.com/api"

    def __init__(
        self,
        settings: Optional[SlackSettings] = None,
        bot_token: Optional[str] = None,
    ):
        """
        Initialize the Slack client.

        Args:
            settings: Slack settings instance. If None, loads from environment.
            bot_token: Override bot token. Useful for multi-workspace support.
        """
        self.settings = settings or get_slack_settings()
        self._bot_token = bot_token or self.settings.bot_token
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.settings.api_timeout_seconds,
                headers=self._get_default_headers(),
            )
        return self._http_client

    def _get_default_headers(self) -> dict:
        """Get default headers for API requests."""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self._bot_token:
            headers["Authorization"] = f"Bearer {self._bot_token}"
        return headers

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # === OAuth Methods ===

    async def exchange_oauth_code(self, code: str) -> SlackOAuthTokenResponse:
        """
        Exchange an OAuth authorization code for access tokens.

        Args:
            code: The authorization code from Slack OAuth redirect.

        Returns:
            SlackOAuthTokenResponse with access tokens and workspace info.

        Raises:
            SlackAPIError: If the token exchange fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/oauth.v2.access",
                data={
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                    "code": code,
                    "redirect_uri": self.settings.oauth_redirect_uri,
                },
            )
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                logger.error(f"OAuth token exchange failed: {error}")
                raise SlackAPIError(f"OAuth failed: {error}", error_code=error)

            return SlackOAuthTokenResponse(**data)

    def create_workspace_connection(
        self,
        token_response: SlackOAuthTokenResponse,
        organization_id: Optional[str] = None,
    ) -> SlackWorkspaceConnection:
        """
        Create a workspace connection from OAuth response.

        Args:
            token_response: The OAuth token response from Slack.
            organization_id: The Sales OS organization ID to associate.

        Returns:
            SlackWorkspaceConnection object.
        """
        return SlackWorkspaceConnection(
            team_id=token_response.team.get("id", ""),
            team_name=token_response.team.get("name", ""),
            bot_user_id=token_response.bot_user_id,
            bot_access_token=token_response.access_token,
            app_id=token_response.app_id,
            scopes=token_response.scope.split(","),
            installing_user_id=token_response.authed_user.get("id", ""),
            organization_id=organization_id,
        )

    # === Message Methods ===

    async def send_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict]] = None,
        thread_ts: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
        unfurl_links: bool = True,
        unfurl_media: bool = True,
    ) -> SlackNotificationResult:
        """
        Send a message to a Slack channel or DM.

        Args:
            channel: Channel ID or user ID for DM.
            text: Plain text message (required for notifications).
            blocks: Block Kit blocks for rich formatting.
            thread_ts: Thread timestamp to reply in thread.
            attachments: Legacy attachments.
            unfurl_links: Whether to unfurl URLs.
            unfurl_media: Whether to unfurl media.

        Returns:
            SlackNotificationResult with message details.
        """
        payload: dict[str, Any] = {
            "channel": channel,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
        }

        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if attachments:
            payload["attachments"] = attachments

        response = await self.http_client.post(
            f"{self.BASE_URL}/chat.postMessage",
            json=payload,
        )
        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            logger.error(f"Failed to send message: {error}")
            return SlackNotificationResult(ok=False, error=error)

        return SlackNotificationResult(
            ok=True,
            channel=data.get("channel"),
            ts=data.get("ts"),
            message=data.get("message"),
        )

    async def send_notification(
        self,
        notification: SlackNotification,
    ) -> SlackNotificationResult:
        """
        Send a structured notification to Slack.

        Args:
            notification: The notification to send.

        Returns:
            SlackNotificationResult with delivery status.
        """
        target = notification.target
        channel = target.channel_id or target.user_id

        if not channel:
            return SlackNotificationResult(
                ok=False,
                error="No channel or user specified for notification",
            )

        return await self.send_message(
            channel=channel,
            text=notification.message,
            blocks=notification.blocks,
            thread_ts=target.thread_ts,
            attachments=notification.attachments,
        )

    async def send_dm(
        self,
        user_id: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict]] = None,
    ) -> SlackNotificationResult:
        """
        Send a direct message to a user.

        Args:
            user_id: Slack user ID.
            text: Plain text message.
            blocks: Block Kit blocks.

        Returns:
            SlackNotificationResult with delivery status.
        """
        # First, open a DM conversation
        open_response = await self.http_client.post(
            f"{self.BASE_URL}/conversations.open",
            json={"users": user_id},
        )
        open_data = open_response.json()

        if not open_data.get("ok"):
            error = open_data.get("error", "unknown_error")
            logger.error(f"Failed to open DM: {error}")
            return SlackNotificationResult(ok=False, error=error)

        channel_id = open_data["channel"]["id"]
        return await self.send_message(channel=channel_id, text=text, blocks=blocks)

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict]] = None,
    ) -> SlackNotificationResult:
        """
        Update an existing message.

        Args:
            channel: Channel containing the message.
            ts: Timestamp of the message to update.
            text: New text content.
            blocks: New Block Kit blocks.

        Returns:
            SlackNotificationResult with update status.
        """
        payload: dict[str, Any] = {"channel": channel, "ts": ts}
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks

        response = await self.http_client.post(
            f"{self.BASE_URL}/chat.update",
            json=payload,
        )
        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            logger.error(f"Failed to update message: {error}")
            return SlackNotificationResult(ok=False, error=error)

        return SlackNotificationResult(
            ok=True,
            channel=data.get("channel"),
            ts=data.get("ts"),
        )

    async def delete_message(self, channel: str, ts: str) -> bool:
        """
        Delete a message.

        Args:
            channel: Channel containing the message.
            ts: Timestamp of the message to delete.

        Returns:
            True if deleted successfully.
        """
        response = await self.http_client.post(
            f"{self.BASE_URL}/chat.delete",
            json={"channel": channel, "ts": ts},
        )
        data = response.json()
        return data.get("ok", False)

    # === User Methods ===

    async def get_user_info(self, user_id: str) -> Optional[dict]:
        """
        Get information about a Slack user.

        Args:
            user_id: Slack user ID.

        Returns:
            User info dict or None if not found.
        """
        response = await self.http_client.get(
            f"{self.BASE_URL}/users.info",
            params={"user": user_id},
        )
        data = response.json()

        if not data.get("ok"):
            logger.warning(f"Failed to get user info: {data.get('error')}")
            return None

        return data.get("user")

    async def lookup_user_by_email(self, email: str) -> Optional[dict]:
        """
        Look up a Slack user by email address.

        Args:
            email: Email address to look up.

        Returns:
            User info dict or None if not found.
        """
        response = await self.http_client.get(
            f"{self.BASE_URL}/users.lookupByEmail",
            params={"email": email},
        )
        data = response.json()

        if not data.get("ok"):
            # User not found is common, don't log as error
            return None

        return data.get("user")

    # === Channel Methods ===

    async def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100,
    ) -> list[dict]:
        """
        List channels the bot has access to.

        Args:
            types: Comma-separated channel types.
            limit: Maximum number of channels to return.

        Returns:
            List of channel objects.
        """
        response = await self.http_client.get(
            f"{self.BASE_URL}/conversations.list",
            params={"types": types, "limit": limit},
        )
        data = response.json()

        if not data.get("ok"):
            logger.error(f"Failed to list channels: {data.get('error')}")
            return []

        return data.get("channels", [])

    async def join_channel(self, channel_id: str) -> bool:
        """
        Join a public channel.

        Args:
            channel_id: Channel ID to join.

        Returns:
            True if joined successfully.
        """
        response = await self.http_client.post(
            f"{self.BASE_URL}/conversations.join",
            json={"channel": channel_id},
        )
        data = response.json()
        return data.get("ok", False)

    # === Response URL Methods ===

    async def respond_to_url(
        self,
        response_url: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict]] = None,
        replace_original: bool = False,
        delete_original: bool = False,
        response_type: str = "ephemeral",
    ) -> bool:
        """
        Send a response to a Slack response URL.

        Used for responding to slash commands and interactive messages.

        Args:
            response_url: The response URL from Slack.
            text: Plain text response.
            blocks: Block Kit blocks.
            replace_original: Whether to replace the original message.
            delete_original: Whether to delete the original message.
            response_type: 'ephemeral' or 'in_channel'.

        Returns:
            True if response was sent successfully.
        """
        payload: dict[str, Any] = {"response_type": response_type}
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks
        if replace_original:
            payload["replace_original"] = True
        if delete_original:
            payload["delete_original"] = True

        async with httpx.AsyncClient() as client:
            response = await client.post(response_url, json=payload)
            return response.status_code == 200

    # === Signature Verification ===

    def verify_signature(
        self,
        signature: str,
        timestamp: str,
        body: bytes,
    ) -> bool:
        """
        Verify a Slack request signature.

        Args:
            signature: The X-Slack-Signature header value.
            timestamp: The X-Slack-Request-Timestamp header value.
            body: The raw request body.

        Returns:
            True if the signature is valid.
        """
        # Check timestamp is recent (within 5 minutes)
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > 300:
                logger.warning("Slack request timestamp too old")
                return False
        except ValueError:
            return False

        # Compute expected signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected_sig = (
            "v0="
            + hmac.new(
                self.settings.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        return hmac.compare_digest(expected_sig, signature)


# === Factory Functions ===


def create_client(
    bot_token: Optional[str] = None,
    settings: Optional[SlackSettings] = None,
) -> SlackClient:
    """
    Create a Slack client instance.

    Args:
        bot_token: Optional bot token override.
        settings: Optional settings override.

    Returns:
        Configured SlackClient instance.
    """
    return SlackClient(settings=settings, bot_token=bot_token)


def create_client_for_workspace(
    workspace: SlackWorkspaceConnection,
) -> SlackClient:
    """
    Create a Slack client for a specific workspace.

    Args:
        workspace: The workspace connection with credentials.

    Returns:
        SlackClient configured for the workspace.
    """
    return SlackClient(bot_token=workspace.bot_access_token)
