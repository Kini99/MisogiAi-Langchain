"""
WebSocket service for real-time chat communication
"""
import asyncio
import json
from typing import Dict, List, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.database import ChatMessage, get_db
from app.services.data.stock_data_service import stock_data_service
from app.services.news.news_service import news_service
from app.services.ai.ai_service import ai_advisor


class ConnectionManager:
    """Manages WebSocket connections and chat sessions"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_messages: Dict[str, List[Dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        session_id = f"session_{user_id}_{datetime.now().timestamp()}"
        
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = session_id
        self.session_messages[session_id] = []
        
        logger.info(f"User {user_id} connected with session {session_id}")
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "content": "Welcome to Stock Market Chat! Ask me about stocks, market data, or get AI-powered recommendations.",
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(welcome_message, user_id)
    
    def disconnect(self, user_id: str):
        """Disconnect a WebSocket client"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            session_id = self.user_sessions[user_id]
            del self.user_sessions[user_id]
            if session_id in self.session_messages:
                del self.session_messages[session_id]
        
        logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: Dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected users"""
        disconnected_users = []
        
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def save_message(self, user_id: str, message_type: str, content: str, metadata: Dict = None):
        """Save message to database"""
        try:
            session_id = self.user_sessions.get(user_id, f"session_{user_id}")
            db = next(get_db())
            
            db_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                message_type=message_type,
                content=content,
                metadata=json.dumps(metadata) if metadata else None,
                timestamp=datetime.now()
            )
            
            db.add(db_message)
            db.commit()
            
            # Add to session messages
            if session_id in self.session_messages:
                self.session_messages[session_id].append({
                    "type": message_type,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata
                })
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")


class ChatHandler:
    """Handles chat message processing and responses"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_message(self, user_id: str, message: str):
        """Handle incoming chat message"""
        try:
            # Save user message
            await self.connection_manager.save_message(user_id, "user", message)
            
            # Process message and generate response
            response = await self.process_message(message, user_id)
            
            # Send response
            await self.connection_manager.send_personal_message(response, user_id)
            
            # Save assistant response
            await self.connection_manager.save_message(
                user_id, 
                "assistant", 
                response["content"],
                response.get("metadata")
            )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_response = {
                "type": "error",
                "content": "Sorry, I encountered an error processing your request. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
            await self.connection_manager.send_personal_message(error_response, user_id)
    
    async def process_message(self, message: str, user_id: str) -> Dict:
        """Process message and generate appropriate response"""
        message_lower = message.lower().strip()
        
        # Check for stock price requests
        if any(keyword in message_lower for keyword in ["price", "stock", "quote", "ticker"]):
            return await self.handle_stock_request(message)
        
        # Check for news requests
        elif any(keyword in message_lower for keyword in ["news", "article", "update"]):
            return await self.handle_news_request(message)
        
        # Check for recommendation requests
        elif any(keyword in message_lower for keyword in ["recommend", "analysis", "advice", "should i"]):
            return await self.handle_recommendation_request(message)
        
        # Check for market summary
        elif any(keyword in message_lower for keyword in ["market", "summary", "overview", "indices"]):
            return await self.handle_market_request(message)
        
        # Check for trending stocks
        elif any(keyword in message_lower for keyword in ["trending", "popular", "hot", "top"]):
            return await self.handle_trending_request(message)
        
        # Default response
        else:
            return await self.handle_general_query(message)
    
    async def handle_stock_request(self, message: str) -> Dict:
        """Handle stock price requests"""
        try:
            # Extract stock symbol (simple extraction)
            words = message.upper().split()
            symbols = [word for word in words if len(word) <= 5 and word.isalpha()]
            
            if not symbols:
                return {
                    "type": "assistant",
                    "content": "Please provide a stock symbol (e.g., 'What's the price of AAPL?')",
                    "timestamp": datetime.now().isoformat()
                }
            
            symbol = symbols[0]
            stock_data = await stock_data_service.get_stock_price(symbol)
            
            if stock_data:
                content = f"**{symbol}**\n"
                content += f"Price: ${stock_data['price']:.2f}\n"
                content += f"Change: {stock_data['change']:+.2f} ({stock_data['change_percent']:+.2f}%)\n"
                content += f"Volume: {stock_data['volume']:,}\n"
                content += f"Market Cap: ${stock_data['market_cap']/1e9:.2f}B"
                
                return {
                    "type": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"symbol": symbol, "stock_data": stock_data}
                }
            else:
                return {
                    "type": "assistant",
                    "content": f"Sorry, I couldn't find data for {symbol}. Please check the symbol and try again.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling stock request: {e}")
            return {
                "type": "assistant",
                "content": "Sorry, I encountered an error fetching stock data. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_news_request(self, message: str) -> Dict:
        """Handle news requests"""
        try:
            # Extract potential stock symbol
            words = message.upper().split()
            symbols = [word for word in words if len(word) <= 5 and word.isalpha()]
            
            if symbols:
                symbol = symbols[0]
                news_data = await news_service.get_stock_specific_news(symbol, 3)
                query = f"news about {symbol}"
            else:
                news_data = await news_service.get_market_news()
                query = "market news"
            
            if news_data:
                content = f"**Latest {query.title()}:**\n\n"
                for i, article in enumerate(news_data[:3], 1):
                    sentiment_emoji = "📈" if article['sentiment_score'] > 0.1 else "📉" if article['sentiment_score'] < -0.1 else "➡️"
                    content += f"{i}. {sentiment_emoji} {article['title']}\n"
                    content += f"   Source: {article['source']}\n\n"
                
                return {
                    "type": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"news_count": len(news_data)}
                }
            else:
                return {
                    "type": "assistant",
                    "content": "Sorry, I couldn't find any recent news. Please try again later.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling news request: {e}")
            return {
                "type": "assistant",
                "content": "Sorry, I encountered an error fetching news. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_recommendation_request(self, message: str) -> Dict:
        """Handle stock recommendation requests"""
        try:
            # Extract stock symbol
            words = message.upper().split()
            symbols = [word for word in words if len(word) <= 5 and word.isalpha()]
            
            if not symbols:
                return {
                    "type": "assistant",
                    "content": "Please specify a stock symbol for analysis (e.g., 'Analyze AAPL' or 'Should I buy TSLA?')",
                    "timestamp": datetime.now().isoformat()
                }
            
            symbol = symbols[0]
            recommendation_data = await ai_advisor.get_stock_recommendation(symbol)
            
            if recommendation_data and 'recommendation' in recommendation_data:
                rec = recommendation_data['recommendation']
                
                # Recommendation emoji
                rec_emoji = {
                    "buy": "🟢",
                    "sell": "🔴", 
                    "hold": "🟡"
                }.get(rec.get('recommendation', 'hold'), '🟡')
                
                content = f"**{rec_emoji} {symbol} Analysis:**\n\n"
                content += f"**Recommendation:** {rec.get('recommendation', 'hold').upper()}\n"
                content += f"**Confidence:** {rec.get('confidence_score', 0.5)*100:.0f}%\n"
                content += f"**Reasoning:** {rec.get('reasoning', 'No reasoning provided')}\n"
                content += f"**Price Target:** {rec.get('price_target', 'Not specified')}\n"
                content += f"**Risk Level:** {rec.get('risk_level', 'medium').title()}\n"
                content += f"**Time Horizon:** {rec.get('time_horizon', 'short-term').title()}"
                
                return {
                    "type": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"symbol": symbol, "recommendation": rec}
                }
            else:
                return {
                    "type": "assistant",
                    "content": f"Sorry, I couldn't generate a recommendation for {symbol}. Please try again.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling recommendation request: {e}")
            return {
                "type": "assistant",
                "content": "Sorry, I encountered an error generating the recommendation. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_market_request(self, message: str) -> Dict:
        """Handle market summary requests"""
        try:
            market_data = await stock_data_service.get_market_summary()
            
            if market_data and 'indices' in market_data:
                content = "**Market Summary:**\n\n"
                
                for symbol, data in market_data['indices'].items():
                    if data:
                        name_map = {
                            '^GSPC': 'S&P 500',
                            '^DJI': 'Dow Jones',
                            '^IXIC': 'NASDAQ',
                            '^VIX': 'VIX'
                        }
                        name = name_map.get(symbol, symbol)
                        content += f"**{name}:** ${data['price']:.2f} ({data['change_percent']:+.2f}%)\n"
                
                content += f"\n**Market Status:** {market_data.get('market_status', 'Unknown').title()}"
                
                return {
                    "type": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"market_data": market_data}
                }
            else:
                return {
                    "type": "assistant",
                    "content": "Sorry, I couldn't fetch market data. Please try again later.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling market request: {e}")
            return {
                "type": "assistant",
                "content": "Sorry, I encountered an error fetching market data. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_trending_request(self, message: str) -> Dict:
        """Handle trending stocks requests"""
        try:
            trending_stocks = await stock_data_service.get_trending_stocks()
            
            if trending_stocks:
                content = "**Trending Stocks:**\n\n"
                
                for i, stock in enumerate(trending_stocks[:5], 1):
                    change_emoji = "📈" if stock['change_percent'] > 0 else "📉"
                    content += f"{i}. {change_emoji} **{stock['symbol']}**\n"
                    content += f"   ${stock['price']:.2f} ({stock['change_percent']:+.2f}%)\n"
                    content += f"   Volume: {stock['volume']:,}\n\n"
                
                return {
                    "type": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"trending_count": len(trending_stocks)}
                }
            else:
                return {
                    "type": "assistant",
                    "content": "Sorry, I couldn't fetch trending stocks. Please try again later.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling trending request: {e}")
            return {
                "type": "assistant",
                "content": "Sorry, I encountered an error fetching trending stocks. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_general_query(self, message: str) -> Dict:
        """Handle general queries"""
        content = "I'm here to help with stock market information! You can ask me about:\n\n"
        content += "• **Stock prices** (e.g., 'What's the price of AAPL?')\n"
        content += "• **Market news** (e.g., 'Show me market news')\n"
        content += "• **Stock analysis** (e.g., 'Analyze TSLA' or 'Should I buy MSFT?')\n"
        content += "• **Market summary** (e.g., 'Market overview')\n"
        content += "• **Trending stocks** (e.g., 'Show trending stocks')\n\n"
        content += "Just ask me anything about stocks and the market!"
        
        return {
            "type": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }


# Global instances
connection_manager = ConnectionManager()
chat_handler = ChatHandler(connection_manager) 