"""Application configuration using Pydantic Settings."""

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
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sales_os",
        alias="DATABASE_URL",
    )

    # Redis (for queues and caching)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # S3 Storage Configuration
    s3_endpoint_url: Optional[str] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_access_key_id: str = Field(default="", alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(default="", alias="S3_SECRET_ACCESS_KEY")
    s3_bucket_name: str = Field(default="sales-os-files", alias="S3_BUCKET_NAME")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")

    # File Upload Settings
    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")
    chunk_size_mb: int = Field(default=5, alias="CHUNK_SIZE_MB")
    upload_temp_dir: str = Field(default="/tmp/sales-os-uploads", alias="UPLOAD_TEMP_DIR")
    file_retention_days: int = Field(default=30, alias="FILE_RETENTION_DAYS")
    temp_file_expiry_hours: int = Field(default=24, alias="TEMP_FILE_EXPIRY_HOURS")

    # Allowed File Types
    allowed_transcript_extensions: list[str] = [".txt", ".vtt", ".srt", ".json"]
    allowed_data_extensions: list[str] = [".csv", ".xlsx"]
    allowed_asset_extensions: list[str] = [".png", ".jpg", ".jpeg", ".pdf"]

    # JWT Settings (for file access tokens)
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    file_access_token_expire_minutes: int = 60

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def chunk_size_bytes(self) -> int:
        """Chunk size in bytes."""
        return self.chunk_size_mb * 1024 * 1024

    @property
    def all_allowed_extensions(self) -> list[str]:
        """All allowed file extensions combined."""
        return (
            self.allowed_transcript_extensions
            + self.allowed_data_extensions
            + self.allowed_asset_extensions
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
