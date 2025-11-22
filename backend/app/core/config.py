"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Sales OS"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sales_os"
    database_url_sync: str = "postgresql://user:password@localhost:5432/sales_os"

    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # External Services
    claude_api_key: str = ""
    hubspot_client_id: str = ""
    hubspot_client_secret: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
