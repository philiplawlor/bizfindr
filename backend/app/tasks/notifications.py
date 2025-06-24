"""
Background tasks for sending notifications.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

from pymongo import UpdateOne

from app.core.celery_app import task
from app.core.config import settings
from app.db.mongodb import get_database
from app.core.email import send_email

logger = logging.getLogger(__name__)

@task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300)
def send_email_notification(
    self,
    to_email: Union[str, List[str]],
    subject: str,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    priority: str = 'normal'
) -> Dict[str, Any]:
    """
    Send an email notification in the background.
    
    Args:
        to_email: Email address or list of email addresses to send to
        subject: Email subject
        template_name: Name of the email template to use
        context: Dictionary of template variables
        priority: Priority of the email ('high', 'normal', 'low')
        
    Returns:
        Dict with send status and message ID
    """
    try:
        if not context:
            context = {}
            
        # Add common context variables
        context.setdefault('app_name', settings.PROJECT_NAME)
        context.setdefault('current_year', datetime.utcnow().year)
        
        # Send the email
        message_id = send_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            context=context,
            priority=priority
        )
        
        logger.info(f"Sent email notification to {to_email} with subject: {subject}")
        return {
            "status": "success",
            "message_id": message_id,
            "recipient": to_email,
            "template": template_name
        }
        
    except Exception as exc:
        logger.error(f"Error sending email to {to_email}: {exc}", exc_info=True)
        self.retry(exc=exc)


@task(bind=True, max_retries=3, default_retry_delay=300, time_limit=1800)
def send_daily_digest(self) -> Dict[str, Any]:
    """
    Send daily digest emails to users.
    
    Returns:
        Dict with send statistics
    """
    try:
        db = get_database()
        stats = {
            "start_time": datetime.utcnow(),
            "emails_sent": 0,
            "users_processed": 0,
            "errors": []
        }
        
        # Get users who should receive the digest
        users = db.users.find({
            "email_notifications.daily_digest": True,
            "is_active": True,
            "email_verified": True
        })
        
        # Process each user
        for user in users:
            try:
                # Get content for the digest
                digest_content = _generate_daily_digest_content(user['_id'])
                
                if not digest_content['has_content']:
                    logger.debug(f"No new content for user {user['email']}, skipping digest")
                    continue
                
                # Send the digest email
                send_email_notification.delay(
                    to_email=user['email'],
                    subject=f"{settings.PROJECT_NAME} Daily Digest - {datetime.utcnow().strftime('%Y-%m-%d')}",
                    template_name="daily_digest",
                    context={
                        "user": user,
                        "digest": digest_content,
                        "unsubscribe_token": _generate_unsubscribe_token(user['_id'], 'daily_digest')
                    },
                    priority="low"
                )
                
                stats["emails_sent"] += 1
                
            except Exception as e:
                error_msg = f"Error processing digest for user {user.get('email', 'unknown')}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats["errors"].append(error_msg)
            
            stats["users_processed"] += 1
        
        # Update statistics
        stats["end_time"] = datetime.utcnow()
        stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        logger.info(
            f"Sent daily digest to {stats['emails_sent']} users in {stats['duration_seconds']:.2f} seconds. "
            f"Processed {stats['users_processed']} users with {len(stats['errors'])} errors"
        )
        
        return {
            "status": "success" if not stats["errors"] else "partial",
            "stats": stats
        }
        
    except Exception as exc:
        logger.error(f"Error in send_daily_digest: {exc}", exc_info=True)
        self.retry(exc=exc)


def _generate_daily_digest_content(user_id: str) -> Dict[str, Any]:
    """
    Generate content for a user's daily digest.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dict with digest content
    """
    db = get_database()
    
    # Get new notifications
    notifications = list(db.notifications.find({
        "user_id": user_id,
        "read": False,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}
    }).sort("created_at", -1).limit(10))
    
    # Get recent activity
    recent_activity = list(db.activities.find({
        "user_id": user_id,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}
    }).sort("created_at", -1).limit(10))
    
    # Get any other relevant content
    # This would be customized based on your application's needs
    
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "notifications": notifications,
        "recent_activity": recent_activity,
        "has_content": len(notifications) > 0 or len(recent_activity) > 0
    }


def _generate_unsubscribe_token(user_id: str, notification_type: str) -> str:
    """
    Generate an unsubscribe token for email notifications.
    
    Args:
        user_id: ID of the user
        notification_type: Type of notification to unsubscribe from
        
    Returns:
        JWT token for unsubscribing
    """
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "user_id": str(user_id),
        "notification_type": notification_type,
        "exp": datetime.utcnow() + timedelta(days=30)  # Token expires in 30 days
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300)
def send_welcome_email(self, user_id: str) -> Dict[str, Any]:
    """
    Send a welcome email to a new user.
    
    Args:
        user_id: ID of the new user
        
    Returns:
        Dict with send status
    """
    try:
        db = get_database()
        user = db.users.find_one({"_id": user_id})
        
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "error", "message": "User not found"}
        
        # Generate email verification token
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(days=7)  # 7 days to verify email
        )
        
        # Send welcome email with verification link
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        send_email_notification.delay(
            to_email=user['email'],
            subject=f"Welcome to {settings.PROJECT_NAME}!",
            template_name="welcome_email",
            context={
                "user": user,
                "verification_url": verification_url,
                "support_email": settings.SUPPORT_EMAIL
            },
            priority="high"
        )
        
        logger.info(f"Sent welcome email to {user['email']}")
        return {"status": "success", "user_id": str(user_id), "email_sent": True}
        
    except Exception as exc:
        logger.error(f"Error sending welcome email to user {user_id}: {exc}", exc_info=True)
        self.retry(exc=exc)
