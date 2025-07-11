"""
Redis-based caching service for frequently accessed policies and templates.
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import asyncio

import redis.asyncio as redis
from loguru import logger

from ..config import get_settings


class CacheService:
    """Redis-based caching service for performance optimization."""
    
    def __init__(self):
        """Initialize Redis cache connection."""
        self.settings = get_settings()
        self.redis_client = None
        self.default_ttl = self.settings.cache_ttl
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=False  # Keep as bytes for pickle
            )
            logger.info("Redis cache service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if not self.redis_client:
                return None
            
            value = await self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            if not self.redis_client:
                return False
            
            serialized_value = pickle.dumps(value)
            ttl_seconds = ttl or self.default_ttl
            
            await self.redis_client.setex(key, ttl_seconds, serialized_value)
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self.redis_client:
                return False
            
            return await self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key."""
        try:
            if not self.redis_client:
                return False
            
            return await self.redis_client.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"Error setting cache expiration: {e}")
            return False
    
    async def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get policy from cache."""
        cache_key = f"policy:{policy_id}"
        return await self.get(cache_key)
    
    async def set_policy(self, policy_id: str, policy_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache policy data."""
        cache_key = f"policy:{policy_id}"
        return await self.set(cache_key, policy_data, ttl)
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template from cache."""
        cache_key = f"template:{template_id}"
        return await self.get(cache_key)
    
    async def set_template(self, template_id: str, template_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache template data."""
        cache_key = f"template:{template_id}"
        return await self.set(cache_key, template_data, ttl)
    
    async def get_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        cache_key = f"embedding:{text_hash}"
        return await self.get(cache_key)
    
    async def set_embedding(self, text_hash: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """Cache text embedding."""
        cache_key = f"embedding:{text_hash}"
        return await self.set(cache_key, embedding, ttl)
    
    async def get_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        cache_key = f"search:{query_hash}"
        return await self.get(cache_key)
    
    async def set_search_results(self, query_hash: str, results: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache search results."""
        cache_key = f"search:{query_hash}"
        return await self.set(cache_key, results, ttl)
    
    async def invalidate_policy_cache(self, policy_id: str) -> bool:
        """Invalidate policy cache."""
        cache_key = f"policy:{policy_id}"
        return await self.delete(cache_key)
    
    async def invalidate_template_cache(self, template_id: str) -> bool:
        """Invalidate template cache."""
        cache_key = f"template:{template_id}"
        return await self.delete(cache_key)
    
    async def clear_category_cache(self, category: str) -> bool:
        """Clear all cache entries for a category."""
        try:
            if not self.redis_client:
                return False
            
            pattern = f"{category}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries for category: {category}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing category cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if not self.redis_client:
                return {}
            
            info = await self.redis_client.info()
            stats = {
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
            }
            
            # Calculate hit rate
            total_requests = stats['keyspace_hits'] + stats['keyspace_misses']
            if total_requests > 0:
                stats['hit_rate'] = stats['keyspace_hits'] / total_requests
            else:
                stats['hit_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if cache service is healthy."""
        try:
            if not self.redis_client:
                return False
            
            # Simple ping test
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis cache connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global cache service instance
cache_service = CacheService() 