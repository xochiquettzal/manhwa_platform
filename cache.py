# cache.py
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory cache manager with TTL support"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._default_ttl = 300  # 5 minutes default
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set a value in cache with optional TTL"""
        if ttl is None:
            ttl = self._default_ttl
        
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl
        
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired"""
        if key not in self._cache:
            return None
        
        # Check if expired
        if time.time() > self._timestamps[key]:
            self.delete(key)
            return None
        
        logger.debug(f"Cache hit: {key}")
        return self._cache[key]
    
    def delete(self, key: str) -> None:
        """Delete a key from cache"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"Cache delete: {key}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time > timestamp
        ]
        
        for key in expired_keys:
            self.delete(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time <= timestamp
        ]
        
        return {
            'total_keys': len(self._cache),
            'active_keys': len(active_keys),
            'expired_keys': len(self._cache) - len(active_keys),
            'memory_usage': sum(len(str(v)) for v in self._cache.values())
        }

# Global cache instance
cache_manager = CacheManager()

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def _generate_cache_key(func, args, kwargs, prefix: str) -> str:
    """Generate a unique cache key for function call"""
    # Create a string representation of the function call
    key_data = {
        'func_name': func.__name__,
        'args': args,
        'kwargs': kwargs,
        'prefix': prefix
    }
    
    # Convert to JSON string and hash it
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache keys matching a pattern"""
    count = 0
    keys_to_delete = []
    
    for key in cache_manager._cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache_manager.delete(key)
        count += 1
    
    if count > 0:
        logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
    
    return count

def cache_clear():
    """Clear all cache"""
    cache_manager.clear()

def get_cache_stats():
    """Get cache statistics"""
    return cache_manager.get_stats()

# Cache decorators for specific use cases
def cache_search_results(ttl: int = 300):
    """Cache search results specifically"""
    return cache_result(ttl=ttl, key_prefix="search")

def cache_user_data(ttl: int = 600):
    """Cache user-specific data"""
    return cache_result(ttl=ttl, key_prefix="user")

def cache_static_data(ttl: int = 3600):
    """Cache static data that doesn't change often"""
    return cache_result(ttl=ttl, key_prefix="static")

# Periodic cleanup task
def start_cache_cleanup(interval: int = 60):
    """Start periodic cache cleanup (call this in a separate thread)"""
    import threading
    import time
    
    def cleanup_loop():
        while True:
            time.sleep(interval)
            try:
                cache_manager.cleanup_expired()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info(f"Cache cleanup started with {interval}s interval")
