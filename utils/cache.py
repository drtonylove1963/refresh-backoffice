import os
import json
from datetime import datetime, timedelta
from functools import wraps

class APICache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key):
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                if datetime.fromisoformat(data['expires']) > datetime.now():
                    return data['value']
        return None
    
    def set(self, key, value, expiry_minutes=15):
        cache_path = self._get_cache_path(key)
        expires = datetime.now() + timedelta(minutes=expiry_minutes)
        with open(cache_path, 'w') as f:
            json.dump({
                'value': value,
                'expires': expires.isoformat()
            }, f)

def cache_api_response(expiry_minutes=15):
    """Decorator to cache API responses"""
    cache = APICache()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, expiry_minutes)
            
            return result
        return wrapper
    return decorator
