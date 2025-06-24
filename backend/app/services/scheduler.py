"""
Scheduler Service

This module handles scheduling periodic tasks for the BizFindr application,
such as fetching new data from the CT.gov API at regular intervals.
"""
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def init_scheduler(app):
    """Initialize the scheduler with the Flask application context.
    
    Args:
        app: The Flask application instance
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning('Scheduler already initialized')
        return
    
    # Configure the scheduler
    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 60 * 60  # 1 hour
    }
    
    scheduler = BackgroundScheduler(job_defaults=job_defaults, timezone='UTC')
    
    # Add the fetch job if enabled
    if app.config.get('ENABLE_SCHEDULED_FETCH', True):
        fetch_interval = app.config.get('FETCH_INTERVAL_HOURS', 24)
        
        scheduler.add_job(
            id='fetch_latest_data',
            func=fetch_job,
            args=[app],
            trigger=IntervalTrigger(
                hours=fetch_interval,
                start_date=datetime.utcnow() + timedelta(seconds=10)  # Start 10 seconds after init
            ),
            replace_existing=True
        )
        
        logger.info(f"Scheduled data fetch to run every {fetch_interval} hours")
    
    # Start the scheduler
    scheduler.start()
    logger.info('Scheduler started')
    
    # Add a shutdown handler
    import atexit
    atexit.register(shutdown_scheduler)

def shutdown_scheduler():
    """Shut down the scheduler gracefully."""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info('Scheduler shut down')

def fetch_job(app):
    """Job function to fetch the latest data.
    
    Args:
        app: The Flask application instance
    """
    with app.app_context():
        try:
            logger.info('Starting scheduled data fetch...')
            
            # Import here to avoid circular imports
            from .data_fetcher import fetch_latest_data
            
            # Execute the fetch
            result = fetch_latest_data()
            
            if result.get('success'):
                logger.info(
                    f"Scheduled fetch completed: {result.get('count', 0)} records processed, "
                    f"{result.get('errors', 0)} errors"
                )
            else:
                logger.error(f"Scheduled fetch failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in scheduled job: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

def run_immediate_fetch():
    """Run the fetch job immediately.
    
    Returns:
        dict: Result of the fetch operation
    """
    if scheduler is None:
        return {
            'success': False,
            'error': 'Scheduler not initialized',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Find the fetch job
    job = scheduler.get_job('fetch_latest_data')
    if job is None:
        return {
            'success': False,
            'error': 'Fetch job not found',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Run the job immediately
    try:
        return job.func(*job.args, **job.kwargs)
    except Exception as e:
        logger.error(f"Error running immediate fetch: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
