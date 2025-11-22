"""
Application configuration management.

Uses pydantic-settings for environment variable loading
and validation of configuration values.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Environment variables are case-insensitive.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field("Sales OS", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Enable debug mode")
    environment: str = Field("development", description="Environment (development, staging, production)")

    # API settings
    api_prefix: str = Field("/api", description="API route prefix")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Avoma integration settings
    avoma_client_id: Optional[str] = Field(None, description="Avoma OAuth client ID")
    avoma_client_secret: Optional[str] = Field(None, description="Avoma OAuth client secret")
    avoma_api_key: Optional[str] = Field(None, description="Avoma API key (alternative to OAuth)")
    avoma_webhook_secret: Optional[str] = Field(None, description="Avoma webhook signing secret")
    avoma_redirect_uri: str = Field(
        "http://localhost:8000/api/avoma/oauth/callback",
        description="Avoma OAuth redirect URI",
    )

    # HubSpot integration settings (for future use)
    hubspot_client_id: Optional[str] = Field(None, description="HubSpot OAuth client ID")
    hubspot_client_secret: Optional[str] = Field(None, description="HubSpot OAuth client secret")
    hubspot_api_key: Optional[str] = Field(None, description="HubSpot API key")

    # Database settings
    database_url: str = Field(
        "sqlite:///./sales_os.db",
        description="Database connection URL",
    )

    # Claude API settings
    claude_api_key: Optional[str] = Field(None, description="Claude API key for AI features")
    claude_model: str = Field("claude-sonnet-4-20250514", description="Claude model to use")

    # JWT/Auth settings
    jwt_secret_key: str = Field(
        "change-me-in-production",
        description="Secret key for JWT signing",
    )
    jwt_algorithm: str = Field("HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(60, description="JWT token expiration in minutes")

    # Logging settings
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def get_avoma_credentials(self) -> dict:
        """Get Avoma credentials as a dictionary."""
        return {
            "client_id": self.avoma_client_id,
            "client_secret": self.avoma_client_secret,
            "api_key": self.avoma_api_key,
            "webhook_secret": self.avoma_webhook_secret,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns a cached Settings instance for efficient access
    throughout the application.
    """
    return Settings()
