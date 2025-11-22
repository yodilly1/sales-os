"""Application configuration settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Sales OS"
    app_version: str = "0.1.0"
    debug: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    data_dir: Path = base_dir / "data"
    templates_dir: Path = data_dir / "templates"
    assets_dir: Path = data_dir / "assets"
    output_dir: Path = base_dir / "output"

    # Brand settings
    brand_primary_color: str = "#1E40AF"  # Blue-800
    brand_secondary_color: str = "#3B82F6"  # Blue-500
    brand_accent_color: str = "#10B981"  # Emerald-500
    brand_text_color: str = "#1F2937"  # Gray-800
    brand_light_color: str = "#F9FAFB"  # Gray-50
    brand_font_family: str = "Inter, system-ui, sans-serif"
    brand_heading_font: str = "Inter, system-ui, sans-serif"

    # PDF settings
    pdf_page_size: str = "A4"
    pdf_margin_top: float = 72.0  # points (1 inch)
    pdf_margin_bottom: float = 72.0
    pdf_margin_left: float = 72.0
    pdf_margin_right: float = 72.0

    # Deck settings
    deck_width: int = 1920
    deck_height: int = 1080

    # Export settings
    export_quality: str = "high"  # low, medium, high

    # API settings
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_prefix = "SALES_OS_"
        env_file = ".env"


settings = Settings()
