"""
Application middleware configuration.
"""
from flask import request, g
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_middleware(app):
    """Set up application middleware.
    
    Args:
        app: Flask application instance
    """
    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Calculate request processing time
        if hasattr(g, 'start_time'):
            response_time = (time.time() - g.start_time) * 1000  # Convert to milliseconds
            response.headers['X-Response-Time'] = f'{response_time:.2f}ms'
            
            # Log slow requests
            if response_time > 500:  # Log requests slower than 500ms
                logger.warning(
                    'Slow request: %s %s (%.2fms)',
                    request.method,
                    request.path,
                    response_time
                )
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CORS headers are handled by Flask-CORS
        
        return response
    
    # Rate limiting middleware (basic implementation)
    if settings.ENVIRONMENT != 'testing':
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[settings.RATE_LIMIT_DEFAULT],
            storage_uri=settings.RATE_LIMIT_STORAGE_URL,
            strategy="fixed-window"
        )
        
        # Apply rate limiting to all API routes
        limiter.exempt('static')
        
        # Special rate limits for auth endpoints
        auth_limits = ["10 per minute", "100 per hour"]
        
        @app.before_request
        def set_rate_limits():
            if request.path.startswith(f"{settings.API_PREFIX}/v1/auth"):
                limiter.limit(auth_limits[0], per_method=True)(lambda: None)()
            elif request.path.startswith(settings.API_PREFIX):
                limiter.limit(settings.RATE_LIMIT_DEFAULT, per_method=True)(lambda: None)()
    
    # Request ID middleware
    @app.before_request
    def set_request_id():
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
        g.request_id = request_id
    
    # Logging context
    @app.before_request
    def set_logging_context():
        from flask import has_request_context
        
        if has_request_context():
            import logging
            from pythonjsonlogger import jsonlogger
            
            class RequestFilter(logging.Filter):
                def filter(self, record):
                    if has_request_context():
                        record.request_id = g.get('request_id', '')
                        record.remote_addr = request.remote_addr
                        record.method = request.method
                        record.path = request.path
                        record.user_agent = request.user_agent.string if request.user_agent else ''
                    return True
            
            # Add filter to all handlers
            for handler in logging.getLogger().handlers:
                if not any(isinstance(f, RequestFilter) for f in handler.filters):
                    handler.addFilter(RequestFilter())
    
    # Compression middleware (if enabled)
    if settings.ENABLE_GZIP:
        from flask_compress import Compress
        Compress(app)
    
    # Security headers middleware
    @app.after_request
    def set_security_headers(response):
        # Content Security Policy
        csp = "default-src 'self'; " \
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; " \
              "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " \
              "img-src 'self' data: https:; " \
              "font-src 'self' https://cdn.jsdelivr.net; " \
              "connect-src 'self' https://api.ct.gov;"
        
        response.headers['Content-Security-Policy'] = csp
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS - only in production with HTTPS
        if settings.ENVIRONMENT == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

def rate_limit(limit: str, key_func: Optional[Callable[[], str]] = None):
    """
    Decorator to apply rate limiting to a specific endpoint.
    
    Args:
        limit: Rate limit string (e.g., '100 per day')
        key_func: Optional function to generate a key for rate limiting
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from flask_limiter.util import get_remote_address
            
            # Use provided key_func or default to remote address
            key = key_func() if key_func else get_remote_address()
            
            # Get or create rate limiter
            from flask import current_app
            if not hasattr(current_app, 'limiter'):
                from flask_limiter import Limiter
                current_app.limiter = Limiter(
                    app=current_app,
                    key_func=get_remote_address,
                    storage_uri=current_app.config.get('RATE_LIMIT_STORAGE_URL'),
                    strategy="fixed-window"
                )
            
            # Apply rate limit
            with current_app.test_request_context():
                current_app.limiter.check(limit, key=key)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
