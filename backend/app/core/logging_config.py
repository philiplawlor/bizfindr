"""
Logging configuration for the BizFindr application.

This module sets up a centralized logging configuration that can be used throughout
the application. It configures both file and console handlers with appropriate
formatters and log levels.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import current_app
from pathlib import Path

def configure_logging(app):
    """
    Configure logging for the Flask application.
    
    Args:
        app: The Flask application instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(app.config.get('LOG_DIR', 'logs'))
    logs_dir.mkdir(exist_ok=True)
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler for all logs
    all_logs_file = logs_dir / 'bizfindr.log'
    file_handler = RotatingFileHandler(
        all_logs_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Error file handler (only errors)
    error_logs_file = logs_dir / 'bizfindr_errors.log'
    error_handler = RotatingFileHandler(
        error_logs_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    # Log application startup
    logger.info("=" * 80)
    logger.info(f"Starting BizFindr application (environment: {app.env})")
    logger.info(f"Logging to: {all_logs_file.absolute()}")
    logger.info("=" * 80)
    
    return logger

class RequestIdFilter(logging.Filter):
    """
    A logging filter that adds request ID to log records.
    """
    def filter(self, record):
        from flask import request
        record.request_id = request.headers.get('X-Request-ID', 'no-request-id')
        return True

def get_logger(name):
    """
    Get a logger instance with the given name.
    
    Args:
        name (str): The name of the logger (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Add request ID filter if we're in a request context
    try:
        from flask import has_request_context
        if has_request_context() and not any(isinstance(f, RequestIdFilter) for f in logger.filters.values()):
            logger.addFilter(RequestIdFilter())
    except RuntimeError:
        # Outside of application context
        pass
        
    return logger

def log_exception(sender, exception, **extra):
    """
    Log unhandled exceptions.
    
    This function is intended to be connected to Flask's got_request_exception signal.
    """
    logger = get_logger(__name__)
    logger.error(
        "Unhandled exception: %s",
        str(exception),
        exc_info=exception,
        extra=extra
    )
