"""
Configuration settings for the Stock Market Chat Application
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Stock Market Chat"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./stock_chat.db"
    chroma_persist_directory: str = "./chroma_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # API Keys
    openai_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    max_concurrent_connections: int = 100
    
    # AI Model Settings
    openai_model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Stock Data Settings
    update_interval_seconds: int = 30
    max_stocks_per_request: int = 10
    news_update_interval: int = 300  # 5 minutes
    
    # Vector Database
    vector_dimension: int = 1536
    similarity_threshold: float = 0.8
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings 