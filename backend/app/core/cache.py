"""
Redis cache configuration and utilities for BizFindr.
"""
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

import redis
from flask import current_app

from app.core.config import settings

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

# Initialize logger
logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool = None


def get_redis_connection() -> redis.Redis:
    """Get a Redis connection from the pool.
    
    Returns:
        redis.Redis: Redis connection instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    return redis.Redis(connection_pool=_redis_pool)


def init_cache(app) -> None:
    """Initialize the Redis cache with the Flask app.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        try:
            # Test the connection
            redis_conn = get_redis_connection()
            redis_conn.ping()
            app.extensions['redis'] = redis_conn
            logger.info("Redis cache initialized successfully")
        except redis.RedisError as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            app.extensions['redis'] = None


def get_cache() -> Optional[redis.Redis]:
    """Get the Redis cache instance from the current app context.
    
    Returns:
        Optional[redis.Redis]: Redis instance or None if not initialized
    """
    if not hasattr(current_app, 'extensions') or 'redis' not in current_app.extensions:
        return None
    return current_app.extensions['redis']


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from the given prefix and arguments.
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key
        
    Returns:
        str: Generated cache key
    """
    key_parts = [prefix] + [str(arg) for arg in args]
    if kwargs:
        key_parts.append(json.dumps(kwargs, sort_keys=True))
    return ':'.join(key_parts)


def cached(timeout: int = 300, key_prefix: str = None, unless=None):
    """Decorator to cache the result of a function.
    
    Args:
        timeout: Cache timeout in seconds (default: 300)
        key_prefix: Custom cache key prefix (default: function name)
        unless: Callable that returns True to bypass caching
    """
    def decorator(f: F) -> F:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Bypass cache if specified
            if callable(unless) and unless():
                return f(*args, **kwargs)
                
            # Get Redis connection
            cache = get_cache()
            if cache is None:
                return f(*args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or f"{f.__module__}:{f.__name__}"
            key = cache_key(prefix, *args, **kwargs)
            
            try:
                # Try to get from cache
                cached_value = cache.get(key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return json.loads(cached_value)
                
                # Call the function and cache the result
                result = f(*args, **kwargs)
                cache.setex(key, timeout, json.dumps(result))
                return result
                
            except (redis.RedisError, json.JSONDecodeError) as e:
                logger.error(f"Cache error for key {key}: {e}")
                # If there's a cache error, just call the function
                return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    return decorator


def invalidate_cache(prefix: str, *args, **kwargs) -> None:
    """Invalidate cache entries matching the given prefix and arguments.
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key
    """
    cache = get_cache()
    if cache is None:
        return
    
    pattern = cache_key(prefix, *args, **kwargs) + '*'
    try:
        keys = cache.keys(pattern)
        if keys:
            cache.delete(*keys)
            logger.debug(f"Invalidated cache keys: {keys}")
    except redis.RedisError as e:
        logger.error(f"Error invalidating cache for pattern {pattern}: {e}")


def clear_cache() -> None:
    """Clear the entire cache."""
    cache = get_cache()
    if cache is not None:
        try:
            cache.flushdb()
            logger.info("Cache cleared successfully")
        except redis.RedisError as e:
            logger.error(f"Error clearing cache: {e}")
