"""
Application Configuration

Manages application settings using Pydantic for validation
and environment variable loading.
"""

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application Settings
    app_name: str = "Sales OS API"
    app_version: str = "1.0.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # API Settings
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sales_os"
    database_url_sync: str = "postgresql://user:password@localhost:5432/sales_os"

    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Claude AI
    anthropic_api_key: str = ""
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.7

    # External Services
    hubspot_client_id: str = ""
    hubspot_client_secret: str = ""
    hubspot_api_key: str = ""
    avoma_api_key: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance loaded from environment
    """
    return Settings()


settings = get_settings()
