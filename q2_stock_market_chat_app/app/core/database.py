"""
Database configuration and session management
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Generator
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_id = Column(String, index=True)
    message_type = Column(String)  # user, assistant, system
    content = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    message_metadata = Column(Text)  # JSON string for additional data


class StockData(Base):
    """Stock data model"""
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    change = Column(Float)
    change_percent = Column(Float)
    volume = Column(Integer)
    market_cap = Column(Float)
    timestamp = Column(DateTime, default=func.now())


class NewsArticle(Base):
    """News article model"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    source = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    sentiment_score = Column(Float)
    relevance_score = Column(Float)
    symbols = Column(String)  # Comma-separated stock symbols
    timestamp = Column(DateTime, default=func.now())


class StockRecommendation(Base):
    """Stock recommendation model"""
    __tablename__ = "stock_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    recommendation = Column(String)  # buy, sell, hold
    confidence_score = Column(Float)
    reasoning = Column(Text)
    price_target = Column(Float)
    risk_level = Column(String)
    timestamp = Column(DateTime, default=func.now())


# ChromaDB setup
def get_chroma_client():
    """Get ChromaDB client for vector storage"""
    return chromadb.PersistentClient(
        path=settings.chroma_persist_directory,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )


# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine) 