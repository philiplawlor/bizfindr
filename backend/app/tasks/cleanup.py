"""
Background tasks for cleanup and maintenance operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from pymongo import UpdateOne, DeleteMany

from app.core.celery_app import task
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

@task(bind=True, max_retries=3, default_retry_delay=300, time_limit=3600)
def cleanup_old_data(self, days_old: int = 90) -> Dict[str, Any]:
    """
    Clean up old data from the database.
    
    Args:
        days_old: Number of days of data to keep
        
    Returns:
        Dict with cleanup statistics
    """
    try:
        db = get_database()
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        stats = {
            "start_time": datetime.utcnow(),
            "cutoff_date": cutoff_date,
            "collections_processed": 0,
            "documents_deleted": 0,
            "errors": []
        }
        
        # Define collections and their cleanup queries
        cleanup_config = [
            {
                "name": "audit_logs",
                "query": {"timestamp": {"$lt": cutoff_date}},
                "description": "Old audit logs"
            },
            {
                "name": "notifications",
                "query": {
                    "created_at": {"$lt": cutoff_date},
                    "status": "read"
                },
                "description": "Old read notifications"
            },
            {
                "name": "temp_files",
                "query": {
                    "created_at": {"$lt": cutoff_date}
                },
                "description": "Old temporary files"
            }
        ]
        
        # Process each collection
        for config in cleanup_config:
            collection_name = config["name"]
            if collection_name not in db.list_collection_names():
                continue
                
            try:
                collection = db[collection_name]
                result = collection.delete_many(config["query"])
                
                if result.deleted_count > 0:
                    logger.info(
                        f"Deleted {result.deleted_count} {config['description']} "
                        f"older than {days_old} days from {collection_name}"
                    )
                    stats["documents_deleted"] += result.deleted_count
                    stats["collections_processed"] += 1
                    
            except Exception as e:
                error_msg = f"Error cleaning up {collection_name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats["errors"].append(error_msg)
        
        # Update statistics
        stats["end_time"] = datetime.utcnow()
        stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        logger.info(
            f"Completed data cleanup. Processed {stats['collections_processed']} collections, "
            f"deleted {stats['documents_deleted']} documents in {stats['duration_seconds']:.2f} seconds"
        )
        
        return {
            "status": "success" if not stats["errors"] else "partial",
            "stats": stats
        }
        
    except Exception as exc:
        logger.error(f"Error in cleanup_old_data: {exc}", exc_info=True)
        self.retry(exc=exc)


@task(bind=True, max_retries=3, default_retry_delay=300, time_limit=1800)
def optimize_database(self) -> Dict[str, Any]:
    """
    Optimize database performance by running maintenance operations.
    
    Returns:
        Dict with optimization results
    """
    try:
        db = get_database()
        stats = {
            "start_time": datetime.utcnow(),
            "operations": [],
            "errors": []
        }
        
        # Run database commands to optimize performance
        try:
            # Rebuild all indexes
            for collection_name in db.list_collection_names():
                try:
                    start = datetime.utcnow()
                    db.command("reIndex", collection_name)
                    duration = (datetime.utcnow() - start).total_seconds()
                    stats["operations"].append({
                        "operation": "reindex",
                        "collection": collection_name,
                        "duration_seconds": duration,
                        "status": "success"
                    })
                    logger.info(f"Rebuilt indexes for collection: {collection_name} in {duration:.2f}s")
                except Exception as e:
                    error_msg = f"Error rebuilding indexes for {collection_name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats["errors"].append(error_msg)
            
            # Run compact command (if supported)
            try:
                start = datetime.utcnow()
                db.command("compact", force=True)
                duration = (datetime.utcnow() - start).total_seconds()
                stats["operations"].append({
                    "operation": "compact",
                    "duration_seconds": duration,
                    "status": "success"
                })
                logger.info(f"Compacted database in {duration:.2f}s")
            except Exception as e:
                error_msg = f"Error compacting database: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Database optimization error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            stats["errors"].append(error_msg)
        
        # Update statistics
        stats["end_time"] = datetime.utcnow()
        stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        logger.info(
            f"Completed database optimization in {stats['duration_seconds']:.2f} seconds. "
            f"Performed {len(stats['operations'])} operations with {len(stats['errors'])} errors"
        )
        
        return {
            "status": "success" if not stats["errors"] else "partial",
            "stats": stats
        }
        
    except Exception as exc:
        logger.error(f"Error in optimize_database: {exc}", exc_info=True)
        self.retry(exc=exc)
