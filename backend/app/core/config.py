"""
Application Configuration

This module provides centralized configuration management using Pydantic settings.
Environment variables are loaded from .env files and validated at startup.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Sales OS"
    app_version: str = "0.1.0"
    debug: bool = False

    # HubSpot Configuration
    hubspot_api_key: str | None = Field(None, description="HubSpot private app API key")
    hubspot_client_id: str | None = Field(None, description="HubSpot OAuth client ID")
    hubspot_client_secret: str | None = Field(None, description="HubSpot OAuth client secret")
    hubspot_redirect_uri: str = Field(
        "http://localhost:8000/api/hubspot/oauth/callback",
        description="HubSpot OAuth redirect URI",
    )
    hubspot_base_url: str = Field(
        "https://api.hubapi.com",
        description="HubSpot API base URL",
    )
    hubspot_rate_limit_requests: int = Field(
        100,
        description="Max requests per rate limit window",
    )
    hubspot_rate_limit_window: int = Field(
        10,
        description="Rate limit window in seconds",
    )

    # Database
    database_url: str = Field(
        "postgresql://postgres:postgres@localhost:5432/sales_os",
        description="PostgreSQL connection string",
    )

    # Redis (for rate limiting and caching)
    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis connection string",
    )

    # JWT Authentication
    jwt_secret_key: str = Field(
        "your-secret-key-change-in-production",
        description="JWT signing secret",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Claude AI
    anthropic_api_key: str | None = Field(None, description="Anthropic API key")

    # Avoma Integration
    avoma_api_key: str | None = Field(None, description="Avoma API key")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
