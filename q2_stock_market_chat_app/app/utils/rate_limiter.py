"""
Rate limiter utility for API protection
"""
import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict
from loguru import logger


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self.requests:
            del self.requests[identifier]


class AsyncRateLimiter:
    """Async rate limiter with semaphore"""
    
    def __init__(self, max_concurrent: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_connections = 0
    
    async def acquire(self):
        """Acquire connection slot"""
        await self.semaphore.acquire()
        self.active_connections += 1
        logger.debug(f"Active connections: {self.active_connections}")
    
    def release(self):
        """Release connection slot"""
        self.semaphore.release()
        self.active_connections = max(0, self.active_connections - 1)
        logger.debug(f"Active connections: {self.active_connections}")
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Global instances
rate_limiter = RateLimiter()
async_rate_limiter = AsyncRateLimiter() 