"""Application configuration and settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
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
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", alias="ENV")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sales_os",
        alias="DATABASE_URL",
    )

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="change-me-in-production-use-strong-secret-key",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # OAuth2 - HubSpot
    hubspot_client_id: Optional[str] = None
    hubspot_client_secret: Optional[str] = None
    hubspot_redirect_uri: str = "http://localhost:8000/api/auth/hubspot/callback"
    hubspot_scopes: str = "crm.objects.contacts.read crm.objects.contacts.write crm.objects.deals.read crm.objects.deals.write"

    # OAuth2 - Avoma
    avoma_client_id: Optional[str] = None
    avoma_client_secret: Optional[str] = None
    avoma_redirect_uri: str = "http://localhost:8000/api/auth/avoma/callback"
    avoma_api_key: Optional[str] = None

    # API Keys
    api_key_prefix: str = "sk_"
    api_key_length: int = 32

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Security
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]

    # Audit Logging
    audit_log_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
