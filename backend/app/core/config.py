"""
Configuration Settings for Sales OS

Central configuration management using Pydantic settings.
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class EmailSettings(BaseSettings):
    """Email service configuration."""

    # Provider selection
    EMAIL_PROVIDER: str = Field(
        default="sendgrid",
        description="Email provider: 'sendgrid' or 'ses'"
    )

    # SendGrid settings
    SENDGRID_API_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid API key"
    )
    SENDGRID_WEBHOOK_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid webhook verification key"
    )

    # AWS SES settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS access key ID for SES"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS secret access key for SES"
    )
    AWS_SES_REGION: str = Field(
        default="us-east-1",
        description="AWS region for SES"
    )
    AWS_SES_CONFIGURATION_SET: Optional[str] = Field(
        default=None,
        description="SES configuration set for tracking"
    )

    # Default sender settings
    EMAIL_FROM_ADDRESS: str = Field(
        default="noreply@example.com",
        description="Default from email address"
    )
    EMAIL_FROM_NAME: str = Field(
        default="Sales OS",
        description="Default from name"
    )
    EMAIL_REPLY_TO: Optional[str] = Field(
        default=None,
        description="Default reply-to address"
    )

    # Tracking settings
    EMAIL_TRACKING_BASE_URL: str = Field(
        default="https://api.example.com",
        description="Base URL for tracking endpoints"
    )
    EMAIL_TRACK_OPENS: bool = Field(
        default=True,
        description="Enable open tracking by default"
    )
    EMAIL_TRACK_CLICKS: bool = Field(
        default=True,
        description="Enable click tracking by default"
    )

    # Security settings
    EMAIL_UNSUBSCRIBE_SECRET: str = Field(
        default="change-me-in-production",
        description="Secret key for unsubscribe token generation"
    )

    # Rate limiting
    EMAIL_RATE_LIMIT_PER_SECOND: int = Field(
        default=10,
        description="Maximum emails per second"
    )
    EMAIL_BATCH_SIZE: int = Field(
        default=100,
        description="Maximum batch size for bulk sending"
    )

    class Config:
        env_prefix = ""
        case_sensitive = True


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    APP_NAME: str = Field(default="Sales OS", description="Application name")
    APP_ENV: str = Field(default="development", description="Environment")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # API
    API_V1_PREFIX: str = Field(default="/api/v1", description="API prefix")
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Database (placeholder for AGENT-011)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )

    # Redis (for caching/queues)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )

    # Email settings
    email: EmailSettings = Field(default_factory=EmailSettings)

    class Config:
        env_prefix = ""
        case_sensitive = True
        env_nested_delimiter = "__"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


def get_email_config() -> dict:
    """
    Get email provider configuration dictionary.

    Returns configuration suitable for EmailService initialization.
    """
    settings = get_settings()
    email = settings.email

    config = {
        "provider": email.EMAIL_PROVIDER,
    }

    if email.EMAIL_PROVIDER == "sendgrid":
        config["sendgrid"] = {
            "api_key": email.SENDGRID_API_KEY,
            "webhook_verification_key": email.SENDGRID_WEBHOOK_KEY,
        }
    elif email.EMAIL_PROVIDER == "ses":
        config["ses"] = {
            "aws_access_key_id": email.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": email.AWS_SECRET_ACCESS_KEY,
            "region": email.AWS_SES_REGION,
            "configuration_set": email.AWS_SES_CONFIGURATION_SET,
        }

    return config
