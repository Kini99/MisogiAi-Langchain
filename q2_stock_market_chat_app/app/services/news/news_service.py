"""
News service for fetching financial news and performing sentiment analysis
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from loguru import logger

from app.core.config import settings
from app.core.database import NewsArticle, get_db


class NewsService:
    """Service for fetching and analyzing financial news"""
    
    def __init__(self):
        self.session = None
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_financial_news(self, query: str = "stock market", count: int = 20) -> List[Dict[str, Any]]:
        """Get financial news from NewsAPI"""
        try:
            if not settings.news_api_key:
                logger.warning("News API key not configured, using mock data")
                return await self.get_mock_news()
            
            # Check cache
            cache_key = f"news_{query}_{count}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_data
            
            session = await self.get_session()
            
            # NewsAPI endpoint
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': count,
                'apiKey': settings.news_api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get('articles', [])
                    
                    # Process and analyze articles
                    processed_articles = []
                    for article in articles:
                        processed = await self.process_article(article)
                        if processed:
                            processed_articles.append(processed)
                    
                    # Cache results
                    self.cache[cache_key] = (processed_articles, datetime.now())
                    
                    return processed_articles
                else:
                    logger.error(f"News API error: {response.status}")
                    return await self.get_mock_news()
                    
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return await self.get_mock_news()
    
    async def get_stock_specific_news(self, symbol: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get news specific to a stock symbol"""
        query = f"{symbol} stock"
        return await self.get_financial_news(query, count)
    
    async def get_market_news(self) -> List[Dict[str, Any]]:
        """Get general market news"""
        queries = [
            "stock market",
            "wall street",
            "financial markets",
            "trading",
            "investing"
        ]
        
        all_news = []
        for query in queries:
            news = await self.get_financial_news(query, 5)
            all_news.extend(news)
        
        # Remove duplicates and sort by relevance
        unique_news = self.remove_duplicate_news(all_news)
        return sorted(unique_news, key=lambda x: x['relevance_score'], reverse=True)[:20]
    
    async def process_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process and analyze a news article"""
        try:
            title = article.get('title', '')
            content = article.get('content', '')
            description = article.get('description', '')
            
            # Combine text for analysis
            full_text = f"{title} {description} {content}"
            
            # Perform sentiment analysis
            sentiment_scores = self.sentiment_analyzer.polarity_scores(full_text)
            textblob_sentiment = TextBlob(full_text).sentiment
            
            # Extract stock symbols mentioned
            symbols = self.extract_stock_symbols(full_text)
            
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(full_text, symbols)
            
            processed_article = {
                'title': title,
                'content': content,
                'description': description,
                'source': article.get('source', {}).get('name', ''),
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'sentiment_score': sentiment_scores['compound'],
                'sentiment_label': self.get_sentiment_label(sentiment_scores['compound']),
                'relevance_score': relevance_score,
                'symbols': symbols,
                'timestamp': datetime.now()
            }
            
            # Save to database
            await self.save_news_article(processed_article)
            
            return processed_article
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """Extract potential stock symbols from text"""
        import re
        
        # Common stock symbols pattern
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(symbol_pattern, text)
        
        # Filter common words that aren't stock symbols
        common_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER',
            'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
            'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID',
            'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'YEAR', 'YOUR'
        }
        
        symbols = [s for s in potential_symbols if s not in common_words and len(s) >= 2]
        return list(set(symbols))[:5]  # Limit to 5 symbols
    
    def calculate_relevance_score(self, text: str, symbols: List[str]) -> float:
        """Calculate relevance score for news article"""
        score = 0.0
        
        # Base score for financial keywords
        financial_keywords = [
            'stock', 'market', 'trading', 'invest', 'earnings', 'revenue',
            'profit', 'loss', 'price', 'shares', 'dividend', 'analyst',
            'forecast', 'growth', 'decline', 'rally', 'crash', 'bull',
            'bear', 'portfolio', 'fund', 'etf', 'options', 'futures'
        ]
        
        text_lower = text.lower()
        for keyword in financial_keywords:
            if keyword in text_lower:
                score += 0.1
        
        # Bonus for stock symbols
        score += len(symbols) * 0.2
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.05:
            return 'positive'
        elif score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def remove_duplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate news articles"""
        seen_urls = set()
        unique_news = []
        
        for article in news_list:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_news.append(article)
        
        return unique_news
    
    async def save_news_article(self, article: Dict[str, Any]):
        """Save news article to database"""
        try:
            db = next(get_db())
            db_article = NewsArticle(
                title=article['title'],
                content=article['content'],
                source=article['source'],
                url=article['url'],
                published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')) if article['published_at'] else datetime.now(),
                sentiment_score=article['sentiment_score'],
                relevance_score=article['relevance_score'],
                symbols=','.join(article['symbols']),
                timestamp=article['timestamp']
            )
            db.add(db_article)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving news article: {e}")
    
    async def get_mock_news(self) -> List[Dict[str, Any]]:
        """Get mock news data for testing"""
        mock_articles = [
            {
                'title': 'Tech Stocks Rally on Strong Earnings Reports',
                'content': 'Major technology companies reported better-than-expected earnings, driving the NASDAQ to new highs.',
                'description': 'Technology sector leads market gains as earnings season continues.',
                'source': 'Financial Times',
                'url': 'https://example.com/tech-rally',
                'published_at': datetime.now().isoformat(),
                'sentiment_score': 0.3,
                'sentiment_label': 'positive',
                'relevance_score': 0.8,
                'symbols': ['AAPL', 'MSFT', 'GOOGL'],
                'timestamp': datetime.now()
            },
            {
                'title': 'Federal Reserve Signals Potential Rate Changes',
                'content': 'The Federal Reserve indicated possible adjustments to interest rates in response to economic indicators.',
                'description': 'Central bank policy changes could impact market dynamics.',
                'source': 'Wall Street Journal',
                'url': 'https://example.com/fed-rates',
                'published_at': datetime.now().isoformat(),
                'sentiment_score': -0.1,
                'sentiment_label': 'neutral',
                'relevance_score': 0.9,
                'symbols': [],
                'timestamp': datetime.now()
            }
        ]
        
        return mock_articles


# Global instance
news_service = NewsService() 