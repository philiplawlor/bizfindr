"""
Celery application factory for background task processing.
"""
import logging
import os
from typing import Any, Callable, Optional

from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from flask import Flask

from app.core.celery_config import CeleryConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app instance with proper configuration
celery_app = Celery(
    __name__,
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1'),
    include=[
        'app.tasks.metrics',
        'app.tasks.cleanup',
        'app.tasks.notifications',
        'app.tasks.import',
        'app.tasks.export',
        'app.tasks.reports'
    ]
)

# Configure Celery
try:
    celery_app.config_from_object(CeleryConfig)
except Exception as e:
    logger.error(f"Failed to configure Celery: {e}", exc_info=True)
    raise

# Set up event dispatcher
celery_app.conf.worker_send_task_events = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', '4'))
celery_app.conf.worker_max_tasks_per_child = 100
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True

@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """Handler for when worker is ready."""
    logger.info("Celery worker is ready")

@worker_shutdown.connect
def on_worker_shutdown(sender=None, **kwargs):
    """Handler for when worker is shutting down."""
    logger.info("Celery worker is shutting down")


def init_celery(app: Flask) -> Celery:
    """Initialize Celery with Flask app context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery application instance
    """
    # Configure Celery using settings from Flask app config
    celery_app.conf.update(app.config.get("CELERY_CONFIG", {}))
    
    # Set up Celery using the configuration class
    celery_app.config_from_object(CeleryConfig)
    
    # Set up task routing
    celery_app.conf.update(
        task_routes={
            'app.tasks.metrics.*': {'queue': 'metrics'},
            'app.tasks.notifications.*': {'queue': 'notifications'},
            'app.tasks.cleanup.*': {'queue': 'maintenance'},
            'app.tasks.import.*': {'queue': 'import'},
            'app.tasks.export.*': {'queue': 'export'},
            'app.tasks.reports.*': {'queue': 'reports'},
        },
        task_default_queue='default',
        task_default_exchange='default',
        task_default_routing_key='default',
    )
    
    # Set up task time limits
    celery_app.conf.task_time_limit = 30 * 60  # 30 minutes
    celery_app.conf.task_soft_time_limit = 25 * 60  # 25 minutes
    
    # Set up periodic tasks
    celery_app.conf.beat_schedule = CeleryConfig.beat_schedule
    
    # Set up task serialization
    celery_app.conf.task_serializer = 'json'
    celery_app.conf.result_serializer = 'json'
    celery_app.conf.accept_content = ['json']
    
    # Set up timezone
    celery_app.conf.timezone = 'UTC'
    celery_app.conf.enable_utc = True
    
    # Set up worker settings
    celery_app.conf.worker_prefetch_multiplier = 1
    celery_app.conf.worker_max_tasks_per_child = 100
    celery_app.conf.worker_concurrency = 4
    
    # Set up result backend
    celery_app.conf.result_backend = settings.REDIS_URL
    
    # Set up broker URL
    celery_app.conf.broker_url = settings.REDIS_URL
    
    class ContextTask(celery_app.Task):
        """Celery task with Flask application context."""
        
        def __call__(self, *args, **kwargs):
            """Execute task within Flask application context."""
            with app.app_context():
                return self.run(*args, **kwargs)
    
    # Set the default task class to include Flask app context
    celery_app.Task = ContextTask
    
    # Register tasks
    discover_tasks()
    
    logger.info("Celery initialized")
    return celery_app


def discover_tasks() -> None:
    """Discover and register all tasks."""
    # Import tasks to register them with Celery
    try:
        # Import tasks from all task modules
        from app.tasks import cleanup, metrics, notifications, imports, exports, reports
        logger.info("Discovered task modules")
    except ImportError as e:
        logger.warning(f"Failed to import task modules: {e}")


def get_task_logger(name: str) -> logging.Logger:
    """Get a logger for a task.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    return celery_app.log.get_default_logger()


def task(*args, **kwargs) -> Callable:
    """Decorator to create a Celery task with default settings."""
    # Set default options
    options = {
        'bind': True,
        'max_retries': 3,
        'default_retry_delay': 60,  # 1 minute
        'time_limit': 30 * 60,  # 30 minutes
        'soft_time_limit': 25 * 60,  # 25 minutes
    }
    options.update(kwargs)
    
    return celery_app.task(*args, **options)
