"""Application configuration settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Sales OS"
    app_version: str = "0.1.0"
    debug: bool = False

    # Claude API
    claude_api_key: str = Field(default="", description="Claude API key")
    claude_model: str = Field(
        default="claude-sonnet-4-20250514", description="Claude model to use"
    )
    claude_max_tokens: int = Field(default=4096, description="Max tokens for Claude responses")

    # Database
    database_url: str = Field(
        default="sqlite:///./sales_os.db", description="Database connection URL"
    )

    # Security
    jwt_secret: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours

    # HubSpot Integration
    hubspot_api_key: Optional[str] = None
    hubspot_oauth_client_id: Optional[str] = None
    hubspot_oauth_client_secret: Optional[str] = None

    # Avoma Integration
    avoma_api_key: Optional[str] = None

    # Content Generation
    content_max_retries: int = 3
    content_default_brand_voice: str = "professional"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
