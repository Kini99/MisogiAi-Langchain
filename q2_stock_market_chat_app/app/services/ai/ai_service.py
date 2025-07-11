"""
AI service for generating stock recommendations using LangChain
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.vectorstores import Chroma
from loguru import logger

from app.core.config import settings
from app.core.database import get_chroma_client, StockRecommendation, get_db
from app.services.data.stock_data_service import stock_data_service
from app.services.news.news_service import news_service


class AIStockAdvisor:
    """AI-powered stock recommendation system"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.initialize_ai_components()
    
    def initialize_ai_components(self):
        """Initialize AI components"""
        try:
            if settings.openai_api_key:
                self.llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    api_key=settings.openai_api_key
                )
                self.embeddings = OpenAIEmbeddings(
                    model=settings.embedding_model,
                    api_key=settings.openai_api_key
                )
            else:
                logger.warning("OpenAI API key not configured, using mock responses")
                self.llm = None
                self.embeddings = None
            
            # Initialize vector store
            self.initialize_vectorstore()
            
        except Exception as e:
            logger.error(f"Error initializing AI components: {e}")
    
    def initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        try:
            chroma_client = get_chroma_client()
            self.vectorstore = Chroma(
                client=chroma_client,
                collection_name="stock_knowledge",
                embedding_function=self.embeddings
            )
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
    
    async def gather_data(self, symbol: str) -> Dict[str, Any]:
        """Gather all relevant data for analysis"""
        try:
            symbol = symbol.upper()
            
            # Get stock data
            stock_data = await stock_data_service.get_stock_price(symbol)
            
            # Get historical data
            historical_data = await stock_data_service.get_historical_data(symbol, "6mo")
            
            # Get news data
            news_data = await news_service.get_stock_specific_news(symbol, 10)
            
            return {
                'symbol': symbol,
                'stock_data': stock_data or {},
                'historical_data': historical_data,
                'news_data': news_data or []
            }
            
        except Exception as e:
            logger.error(f"Error gathering data: {e}")
            return {
                'symbol': symbol,
                'stock_data': {},
                'historical_data': None,
                'news_data': []
            }
    
    async def analyze_technical(self, historical_data) -> Dict[str, Any]:
        """Analyze technical indicators"""
        try:
            if historical_data is None:
                return {}
            
            # Calculate technical indicators
            df = historical_data
            
            # Simple moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Current values
            current_price = df['Close'].iloc[-1]
            sma_20 = df['SMA_20'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            technical_analysis = {
                'current_price': current_price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'rsi': rsi,
                'price_vs_sma20': (current_price / sma_20 - 1) * 100 if sma_20 else 0,
                'price_vs_sma50': (current_price / sma_50 - 1) * 100 if sma_50 else 0,
                'trend': 'bullish' if current_price > sma_20 > sma_50 else 'bearish' if current_price < sma_20 < sma_50 else 'neutral'
            }
            
            return technical_analysis
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {}
    
    async def analyze_fundamental(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fundamental factors"""
        try:
            if not stock_data:
                return {}
            
            # Basic fundamental analysis
            fundamental_analysis = {
                'market_cap': stock_data.get('market_cap', 0),
                'volume': stock_data.get('volume', 0),
                'price_change': stock_data.get('change', 0),
                'price_change_percent': stock_data.get('change_percent', 0),
                'volatility': abs(stock_data.get('change_percent', 0))
            }
            
            return fundamental_analysis
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis: {e}")
            return {}
    
    async def analyze_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze news sentiment"""
        try:
            if not news_data:
                return {'overall_sentiment': 'neutral', 'sentiment_score': 0}
            
            # Calculate overall sentiment
            sentiment_scores = [article['sentiment_score'] for article in news_data]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Categorize sentiment
            if avg_sentiment >= 0.1:
                overall_sentiment = 'positive'
            elif avg_sentiment <= -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            sentiment_analysis = {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': avg_sentiment,
                'news_count': len(news_data),
                'positive_news': len([s for s in sentiment_scores if s > 0.1]),
                'negative_news': len([s for s in sentiment_scores if s < -0.1]),
                'neutral_news': len([s for s in sentiment_scores if -0.1 <= s <= 0.1])
            }
            
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0}
    
    async def generate_recommendation(self, symbol: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final recommendation"""
        try:
            if not self.llm:
                # Mock recommendation if no LLM
                recommendation = self.generate_mock_recommendation(analysis_data)
            else:
                recommendation = await self.generate_ai_recommendation(symbol, analysis_data)
            
            # Save recommendation to database
            await self.save_recommendation(symbol, recommendation)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self.generate_mock_recommendation(analysis_data)
    
    async def generate_ai_recommendation(self, symbol: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered recommendation"""
        try:
            # Define response schema
            response_schemas = [
                ResponseSchema(name="recommendation", description="buy, sell, or hold"),
                ResponseSchema(name="confidence_score", description="confidence score between 0.0 and 1.0"),
                ResponseSchema(name="reasoning", description="detailed explanation for the recommendation"),
                ResponseSchema(name="price_target", description="target price or price range"),
                ResponseSchema(name="risk_level", description="low, medium, or high risk"),
                ResponseSchema(name="time_horizon", description="short-term, medium-term, or long-term")
            ]
            output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_template("""
            You are a professional stock analyst. Based on the following data, provide a stock recommendation.
            
            Stock Symbol: {symbol}
            
            Technical Analysis:
            {technical_analysis}
            
            Fundamental Analysis:
            {fundamental_analysis}
            
            Sentiment Analysis:
            {sentiment_analysis}
            
            Recent News:
            {recent_news}
            
            {format_instructions}
            
            Be objective and consider all factors. If you don't have enough data, recommend "hold" with low confidence.
            """)
            
            # Prepare data
            technical_str = json.dumps(analysis_data.get('technical', {}), indent=2)
            fundamental_str = json.dumps(analysis_data.get('fundamental', {}), indent=2)
            sentiment_str = json.dumps(analysis_data.get('sentiment', {}), indent=2)
            news_str = "\n".join([f"- {article['title']}" for article in analysis_data.get('news_data', [])[:5]])
            
            # Generate recommendation
            chain = prompt | self.llm | output_parser
            
            result = await chain.ainvoke({
                "symbol": symbol,
                "technical_analysis": technical_str,
                "fundamental_analysis": fundamental_str,
                "sentiment_analysis": sentiment_str,
                "recent_news": news_str,
                "format_instructions": output_parser.get_format_instructions()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            return self.generate_mock_recommendation(analysis_data)
    
    def generate_mock_recommendation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock recommendation for testing"""
        return {
            "recommendation": "hold",
            "confidence_score": 0.5,
            "reasoning": "Insufficient data for comprehensive analysis. Consider monitoring for more information.",
            "price_target": "Current price ± 5%",
            "risk_level": "medium",
            "time_horizon": "short-term"
        }
    
    async def save_recommendation(self, symbol: str, recommendation: Dict[str, Any]):
        """Save recommendation to database"""
        try:
            db = next(get_db())
            db_recommendation = StockRecommendation(
                symbol=symbol,
                recommendation=recommendation.get('recommendation', 'hold'),
                confidence_score=recommendation.get('confidence_score', 0.5),
                reasoning=recommendation.get('reasoning', ''),
                price_target=0.0,  # Parse from string if needed
                risk_level=recommendation.get('risk_level', 'medium'),
                timestamp=datetime.now()
            )
            db.add(db_recommendation)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
    
    async def get_stock_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock recommendation"""
        try:
            # Step 1: Gather data
            data = await self.gather_data(symbol)
            
            # Step 2: Analyze technical indicators
            technical_analysis = await self.analyze_technical(data['historical_data'])
            
            # Step 3: Analyze fundamental factors
            fundamental_analysis = await self.analyze_fundamental(data['stock_data'])
            
            # Step 4: Analyze sentiment
            sentiment_analysis = await self.analyze_sentiment(data['news_data'])
            
            # Step 5: Generate recommendation
            recommendation = await self.generate_recommendation(symbol, {
                'technical': technical_analysis,
                'fundamental': fundamental_analysis,
                'sentiment': sentiment_analysis,
                'news_data': data['news_data']
            })
            
            return {
                'symbol': symbol,
                'stock_data': data['stock_data'],
                'analysis': {
                    'technical': technical_analysis,
                    'fundamental': fundamental_analysis,
                    'sentiment': sentiment_analysis
                },
                'recommendation': recommendation,
                'timestamp': datetime.now()
            }
                
        except Exception as e:
            logger.error(f"Error getting stock recommendation: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'recommendation': self.generate_mock_recommendation({})
            }
    
    async def simple_analysis(self, symbol: str) -> Dict[str, Any]:
        """Simple analysis without complex workflow"""
        try:
            # Gather data
            stock_data = await stock_data_service.get_stock_price(symbol)
            news_data = await news_service.get_stock_specific_news(symbol, 5)
            
            # Simple sentiment analysis
            sentiment_scores = [article['sentiment_score'] for article in news_data]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Simple recommendation logic
            if stock_data:
                price_change = stock_data.get('change_percent', 0)
                if price_change > 2 and avg_sentiment > 0.1:
                    recommendation = "buy"
                    confidence = 0.7
                elif price_change < -2 and avg_sentiment < -0.1:
                    recommendation = "sell"
                    confidence = 0.7
                else:
                    recommendation = "hold"
                    confidence = 0.5
            else:
                recommendation = "hold"
                confidence = 0.3
            
            return {
                'symbol': symbol,
                'stock_data': stock_data,
                'news_data': news_data,
                'recommendation': {
                    'recommendation': recommendation,
                    'confidence_score': confidence,
                    'reasoning': f"Based on {len(news_data)} news articles and price movement",
                    'price_target': 'Current price ± 10%',
                    'risk_level': 'medium',
                    'time_horizon': 'short-term'
                },
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error in simple analysis: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'recommendation': self.generate_mock_recommendation({})
            }


# Global instance
ai_advisor = AIStockAdvisor() 