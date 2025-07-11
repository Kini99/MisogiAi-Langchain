"""
Main FastAPI application for Stock Market Chat
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db, get_db
from app.api.websockets.chat_websocket import connection_manager, chat_handler
from app.services.data.stock_data_service import stock_data_service
from app.services.news.news_service import news_service
from app.services.ai.ai_service import ai_advisor

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Real-time Stock Market Chat Application with AI-powered recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print(f"🚀 {settings.app_name} starting up...")
    print(f"📊 Stock data service initialized")
    print(f"📰 News service initialized")
    print(f"🤖 AI advisor initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print(f"🛑 {settings.app_name} shutting down...")
    await stock_data_service.close_session()
    await news_service.close_session()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface"""
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                await chat_handler.handle_message(user_id, message_data.get("content", ""))
            elif message_data.get("type") == "ping":
                await connection_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, user_id)
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(user_id)


# REST API endpoints
@app.get("/api/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """Get stock data for a specific symbol"""
    try:
        stock_data = await stock_data_service.get_stock_price(symbol.upper())
        if stock_data:
            return {
                "success": True,
                "data": stock_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Stock data not found for {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def get_multiple_stocks(symbols: str):
    """Get data for multiple stocks"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        if len(symbol_list) > settings.max_stocks_per_request:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {settings.max_stocks_per_request} symbols allowed"
            )
        
        stock_data = await stock_data_service.get_multiple_stocks(symbol_list)
        return {
            "success": True,
            "data": stock_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/summary")
async def get_market_summary():
    """Get market summary for major indices"""
    try:
        market_data = await stock_data_service.get_market_summary()
        return {
            "success": True,
            "data": market_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/trending")
async def get_trending_stocks():
    """Get trending stocks"""
    try:
        trending_stocks = await stock_data_service.get_trending_stocks()
        return {
            "success": True,
            "data": trending_stocks,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news")
async def get_news(query: str = "stock market", count: int = 10):
    """Get financial news"""
    try:
        if count > 20:
            count = 20
        
        news_data = await news_service.get_financial_news(query, count)
        return {
            "success": True,
            "data": news_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/stock/{symbol}")
async def get_stock_news(symbol: str, count: int = 10):
    """Get news specific to a stock"""
    try:
        if count > 20:
            count = 20
        
        news_data = await news_service.get_stock_specific_news(symbol.upper(), count)
        return {
            "success": True,
            "data": news_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/{symbol}")
async def get_stock_recommendation(symbol: str):
    """Get AI-powered stock recommendation"""
    try:
        recommendation = await ai_advisor.get_stock_recommendation(symbol.upper())
        return {
            "success": True,
            "data": recommendation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/stocks")
async def search_stocks(query: str):
    """Search for stocks by name or symbol"""
    try:
        results = await stock_data_service.search_stocks(query)
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database endpoints
@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str, db: Session = Depends(get_db)):
    """Get chat history for a user"""
    try:
        from app.core.database import ChatMessage
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.timestamp.desc()).limit(50).all()
        
        history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            history.append({
                "type": msg.message_type,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": json.loads(msg.metadata) if msg.metadata else None
            })
        
        return {
            "success": True,
            "data": history,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_application_stats():
    """Get application statistics"""
    try:
        from app.core.database import ChatMessage, StockData, NewsArticle, StockRecommendation
        
        db = next(get_db())
        
        stats = {
            "total_messages": db.query(ChatMessage).count(),
            "total_stock_data_points": db.query(StockData).count(),
            "total_news_articles": db.query(NewsArticle).count(),
            "total_recommendations": db.query(StockRecommendation).count(),
            "active_connections": len(connection_manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 