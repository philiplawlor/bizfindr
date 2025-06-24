"""
Background tasks for the BizFindr application.

This package contains all background tasks that are processed asynchronously
using Celery. Tasks are organized into submodules based on their functionality.
"""
import logging

from app.core.celery_app import celery_app, task

logger = logging.getLogger(__name__)

# Import all task modules to ensure they are registered with Celery
# noinspection PyUnresolvedReferences
from . import cleanup, metrics, notifications, imports, exports, reports

__all__ = ['celery_app', 'task']
