"""
Background tasks for metrics and analytics processing.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from pymongo import UpdateOne

from app.core.celery_app import task
from app.db.mongodb import get_database
from app.services.business_service import BusinessService

logger = logging.getLogger(__name__)

@task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300)
def update_business_metrics(self, business_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Update business metrics in the background.
    
    Args:
        business_id: Optional business ID to update metrics for a specific business.
                    If None, updates metrics for all businesses.
                    
    Returns:
        Dict with operation status and statistics
    """
    try:
        db = get_database()
        business_service = BusinessService(db)
        
        if business_id:
            # Update metrics for a single business
            logger.info(f"Updating metrics for business: {business_id}")
            result = _update_single_business_metrics(business_service, business_id)
            return {"status": "success", "updated": 1, "business_id": business_id, "result": result}
        else:
            # Update metrics for all businesses
            logger.info("Updating metrics for all businesses")
            stats = _update_all_businesses_metrics(business_service)
            return {"status": "success", "updated": stats["processed"], "stats": stats}
            
    except Exception as exc:
        logger.error(f"Error updating business metrics: {exc}", exc_info=True)
        self.retry(exc=exc)


def _update_single_business_metrics(service: BusinessService, business_id: str) -> Dict[str, Any]:
    """Update metrics for a single business."""
    # Get the business
    business = service.get_business(business_id)
    if not business:
        logger.warning(f"Business not found: {business_id}")
        return {"status": "error", "message": "Business not found"}
    
    # Calculate metrics (example metrics - customize based on your needs)
    metrics = {
        "updated_at": datetime.utcnow(),
        "metrics": {
            "total_views": 0,  # Would come from analytics
            "active_listings": 0,  # Would be calculated
            "response_rate": 0.0,  # Would be calculated
            "rating_average": 0.0,  # Would come from reviews
            "review_count": 0,  # Would come from reviews
        }
    }
    
    # Update the business with new metrics
    update_result = service.update_business(
        business_id,
        {"$set": {"metrics": metrics}},
        update_metrics_only=True
    )
    
    return {"status": "success", "metrics_updated": update_result.modified_count > 0}


def _update_all_businesses_metrics(service: BusinessService) -> Dict[str, int]:
    """Update metrics for all businesses in batches."""
    db = service.db
    stats = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "start_time": datetime.utcnow()
    }
    
    # Process in batches to avoid memory issues
    batch_size = 100
    last_id = None
    
    while True:
        # Get a batch of business IDs
        query = {}
        if last_id:
            query["_id"] = {"$gt": last_id}
            
        cursor = db.businesses.find(
            query,
            {"_id": 1},
            sort=[("_id", 1)],
            limit=batch_size
        )
        
        batch = list(cursor)
        if not batch:
            break
            
        # Update metrics for each business in the batch
        for business in batch:
            try:
                business_id = str(business["_id"])
                _update_single_business_metrics(service, business_id)
                stats["succeeded"] += 1
            except Exception as e:
                logger.error(f"Error updating metrics for business {business['_id']}: {e}")
                stats["failed"] += 1
            finally:
                stats["processed"] += 1
                last_id = business["_id"]
    
    # Update statistics
    stats["end_time"] = datetime.utcnow()
    stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    
    # Log completion
    logger.info(
        f"Completed metrics update for {stats['processed']} businesses. "
        f"Succeeded: {stats['succeeded']}, Failed: {stats['failed']}, "
        f"Duration: {stats['duration_seconds']:.2f} seconds"
    )
    
    return stats


@task(bind=True, max_retries=3, default_retry_delay=300, time_limit=1800)
def generate_business_report(self, business_id: str, report_type: str, user_id: str) -> Dict[str, Any]:
    """
    Generate a business report in the background.
    
    Args:
        business_id: ID of the business to generate the report for
        report_type: Type of report to generate (e.g., 'monthly', 'annual', 'custom')
        user_id: ID of the user requesting the report
        
    Returns:
        Dict with report generation status and metadata
    """
    try:
        logger.info(f"Generating {report_type} report for business {business_id} requested by user {user_id}")
        
        # Simulate report generation (replace with actual implementation)
        # This would typically involve:
        # 1. Fetching business data
        # 2. Generating report content (PDF, Excel, etc.)
        # 3. Storing the report
        # 4. Sending notification to user
        
        # For now, just simulate some processing time
        import time
        time.sleep(5)  # Simulate processing time
        
        report_data = {
            "business_id": business_id,
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "requested_by": user_id,
            "status": "completed",
            "download_url": f"/api/v1/reports/{business_id}/{report_type}-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        }
        
        logger.info(f"Successfully generated report: {report_data}")
        return {"status": "success", "report": report_data}
        
    except Exception as exc:
        logger.error(f"Error generating business report: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=60)
