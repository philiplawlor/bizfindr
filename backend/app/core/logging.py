"""
Logging configuration for the BizFindr application.
"""
import logging
import logging.config
import os
import sys
from logging.handlers import RotatingFileHandler, SysLogHandler
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def configure_logging() -> None:
    """Configure logging for the application."""
    log_level = logging.getLevelName(settings.LOG_LEVEL.upper())
    
    # Clear any existing log handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    root_logger.setLevel(log_level)
    
    # Prevent propagation to the root logger to avoid duplicate logs
    root_logger.propagate = False
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter in production, simple formatter in development
    if settings.ENVIRONMENT == 'production':
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s',
            timestamp=True,
            json_ensure_ascii=False,
            json_indent=2 if settings.DEBUG else None
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure file handler if LOG_FILE is set
    if settings.LOG_FILE:
        os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure syslog if SYSLOG_ADDRESS is set
    if settings.SYSLOG_ADDRESS:
        try:
            syslog_handler = SysLogHandler(address=settings.SYSLOG_ADDRESS)
            syslog_handler.setLevel(log_level)
            syslog_handler.setFormatter(formatter)
            root_logger.addHandler(syslog_handler)
        except Exception as e:
            root_logger.error(f"Failed to configure syslog: {e}")
    
    # Set log levels for specific loggers
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    
    # Capture warnings from the warnings module
    logging.captureWarnings(True)
    
    # Log unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        root_logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class RequestIdFilter(logging.Filter):
    """Log filter to add request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        from flask import has_request_context, g
        
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'no-request-id')
            record.remote_addr = getattr(g, 'remote_addr', 'no-remote-addr')
        else:
            record.request_id = 'no-request-context'
            record.remote_addr = 'no-remote-addr'
        
        return True


class JsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes request context."""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.created
        
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
            
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
            log_record['remote_addr'] = record.remote_addr
        
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
