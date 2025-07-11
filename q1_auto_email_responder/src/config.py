"""
Configuration management for the Intelligent Email Response System.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Gmail API Configuration
    gmail_client_id: str = Field(..., env="GMAIL_CLIENT_ID")
    gmail_client_secret: str = Field(..., env="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: str = Field(..., env="GMAIL_REFRESH_TOKEN")
    
    # Database Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    chroma_persist_directory: str = Field(
        default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", 
        env="EMBEDDING_MODEL"
    )
    
    # Cache Configuration
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    
    # File paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    policies_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "policies")
    templates_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "templates")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        settings.data_dir,
        settings.policies_dir,
        settings.templates_dir,
        Path(settings.chroma_persist_directory),
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings 