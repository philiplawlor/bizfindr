"""
Application factory for the BizFindr API.
"""
import logging
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.core.cache import init_cache
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limiting import init_rate_limiting, apply_rate_limits
from app.api.v1.api import api_router as api_v1_router
from app.middleware import setup_middleware


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        test_config: Optional test configuration
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Configure logging first
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Create the Flask application
    app = Flask(__name__)
    
    # Load configuration
    if test_config is None:
        # Load from settings for normal operation
        app.config.from_object("app.core.config.settings")
    else:
        # Load test configuration
        app.config.update(test_config)
    
    # Configure CORS
    CORS(
        app,
        resources={
            r"/*": {
                "origins": settings.CORS_ORIGINS,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "supports_credentials": True,
            }
        }
    )
    
    # Initialize Redis cache
    init_cache(app)
    
    # Set up middleware
    setup_middleware(app)
    
    # Initialize rate limiting
    init_rate_limiting(app)
    if not app.config.get('TESTING'):
        apply_rate_limits(app)
    
    # Register blueprints
    app.register_blueprint(api_v1_router, url_prefix=f"{settings.API_PREFIX}/v1")
    
    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        })
    
    # Error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        response = {
            "error": {
                "code": error.code,
                "name": error.name,
                "description": error.description,
            }
        }
        return jsonify(response), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all other exceptions."""
        logger.exception("Unhandled exception")
        response = {
            "error": {
                "code": 500,
                "name": "Internal Server Error",
                "description": "An unexpected error occurred.",
            }
        }
        return jsonify(response), 500
    
    # Request logging
    @app.after_request
    def after_request(response):
        """Log request details after each request."""
        logger.info(
            "%s %s %s %s %s",
            request.remote_addr,
            request.method,
            request.path,
            dict(request.args),
            response.status_code,
        )
        return response
    
    logger.info("Application initialized")
    return app
