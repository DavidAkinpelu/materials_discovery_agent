from cachetools import TTLCache, LRUCache
from typing import Optional, Any
import json

class CacheManager:
    """
    Simple in-memory cache for local development
    No Redis needed
    """
    
    def __init__(self, max_size: int = 1000):
        # LRU cache for permanent storage
        self.permanent = LRUCache(maxsize=max_size)
        
        # TTL cache for temporary storage (24 hours default)
        self.temporary = TTLCache(maxsize=max_size, ttl=86400)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.permanent:
            return self.permanent[key]
        if key in self.temporary:
            return self.temporary[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds. If None, store permanently.
        """
        if ttl is None:
            self.permanent[key] = value
        else:
            if ttl != 86400:
                if not hasattr(self, f'ttl_{ttl}'):
                    setattr(self, f'ttl_{ttl}', TTLCache(maxsize=1000, ttl=ttl))
                cache = getattr(self, f'ttl_{ttl}')
                cache[key] = value
            else:
                self.temporary[key] = value
    
    def clear(self):
        """Clear all caches"""
        self.permanent.clear()
        self.temporary.clear()
        # Clear any dynamic TTL caches
        for attr_name in list(vars(self).keys()):
            if attr_name.startswith('ttl_'):
                getattr(self, attr_name).clear()

# Global cache instance
cache_manager = CacheManager(max_size=1000)

