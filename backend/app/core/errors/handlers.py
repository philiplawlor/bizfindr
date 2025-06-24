"""
Error handlers for the BizFindr application.

This module provides centralized error handling for the application,
including API error responses and web error pages.
"""

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.core.logging_config import get_logger

logger = get_logger(__name__)

class APIError(Exception):
    """Base class for API errors."""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
    
    def to_dict(self):
        """Convert the error to a dictionary for JSON responses."""
        rv = dict(self.payload or {})
        rv['status'] = 'error'
        rv['code'] = self.status_code
        rv['message'] = self.message
        return rv

class ValidationError(APIError):
    """Raised when request validation fails."""
    def __init__(self, message='Invalid input', errors=None):
        super().__init__(message, 400)
        self.errors = errors or {}
    
    def to_dict(self):
        rv = super().to_dict()
        if self.errors:
            rv['errors'] = self.errors
        return rv

class NotFoundError(APIError):
    """Raised when a requested resource is not found."""
    def __init__(self, message='The requested resource was not found'):
        super().__init__(message, 404)

class UnauthorizedError(APIError):
    """Raised when authentication is required or invalid."""
    def __init__(self, message='Authentication required'):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    """Raised when the user doesn't have permission."""
    def __init__(self, message='Insufficient permissions'):
        super().__init__(message, 403)

def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(500)
    def handle_http_error(error):
        """Handle HTTP errors with appropriate responses."""
        if isinstance(error, HTTPException):
            status_code = error.code
            message = error.description
        else:
            status_code = 500
            message = 'Internal Server Error'
        
        # Log the error
        logger.error(
            "HTTP Error %s: %s", status_code, message,
            extra={
                'status_code': status_code,
                'request_url': request.url,
                'request_method': request.method,
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string if request.user_agent else None,
            }
        )
        
        # API response
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'code': status_code,
                'message': message
            }), status_code
            
        # Web response
        if status_code == 404:
            return render_template('errors/404.html'), 404
        elif status_code == 500:
            return render_template('errors/500.html', 
                                error_ref=request.headers.get('X-Request-ID')), 500
        else:
            return render_template('errors/generic.html', 
                                error=error,
                                status_code=status_code), status_code
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle API errors with JSON responses."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all other exceptions."""
        # Log the error
        logger.exception("Unhandled exception: %s", str(error))
        
        # API response
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'code': 500,
                'message': 'An unexpected error occurred',
                'error': str(error) if app.debug else None
            }), 500
            
        # Web response
        return render_template('errors/500.html',
                            error=error,
                            error_ref=request.headers.get('X-Request-ID')), 500
    
    # Register signal handler for unhandled exceptions
    from flask import got_request_exception
    got_request_exception.connect(log_exception, app, weak=False)

def log_exception(sender, exception, **extra):
    """Log unhandled exceptions."""
    logger.error(
        "Unhandled exception: %s",
        str(exception),
        exc_info=exception,
        extra=extra
    )
