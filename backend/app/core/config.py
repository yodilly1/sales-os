"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Sales OS"
    FASTAPI_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sales_os.db"

    # Activity Logging
    ACTIVITY_LOG_ENABLED: bool = True
    ACTIVITY_LOG_RETENTION_DAYS: int = 90
    ACTIVITY_LOG_BATCH_SIZE: int = 100

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.FASTAPI_ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.FASTAPI_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
