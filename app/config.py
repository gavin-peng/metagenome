"""Application configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # App metadata
    app_name: str = "MetaGenome API"
    app_version: str = "0.1.0"

    # Database
    database_url: str = "sqlite:///./metagenome.db"

    # File storage
    storage_path: Path = Path("./storage")
    temp_storage_path: Path = Path("./storage/temp")
    max_upload_size: int = 10 * 1024 * 1024 * 1024  # 10GB

    # Timeouts
    prepare_timeout_seconds: int = 5

    # API settings
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure storage directories exist
settings.storage_path.mkdir(parents=True, exist_ok=True)
settings.temp_storage_path.mkdir(parents=True, exist_ok=True)
