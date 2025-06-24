"""
Celery configuration for background task processing.
"""
import logging
from datetime import timedelta
from typing import Dict, Any

from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Celery configuration
class CeleryConfig:
    """Celery configuration."""
    
    # Broker and result backend settings
    broker_url = settings.REDIS_URL
    result_backend = settings.REDIS_URL
    
    # Task settings
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    
    # Worker settings
    worker_prefetch_multiplier = 1  # Fair task distribution
    worker_max_tasks_per_child = 100  # Prevent memory leaks
    worker_concurrency = 4  # Default concurrency
    
    # Task timeouts
    task_time_limit = 30 * 60  # 30 minutes
    task_soft_time_limit = 25 * 60  # 25 minutes
    
    # Beat schedule (periodic tasks)
    beat_schedule: Dict[str, Dict[str, Any]] = {
        'update-business-metrics-hourly': {
            'task': 'app.tasks.metrics.update_business_metrics',
            'schedule': crontab(minute=0),  # Every hour
            'options': {'queue': 'metrics'}
        },
        'cleanup-old-data-daily': {
            'task': 'app.tasks.cleanup.cleanup_old_data',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            'options': {'queue': 'maintenance'}
        },
        'send-daily-digest': {
            'task': 'app.tasks.notifications.send_daily_digest',
            'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
            'options': {'queue': 'notifications'}
        }
    }
    
    # Task routes
    task_routes = {
        'app.tasks.metrics.*': {'queue': 'metrics'},
        'app.tasks.notifications.*': {'queue': 'notifications'},
        'app.tasks.cleanup.*': {'queue': 'maintenance'},
        'app.tasks.import.*': {'queue': 'import'},
        'app.tasks.export.*': {'queue': 'export'},
        'app.tasks.reports.*': {'queue': 'reports'},
    }
    
    # Task default queue
    task_default_queue = 'default'
    
    # Task soft time limits
    task_annotations = {
        'app.tasks.metrics.*': {'time_limit': 300, 'soft_time_limit': 270},
        'app.tasks.notifications.*': {'time_limit': 600, 'soft_time_limit': 540},
        'app.tasks.cleanup.*': {'time_limit': 1800, 'soft_time_limit': 1740},
        'app.tasks.import.*': {'time_limit': 3600, 'soft_time_limit': 3540},
        'app.tasks.export.*': {'time_limit': 3600, 'soft_time_limit': 3540},
        'app.tasks.reports.*': {'time_limit': 3600, 'soft_time_limit': 3540},
    }


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """Configure Celery loggers."""
    # Configure Celery logger
    logger.setLevel(logging.INFO)
    
    # Add file handler if LOG_FILE is set
    if settings.LOG_FILE:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


@after_setup_task_logger.connect
def setup_task_loggers(logger, *args, **kwargs):
    """Configure Celery task loggers."""
    # Configure task logger
    logger.setLevel(logging.INFO)
    
    # Add file handler if LOG_FILE is set
    if settings.LOG_FILE:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(task_id)s - %(task_name)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
