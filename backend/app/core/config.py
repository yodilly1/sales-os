"""Application configuration settings."""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Sales OS"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./sales_os.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Claude API
    anthropic_api_key: Optional[str] = None

    # HubSpot
    hubspot_api_key: Optional[str] = None
    hubspot_client_id: Optional[str] = None
    hubspot_client_secret: Optional[str] = None

    # Avoma
    avoma_api_key: Optional[str] = None
    avoma_webhook_secret: Optional[str] = None

    # Authentication
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Export Settings
    export_max_records: int = 10000
    export_temp_dir: str = "/tmp/sales_os_exports"
    export_retention_hours: int = 24

    # Import Settings
    import_max_file_size_mb: int = 50
    import_batch_size: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
