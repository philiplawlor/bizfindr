"""
BizFindr Flask Application Factory

This module contains the application factory function that creates and configures
the Flask application instance.
"""
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException

def create_app(test_config=None):
    """Create and configure the Flask application.
    
    Args:
        test_config (dict, optional): Configuration for testing. Defaults to None.
        
    Returns:
        Flask: The configured Flask application instance.
    """
    # Create the Flask app with template and static folder configuration
    template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=template_folder,
        static_folder=static_folder
    )
    
    # Log the template and static folder paths for debugging
    app.logger.info(f"Template folder: {app.template_folder}")
    app.logger.info(f"Static folder: {app.static_folder}")
    
    # List files in template folder for debugging
    try:
        if os.path.exists(app.template_folder):
            template_files = os.listdir(app.template_folder)
            app.logger.info(f"Files in template directory: {template_files}")
        else:
            app.logger.error(f"Template directory does not exist: {app.template_folder}")
    except Exception as e:
        app.logger.error(f"Error listing template directory: {str(e)}")
    
    # Configure the application
    configure_app(app, test_config)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register shell context
    register_shell_context(app)
    
    # Register commands
    register_commands(app)
    
    # Log final configuration
    app.logger.info(f"Final template folder: {app.template_folder}")
    app.logger.info(f"Final static folder: {app.static_folder}")
    
    return app

def configure_app(app, test_config=None):
    """Configure the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
        test_config (dict, optional): Configuration for testing. Defaults to None.
    """
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        MONGO_URI=os.getenv('MONGO_URI', 'mongodb://localhost:27017/bizfindr'),
        API_BASE_URL=os.getenv('API_BASE_URL', 'https://data.ct.gov/resource/n7gp-d28j.json'),
        API_KEY=os.getenv('API_KEY'),
        DEBUG=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        TESTING=test_config is not None
    )
    
    # Load configuration from instance folder
    app.config.from_pyfile('config.py', silent=True)
    
    # Override with test config if provided
    if test_config is not None:
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

def initialize_extensions(app):
    """Initialize Flask extensions.
    
    Args:
        app (Flask): The Flask application instance.
    """
    # Enable CORS
    CORS(app)
    
    # Initialize MongoDB client
    app.mongo = MongoClient(app.config['MONGO_URI'])
    app.db = app.mongo[app.config.get('MONGO_DB', 'bizfindr')]
    
    # Configure logging
    if not app.debug and not app.testing:
        configure_logging(app)

def configure_logging(app):
    """Configure application logging.
    
    Args:
        app (Flask): The Flask application instance.
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = logging.FileHandler('logs/bizfindr.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('BizFindr startup')

def register_blueprints(app):
    """Register Flask blueprints and frontend routes.
    
    Args:
        app (Flask): The Flask application instance.
    """
    # Import and register frontend blueprint first (order matters for route precedence)
    from .frontend import bp as frontend_bp
    app.register_blueprint(frontend_bp)
    
    # Import and register API blueprint
    from . import api
    app.register_blueprint(api.bp)
    
    # Log all registered routes after blueprints registration
    app.logger.info("Registered routes after blueprints:")
    for rule in app.url_map.iter_rules():
        app.logger.info(f"{rule.endpoint}: {rule.rule}")
    
    # Register catch-all route for SPA routing (must be registered last)
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend files for SPA routing."""
        # Handle static files (CSS, JS, images, etc.)
        if path != 'index.html' and os.path.exists(os.path.join(app.static_folder, path)):
            app.logger.info(f"Serving static file: {path}")
            return send_from_directory(app.static_folder, path)
        
        # Default stats to prevent template errors
        stats = {
            'total_registrations': 0,
            'latest_registration': None,
            'by_business_type': [],
            'by_status': [],
            'recent_registrations': []
        }
        
        # For all other routes, serve index.html (SPA routing)
        app.logger.info(f"Serving index.html for SPA route: {path}")
        return render_template('index.html', stats=stats, now=datetime.utcnow())
    
    # Log all registered routes after catch-all route registration
    app.logger.info("Registered routes after catch-all route:")
    for rule in app.url_map.iter_rules():
        app.logger.info(f"{rule.endpoint}: {rule.rule}")

def register_error_handlers(app):
    """Register error handlers.
    
    Args:
        app (Flask): The Flask application instance.
    """
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'not_found',
            'message': 'The requested resource was not found.'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred.'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'error': error.name.lower().replace(' ', '_'),
            'message': error.description
        }), error.code

def register_shell_context(app):
    """Register shell context processors.
    
    Args:
        app (Flask): The Flask application instance.
    """
    @app.shell_context_processor
    def make_shell_context():
        return {
            'app': app,
            'db': app.db,
            'mongo': app.mongo
        }

def register_commands(app):
    """Register Click commands.
    
    Args:
        app (Flask): The Flask application instance.
    """
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database."""
        from .scripts.init_db import main as init_db
        if init_db():
            print('Database initialized.')
        else:
            print('Failed to initialize database.')
    
    @app.cli.command('fetch-data')
    def fetch_data_command():
        """Fetch data from the CT.gov API."""
        from .services.data_fetcher import fetch_latest_data
        result = fetch_latest_data()
        print(f"Fetched {result.get('count', 0)} records.")
        if 'error' in result:
            print(f"Error: {result['error']}")
