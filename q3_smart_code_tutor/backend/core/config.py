"""
Configuration settings for the Code Interpreter
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_title: str = "Code Interpreter API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # E2B Settings
    e2b_api_key: Optional[str] = Field(default=None, env="E2B_API_KEY")
    e2b_project_id: Optional[str] = Field(default=None, env="E2B_PROJECT_ID")
    
    # OpenAI Settings (for RAG)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Vector Database Settings
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Code Execution Settings
    max_execution_time: int = Field(default=30, env="MAX_EXECUTION_TIME")  # seconds
    max_memory_usage: int = Field(default=512, env="MAX_MEMORY_USAGE")  # MB
    
    # WebSocket Settings
    max_connections: int = Field(default=100, env="MAX_WEBSOCKET_CONNECTIONS")
    
    # Documentation Settings
    docs_directory: str = Field(default="./docs", env="DOCS_DIRECTORY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings() 