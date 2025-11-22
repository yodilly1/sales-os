"""
Slack integration configuration.

Loads Slack app credentials and settings from environment variables.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SlackSettings(BaseSettings):
    """Slack integration settings loaded from environment."""

    # Core Slack App Credentials
    client_id: str = Field(
        default="",
        description="Slack App Client ID",
    )
    client_secret: str = Field(
        default="",
        description="Slack App Client Secret",
    )
    signing_secret: str = Field(
        default="",
        description="Slack Request Signing Secret",
    )
    bot_token: Optional[str] = Field(
        default=None,
        description="Bot User OAuth Token (for single workspace installs)",
    )

    # OAuth Configuration
    oauth_redirect_uri: str = Field(
        default="http://localhost:8000/api/slack/oauth/callback",
        description="OAuth redirect URI",
    )
    oauth_scopes: str = Field(
        default=(
            "app_mentions:read,"
            "channels:history,"
            "channels:read,"
            "chat:write,"
            "commands,"
            "im:history,"
            "im:read,"
            "im:write,"
            "users:read,"
            "users:read.email"
        ),
        description="Comma-separated list of OAuth scopes",
    )

    # App Configuration
    app_name: str = Field(
        default="Sales OS",
        description="Display name for the Slack app",
    )
    default_channel: Optional[str] = Field(
        default=None,
        description="Default channel ID for notifications",
    )

    # Feature Flags
    enable_slash_commands: bool = Field(
        default=True,
        description="Enable slash command handling",
    )
    enable_interactive_messages: bool = Field(
        default=True,
        description="Enable interactive message components",
    )
    enable_dm_notifications: bool = Field(
        default=True,
        description="Enable direct message notifications",
    )

    # Rate Limiting
    rate_limit_per_second: int = Field(
        default=1,
        description="Maximum API calls per second",
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Maximum burst size for rate limiting",
    )

    # Timeouts
    api_timeout_seconds: int = Field(
        default=30,
        description="Timeout for Slack API calls",
    )
    webhook_response_timeout_seconds: int = Field(
        default=3,
        description="Max time to respond to webhooks (Slack requires < 3s)",
    )

    class Config:
        env_prefix = "SLACK_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def oauth_scope_list(self) -> list[str]:
        """Get OAuth scopes as a list."""
        return [s.strip() for s in self.oauth_scopes.split(",") if s.strip()]

    @property
    def is_configured(self) -> bool:
        """Check if minimum required credentials are configured."""
        return bool(self.client_id and self.client_secret and self.signing_secret)

    def get_oauth_install_url(self, state: Optional[str] = None) -> str:
        """Generate the OAuth installation URL for the Slack app."""
        base_url = "https://slack.com/oauth/v2/authorize"
        params = [
            f"client_id={self.client_id}",
            f"scope={self.oauth_scopes}",
            f"redirect_uri={self.oauth_redirect_uri}",
        ]
        if state:
            params.append(f"state={state}")
        return f"{base_url}?{'&'.join(params)}"


@lru_cache()
def get_slack_settings() -> SlackSettings:
    """
    Get cached Slack settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return SlackSettings()


# Convenience function for quick access to settings
def get_settings() -> SlackSettings:
    """Alias for get_slack_settings()."""
    return get_slack_settings()
