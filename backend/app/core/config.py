"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

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
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sales_os"
    database_url_sync: str = "postgresql://user:password@localhost:5432/sales_os"

    # Security
    secret_key: str = "development-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Email (SMTP)
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@sales-os.com"
    smtp_from_name: str = "Sales OS"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
