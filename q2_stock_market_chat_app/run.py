#!/usr/bin/env python3
"""
Main entry point for the Stock Market Chat application
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.utils.logger import setup_logging
from loguru import logger


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create database directory if it doesn't exist
    os.makedirs("chroma_db", exist_ok=True)
    
    logger.info("🚀 Starting Stock Market Chat Application")
    logger.info(f"📊 Host: {settings.host}")
    logger.info(f"🌐 Port: {settings.port}")
    logger.info(f"🔧 Debug: {settings.debug}")
    
    # Check for required API keys
    if not settings.openai_api_key:
        logger.warning("⚠️  OpenAI API key not configured - AI features will use mock responses")
    
    if not settings.news_api_key:
        logger.warning("⚠️  News API key not configured - News features will use mock data")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )


if __name__ == "__main__":
    main() 