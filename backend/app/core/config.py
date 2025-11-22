"""Application configuration settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "sales-os"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sales_os"

    # HubSpot Integration
    hubspot_api_key: Optional[str] = None
    hubspot_access_token: Optional[str] = None

    # Enrichment Service Providers
    clearbit_api_key: Optional[str] = None
    apollo_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    linkedin_api_key: Optional[str] = None

    # News API
    news_api_key: Optional[str] = None

    # Rate Limiting
    rate_limit_per_minute: int = 60
    enrichment_batch_size: int = 50

    # Claude AI
    anthropic_api_key: Optional[str] = None

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
