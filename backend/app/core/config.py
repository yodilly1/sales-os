"""
Application configuration settings.

Uses Pydantic settings for environment variable management.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Sales OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/sales_os"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Search settings
    SEARCH_MAX_RESULTS: int = 100
    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    SEARCH_HISTORY_LIMIT: int = 50  # Max recent searches per user
    SEARCH_SUGGESTION_LIMIT: int = 10
    SEARCH_MIN_QUERY_LENGTH: int = 2
    SEARCH_TIMEOUT_MS: int = 500  # Target response time

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
