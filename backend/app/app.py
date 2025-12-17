"""
Application factory for the BizFindr API.
"""
import logging
from typing import Any, Dict, List, Optional

import os
from flask import Flask, jsonify, request, g, send_from_directory, render_template
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
    app.config['DEBUG'] = True
    
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
    
    # Configure template and static folders
    app.template_folder = '/app/templates'
    app.static_folder = '/app/static'
    
    # Register blueprints (after configuring template/static folders)
    logger.info("Registering API blueprint...")
    app.register_blueprint(api_v1_router, url_prefix=f"{settings.API_PREFIX}/v1")
    
    # Debug: Log all registered routes after API blueprint registration
    logger.info("Registered routes after API blueprint:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.rule}")
    
    # Register frontend routes after API blueprint to ensure they take precedence
    @app.route('/')
    @app.route('/<path:path>')
    def serve_frontend(path='index.html'):
        """Serve frontend files."""
        try:
            # Log the request path for debugging
            app.logger.info(f"=== New Request: {request.path} ===")
            app.logger.info(f"Template folder: {os.path.abspath(app.template_folder)}")
            app.logger.info(f"Static folder: {os.path.abspath(app.static_folder)}")
            
            # List all files in template directory for debugging
            try:
                if os.path.exists(app.template_folder):
                    template_files = os.listdir(app.template_folder)
                    app.logger.info(f"Files in template directory: {template_files}")
                    
                    # Check if index.html exists in the template folder
                    if 'index.html' not in template_files:
                        app.logger.error("index.html not found in template directory")
                        return jsonify({"error": "index.html not found in template directory"}), 500
                else:
                    app.logger.error(f"Template directory does not exist: {app.template_folder}")
                    return jsonify({"error": f"Template directory does not exist: {app.template_folder}"}), 500
                    
            except Exception as e:
                app.logger.error(f"Error listing template directory: {str(e)}", exc_info=True)
            
            # Handle static files (CSS, JS, images, etc.)
            if path != 'index.html':
                static_file = os.path.join(app.static_folder, path)
                if os.path.exists(static_file):
                    app.logger.info(f"Serving static file: {static_file}")
                    return send_from_directory(app.static_folder, path)
            
            # For all other routes, serve index.html (SPA routing)
            try:
                # First try to render the template using Flask's template engine
                app.logger.info("Attempting to render template: index.html")
                return render_template('index.html')
                
            except Exception as e:
                app.logger.error(f"Error rendering template: {str(e)}", exc_info=True)
                # Fallback: Try to serve the file directly
                try:
                    app.logger.info("Attempting to serve index.html directly")
                    return send_from_directory(app.template_folder, 'index.html')
                except Exception as e2:
                    app.logger.error(f"Error serving index.html: {str(e2)}", exc_info=True)
                    return jsonify({
                        "error": "Failed to serve frontend",
                        "details": {
                            "template_error": str(e),
                            "direct_serve_error": str(e2),
                            "template_folder": os.path.abspath(app.template_folder),
                            "static_folder": os.path.abspath(app.static_folder),
                            "current_working_directory": os.getcwd(),
                            "files_in_template_dir": os.listdir(app.template_folder) if os.path.exists(app.template_folder) else "Directory not found"
                        }
                    }), 500
                    
        except Exception as e:
            app.logger.error(f"Unexpected error in serve_frontend: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "details": str(e)
            }), 500

    # Health check endpoint
    @app.route("/v1/health")
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        })
        
    # Serve frontend routes
    @app.route('/')
    @app.route('/<path:path>')
    def serve_frontend(path='index.html'):
        """Serve frontend files."""
        try:
            # Log the request path for debugging
            app.logger.info(f"=== New Request: {request.path} ===")
            app.logger.info(f"Template folder: {os.path.abspath(app.template_folder)}")
            app.logger.info(f"Static folder: {os.path.abspath(app.static_folder)}")
            
            # List all files in template directory for debugging
            try:
                if os.path.exists(app.template_folder):
                    template_files = os.listdir(app.template_folder)
                    app.logger.info(f"Files in template directory: {template_files}")
                    
                    # Check if index.html exists in the template folder
                    if 'index.html' not in template_files:
                        app.logger.error("index.html not found in template directory")
                        return jsonify({"error": "index.html not found in template directory"}), 500
                else:
                    app.logger.error(f"Template directory does not exist: {app.template_folder}")
                    return jsonify({"error": f"Template directory does not exist: {app.template_folder}"}), 500
                    
            except Exception as e:
                app.logger.error(f"Error listing template directory: {str(e)}", exc_info=True)
            
            # Handle static files (CSS, JS, images, etc.)
            if path != 'index.html':
                static_file = os.path.join(app.static_folder, path)
                if os.path.exists(static_file):
                    app.logger.info(f"Serving static file: {static_file}")
                    return send_from_directory(app.static_folder, path)
            
            # For all other routes, serve index.html (SPA routing)
            try:
                # First try to render the template using Flask's template engine
                app.logger.info("Attempting to render template: index.html")
                return render_template('index.html')
                
            except Exception as e:
                app.logger.error(f"Error rendering template: {str(e)}", exc_info=True)
                # Fallback: Try to serve the file directly
                try:
                    app.logger.info("Attempting to serve index.html directly")
                    return send_from_directory(app.template_folder, 'index.html')
                except Exception as e2:
                    app.logger.error(f"Error serving index.html: {str(e2)}", exc_info=True)
                    return jsonify({
                        "error": "Failed to serve frontend",
                        "details": {
                            "template_error": str(e),
                            "direct_serve_error": str(e2),
                            "template_folder": os.path.abspath(app.template_folder),
                            "static_folder": os.path.abspath(app.static_folder),
                            "current_working_directory": os.getcwd(),
                            "files_in_template_dir": os.listdir(app.template_folder) if os.path.exists(app.template_folder) else "Directory not found"
                        }
                    }), 500
                    
        except Exception as e:
            app.logger.error(f"Unexpected error in serve_frontend: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "details": str(e)
            }), 500
    
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
