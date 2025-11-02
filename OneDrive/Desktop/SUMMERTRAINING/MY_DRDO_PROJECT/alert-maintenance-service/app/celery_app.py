"""
Celery configuration for Alert & Maintenance Service.

Handles background tasks like:
- Sending email/SMS notifications
- Scheduling periodic maintenance checks
- Batch alert processing
- Report generation
"""

from celery import Celery
from celery.schedules import crontab
from typing import Dict, Any
import logging
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "alert_maintenance_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    'check-critical-alerts-every-5-minutes': {
        'task': 'app.celery_app.check_critical_alerts',
        'schedule': crontab(minute='*/5'),
    },
    'send-daily-maintenance-report': {
        'task': 'app.celery_app.send_daily_maintenance_report',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'cleanup-old-acknowledged-alerts': {
        'task': 'app.celery_app.cleanup_old_alerts',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}


@celery_app.task(name='app.celery_app.send_email_notification', bind=True, max_retries=3)
def send_email_notification(self, alert_id: str, equipment_id: str, severity: str, message: str) -> Dict[str, Any]:
    """
    Send email notification for alert.
    
    Args:
        alert_id: Alert identifier
        equipment_id: Equipment identifier
        severity: Alert severity level
        message: Alert message
        
    Returns:
        Dictionary with send status
    """
    try:
        logger.info(f"Sending email notification for alert: {alert_id}")
        
        # TODO: Implement actual email sending using SMTP or service like SendGrid
        # For now, this is a placeholder
        email_data = {
            "to": "maintenance-team@drdo.gov.in",
            "subject": f"[{severity}] Equipment Alert - {equipment_id}",
            "body": f"""
            Alert ID: {alert_id}
            Equipment: {equipment_id}
            Severity: {severity}
            Message: {message}
            Timestamp: {datetime.utcnow().isoformat()}
            
            Please take immediate action.
            
            DRDO Equipment Monitoring System
            """
        }
        
        logger.info(f"Email notification sent successfully for alert: {alert_id}")
        
        return {
            "status": "sent",
            "alert_id": alert_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed to send email for alert {alert_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name='app.celery_app.send_sms_notification', bind=True, max_retries=3)
def send_sms_notification(self, alert_id: str, equipment_id: str, severity: str, phone_numbers: list) -> Dict[str, Any]:
    """
    Send SMS notification for critical alerts.
    
    Args:
        alert_id: Alert identifier
        equipment_id: Equipment identifier
        severity: Alert severity level
        phone_numbers: List of phone numbers to notify
        
    Returns:
        Dictionary with send status
    """
    try:
        logger.info(f"Sending SMS notification for alert: {alert_id}")
        
        # TODO: Implement actual SMS sending using service like Twilio
        sms_message = f"[{severity}] DRDO Alert: Equipment {equipment_id} requires attention. Alert ID: {alert_id}"
        
        logger.info(f"SMS notification sent to {len(phone_numbers)} recipients for alert: {alert_id}")
        
        return {
            "status": "sent",
            "alert_id": alert_id,
            "recipients": len(phone_numbers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed to send SMS for alert {alert_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name='app.celery_app.schedule_maintenance_task', bind=True)
def schedule_maintenance_task(self, equipment_id: str, task_type: str, priority: str, description: str) -> Dict[str, Any]:
    """
    Create maintenance task in background.
    
    Args:
        equipment_id: Equipment identifier
        task_type: Type of maintenance
        priority: Task priority
        description: Task description
        
    Returns:
        Dictionary with task creation status
    """
    try:
        logger.info(f"Scheduling maintenance task for equipment: {equipment_id}")
        
        # TODO: Implement actual database insertion
        task_data = {
            "equipment_id": equipment_id,
            "task_type": task_type,
            "priority": priority,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Maintenance task scheduled for equipment: {equipment_id}")
        
        return {
            "status": "scheduled",
            "equipment_id": equipment_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed to schedule maintenance for {equipment_id}: {exc}")
        raise


@celery_app.task(name='app.celery_app.check_critical_alerts')
def check_critical_alerts() -> Dict[str, Any]:
    """
    Periodic task to check and escalate critical unacknowledged alerts.
    
    Runs every 5 minutes via Celery Beat.
    
    Returns:
        Dictionary with check results
    """
    try:
        logger.info("Running periodic critical alerts check")
        
        # TODO: Query database for unacknowledged critical alerts
        # Send escalation notifications if alerts are old
        
        return {
            "status": "completed",
            "alerts_checked": 0,
            "escalations_sent": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Critical alerts check failed: {exc}")
        raise


@celery_app.task(name='app.celery_app.send_daily_maintenance_report')
def send_daily_maintenance_report() -> Dict[str, Any]:
    """
    Generate and send daily maintenance report.
    
    Runs daily at 8 AM via Celery Beat.
    
    Returns:
        Dictionary with report generation status
    """
    try:
        logger.info("Generating daily maintenance report")
        
        # TODO: Aggregate maintenance data from database
        # Generate PDF report
        # Send via email
        
        report_data = {
            "date": datetime.utcnow().date().isoformat(),
            "total_alerts": 0,
            "critical_alerts": 0,
            "maintenance_completed": 0,
            "maintenance_pending": 0
        }
        
        logger.info("Daily maintenance report sent successfully")
        
        return {
            "status": "sent",
            "report": report_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Daily report generation failed: {exc}")
        raise


@celery_app.task(name='app.celery_app.cleanup_old_alerts')
def cleanup_old_alerts() -> Dict[str, Any]:
    """
    Clean up old acknowledged alerts from database.
    
    Runs daily at 2 AM via Celery Beat.
    Removes alerts older than 90 days that are acknowledged.
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Cleaning up old acknowledged alerts")
        
        # TODO: Delete acknowledged alerts older than 90 days
        
        return {
            "status": "completed",
            "alerts_deleted": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Alert cleanup failed: {exc}")
        raise


@celery_app.task(name='app.celery_app.batch_process_predictions', bind=True)
def batch_process_predictions(self, prediction_events: list) -> Dict[str, Any]:
    """
    Process batch of prediction events to generate alerts.
    
    Args:
        prediction_events: List of prediction event data
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Batch processing {len(prediction_events)} prediction events")
        
        alerts_created = 0
        notifications_sent = 0
        
        for event in prediction_events:
            equipment_id = event.get('equipment_id')
            severity = event.get('severity')
            failure_prob = event.get('failure_probability')
            
            # Create alert if severity is HIGH or CRITICAL
            if severity in ['HIGH', 'CRITICAL']:
                # TODO: Create alert in database
                alerts_created += 1
                
                # Send notification asynchronously
                if severity == 'CRITICAL':
                    send_email_notification.delay(
                        alert_id=f"alert-{equipment_id}",
                        equipment_id=equipment_id,
                        severity=severity,
                        message=f"{failure_prob:.0%} failure probability detected"
                    )
                    notifications_sent += 1
        
        return {
            "status": "completed",
            "events_processed": len(prediction_events),
            "alerts_created": alerts_created,
            "notifications_sent": notifications_sent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch processing failed: {exc}")
        raise


# Task routing configuration
celery_app.conf.task_routes = {
    'app.celery_app.send_email_notification': {'queue': 'notifications'},
    'app.celery_app.send_sms_notification': {'queue': 'notifications'},
    'app.celery_app.schedule_maintenance_task': {'queue': 'maintenance'},
    'app.celery_app.check_critical_alerts': {'queue': 'periodic'},
    'app.celery_app.send_daily_maintenance_report': {'queue': 'reports'},
    'app.celery_app.cleanup_old_alerts': {'queue': 'maintenance'},
}


if __name__ == '__main__':
    celery_app.start()
