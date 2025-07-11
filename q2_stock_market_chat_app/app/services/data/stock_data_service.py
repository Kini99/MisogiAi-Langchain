"""
Stock data service for fetching live market data from multiple APIs
"""
import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.core.database import StockData, get_db


class StockDataService:
    """Service for fetching and managing stock data"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 30  # seconds
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price using Yahoo Finance"""
        try:
            # Check cache first
            cache_key = f"stock_{symbol}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_data
            
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"Could not fetch data for symbol: {symbol}")
                return None
            
            stock_data = {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'previous_close': info.get('regularMarketPreviousClose', 0),
                'open': info.get('regularMarketOpen', 0),
                'high': info.get('regularMarketDayHigh', 0),
                'low': info.get('regularMarketDayLow', 0),
                'timestamp': datetime.now()
            }
            
            # Cache the result
            self.cache[cache_key] = (stock_data, datetime.now())
            
            # Save to database
            await self.save_stock_data(stock_data)
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple stocks concurrently"""
        tasks = [self.get_stock_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        stock_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {symbol}: {result}")
                continue
            if result:
                stock_data[symbol] = result
        
        return stock_data
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical stock data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get market summary for major indices"""
        indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']  # S&P 500, Dow Jones, NASDAQ, VIX
        market_data = await self.get_multiple_stocks(indices)
        
        summary = {
            'timestamp': datetime.now(),
            'indices': market_data,
            'market_status': 'open' if datetime.now().hour < 16 else 'closed'
        }
        
        return summary
    
    async def save_stock_data(self, stock_data: Dict[str, Any]):
        """Save stock data to database"""
        try:
            db = next(get_db())
            db_stock = StockData(
                symbol=stock_data['symbol'],
                price=stock_data['price'],
                change=stock_data['change'],
                change_percent=stock_data['change_percent'],
                volume=stock_data['volume'],
                market_cap=stock_data['market_cap'],
                timestamp=stock_data['timestamp']
            )
            db.add(db_stock)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving stock data: {e}")
    
    async def get_trending_stocks(self) -> List[Dict[str, Any]]:
        """Get trending stocks based on volume and price movement"""
        try:
            # Popular stocks to check
            popular_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'ZM'
            ]
            
            stock_data = await self.get_multiple_stocks(popular_symbols)
            
            # Sort by absolute change percentage
            trending = sorted(
                stock_data.values(),
                key=lambda x: abs(x['change_percent']),
                reverse=True
            )[:10]
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending stocks: {e}")
            return []
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks by name or symbol"""
        try:
            # Use yfinance to search
            tickers = yf.Tickers(query)
            results = []
            
            for symbol in tickers.tickers:
                try:
                    info = symbol.info
                    if info and 'shortName' in info:
                        results.append({
                            'symbol': symbol.ticker,
                            'name': info.get('shortName', ''),
                            'sector': info.get('sector', ''),
                            'industry': info.get('industry', '')
                        })
                except:
                    continue
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []


# Global instance
stock_data_service = StockDataService() 