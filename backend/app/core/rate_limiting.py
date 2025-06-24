"""
Rate limiting implementation using Redis for the BizFindr API.
"""
import time
import logging
from typing import Optional, Callable, Any, Dict, Tuple
from functools import wraps

from flask import request, g, jsonify, current_app
from redis.exceptions import RedisError

from app.core.cache import get_redis_connection
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Try again in {retry_after} seconds.")


def get_remote_address() -> str:
    """Get the IP address of the client."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr or '127.0.0.1'


def get_rate_limit_headers(limit: int, remaining: int, reset_time: int) -> Dict[str, str]:
    """Get rate limit headers for the response."""
    return {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(remaining),
        'X-RateLimit-Reset': str(reset_time),
        'Retry-After': str(max(0, int(reset_time - time.time())))
    }


def get_rate_limit_key(identifier: str, endpoint: str) -> str:
    """Generate a rate limit key for Redis."""
    return f"rate_limit:{endpoint}:{identifier}"


def is_rate_limited(
    key: str, 
    limit: int, 
    period: int,
    redis_conn = None
) -> Tuple[bool, Dict[str, int]]:
    """
    Check if the request should be rate limited.
    
    Args:
        key: Redis key for the rate limit
        limit: Maximum number of requests allowed in the period
        period: Time period in seconds
        redis_conn: Optional Redis connection
        
    Returns:
        Tuple of (is_limited, headers)
    """
    if redis_conn is None:
        redis_conn = get_redis_connection()
    
    current = int(time.time())
    window_start = current - period
    
    try:
        # Use a Redis pipeline for atomic operations
        pipe = redis_conn.pipeline()
        
        # Remove old timestamps outside the current window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Add current timestamp
        pipe.zadd(key, {current: current})
        
        # Set expiry on the key
        pipe.expire(key, period)
        
        # Get the count of requests in the current window
        pipe.zcard(key)
        
        # Execute the pipeline
        _, _, _, request_count = pipe.execute()
        
        # Check if limit is exceeded
        remaining = max(0, limit - request_count)
        reset_time = current + period
        
        headers = {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time)
        }
        
        return request_count > limit, headers
        
    except RedisError as e:
        logger.error(f"Redis error in rate limiting: {e}")
        # Fail open - don't rate limit if Redis is down
        return False, {}


def rate_limited(
    limit: int = 60,
    period: int = 60,
    key_func: Callable[[], str] = get_remote_address,
    error_message: Optional[str] = None
):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limit: Maximum number of requests allowed in the period
        period: Time period in seconds
        key_func: Function to get the rate limit key
        error_message: Custom error message when rate limit is exceeded
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Skip rate limiting in development
            if current_app.config.get('TESTING') or current_app.config.get('DEBUG'):
                return f(*args, **kwargs)
                
            # Get rate limit key
            identifier = key_func()
            endpoint = f"{request.endpoint}.{request.method.lower()}"
            redis_key = get_rate_limit_key(identifier, endpoint)
            
            # Check rate limit
            is_limited, headers = is_rate_limited(
                key=redis_key,
                limit=limit,
                period=period
            )
            
            # Set headers on response
            g.headers = headers
            
            if is_limited:
                retry_after = int(headers.get('X-RateLimit-Reset', 0) - time.time())
                response = jsonify({
                    'error': error_message or 'Rate limit exceeded',
                    'retry_after': retry_after
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                return response
                
            return f(*args, **kwargs)
        return wrapped
    return decorator


def init_rate_limiting(app):
    """Initialize rate limiting for the Flask app."""
    @app.after_request
    def inject_rate_limit_headers(response):
        # Add rate limit headers to the response
        if hasattr(g, 'headers'):
            for header, value in g.headers.items():
                response.headers[header] = value
        return response


# Default rate limits for different endpoints
DEFAULT_RATE_LIMITS = {
    'auth': (10, 60),  # 10 requests per minute for auth endpoints
    'api': (100, 60),  # 100 requests per minute for API endpoints
    'search': (30, 60),  # 30 requests per minute for search
    'public': (60, 60),  # 60 requests per minute for public endpoints
}


def get_rate_limit_for_endpoint(endpoint: str) -> Tuple[int, int]:
    """Get the rate limit for an endpoint."""
    if 'auth' in endpoint:
        return DEFAULT_RATE_LIMITS['auth']
    elif 'search' in endpoint:
        return DEFAULT_RATE_LIMITS['search']
    elif 'api' in endpoint:
        return DEFAULT_RATE_LIMITS['api']
    return DEFAULT_RATE_LIMITS['public']


def apply_rate_limits(app):
    """Apply rate limits to all routes."""
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        limit, period = get_rate_limit_for_endpoint(endpoint)
        
        # Skip if already decorated
        if hasattr(app.view_functions[endpoint], '_rate_limited'):
            continue
            
        # Apply rate limit decorator
        app.view_functions[endpoint] = rate_limited(
            limit=limit,
            period=period,
            error_message=f"Too many requests. Limit is {limit} per {period} seconds."
        )(app.view_functions[endpoint])
        
        # Mark as decorated
        app.view_functions[endpoint]._rate_limited = True
