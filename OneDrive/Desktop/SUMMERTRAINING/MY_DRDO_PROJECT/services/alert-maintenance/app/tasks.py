"""
Celery background tasks for Alert & Maintenance service.

Minimal implementation with email alerting for demo purposes.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="send_email_alert", bind=True)
def send_email_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email alert for equipment failure (SIMPLIFIED FOR DEMO).
    
    In demo mode, this task logs the alert to console instead of
    actually sending emails. This is sufficient for demonstration
    and testing purposes.
    
    Args:
        alert_data: Dictionary containing alert information:
            - alert_id: str - Alert UUID
            - equipment_id: str - Equipment identifier
            - severity: str - Alert severity (CRITICAL, HIGH, etc.)
            - failure_probability: float - Failure probability (0-1)
            - days_until_failure: int - Days until predicted failure
            - recommended_action: str - Recommended action
            - health_score: float (optional) - Equipment health score
            - confidence: str (optional) - Prediction confidence
    
    Returns:
        Dictionary with task execution results:
            - status: "logged" or "sent"
            - alert_id: str
            - timestamp: str
            - task_id: str
    
    Example:
        >>> from app.tasks import send_email_alert
        >>> alert_data = {
        ...     "alert_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "equipment_id": "RADAR-LOC-001",
        ...     "severity": "CRITICAL",
        ...     "failure_probability": 0.82,
        ...     "days_until_failure": 7,
        ...     "recommended_action": "Schedule immediate maintenance"
        ... }
        >>> # Queue task asynchronously
        >>> result = send_email_alert.delay(alert_data)
        >>> # Or call synchronously (for testing)
        >>> result = send_email_alert(alert_data)
    
    To enable actual email sending in production:
        1. Set EMAIL_ENABLED=True in .env
        2. Configure SMTP settings (host, port, user, password)
        3. Uncomment SMTP code section below
    """
    task_id = self.request.id
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Extract alert data
        alert_id = alert_data.get("alert_id", "unknown")
        equipment_id = alert_data.get("equipment_id", "unknown")
        severity = alert_data.get("severity", "UNKNOWN")
        failure_probability = alert_data.get("failure_probability", 0.0)
        days_until_failure = alert_data.get("days_until_failure", 0)
        recommended_action = alert_data.get("recommended_action", "Contact maintenance team")
        health_score = alert_data.get("health_score")
        confidence = alert_data.get("confidence", "unknown")
        
        # ==================================================================
        # DEMO MODE: Log email to console
        # ==================================================================
        logger.info("=" * 70)
        logger.info("📧 EMAIL ALERT NOTIFICATION")
        logger.info("=" * 70)
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Alert ID: {alert_id}")
        logger.info(f"Timestamp: {timestamp}")
        logger.info("-" * 70)
        logger.info(f"🚨 SEVERITY: {severity}")
        logger.info(f"🔧 Equipment: {equipment_id}")
        logger.info(f"📊 Failure Probability: {failure_probability:.2%}")
        logger.info(f"📅 Days Until Failure: {days_until_failure}")
        
        if health_score is not None:
            logger.info(f"💊 Health Score: {health_score:.1f}/100")
        
        logger.info(f"🎯 Confidence: {confidence}")
        logger.info("-" * 70)
        logger.info(f"📝 Recommended Action:")
        logger.info(f"   {recommended_action}")
        logger.info("=" * 70)
        logger.info(f"✓ Email logged successfully (DEMO MODE)")
        logger.info("=" * 70)
        
        result = {
            "status": "logged",
            "alert_id": alert_id,
            "equipment_id": equipment_id,
            "timestamp": timestamp,
            "task_id": task_id,
            "severity": severity
        }
        
        # ==================================================================
        # PRODUCTION MODE: Uncomment to enable actual email sending
        # ==================================================================
        # import os
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        # import smtplib
        # 
        # EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
        # 
        # if EMAIL_ENABLED:
        #     try:
        #         # SMTP Configuration
        #         SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
        #         SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        #         SMTP_USER = os.getenv("SMTP_USER")
        #         SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
        #         EMAIL_FROM = os.getenv("EMAIL_FROM", "alerts@drdo.gov.in")
        #         EMAIL_TO = os.getenv("EMAIL_TO", "maintenance@drdo.gov.in")
        #         
        #         # Create email message
        #         msg = MIMEMultipart("alternative")
        #         msg["Subject"] = f"[{severity}] Equipment Alert: {equipment_id}"
        #         msg["From"] = EMAIL_FROM
        #         msg["To"] = EMAIL_TO
        #         
        #         # Email body (HTML)
        #         html_body = f"""
        #         <html>
        #           <body>
        #             <h2 style="color: {'red' if severity == 'CRITICAL' else 'orange'};">
        #               {severity} Equipment Alert
        #             </h2>
        #             <p><strong>Equipment:</strong> {equipment_id}</p>
        #             <p><strong>Failure Probability:</strong> {failure_probability:.2%}</p>
        #             <p><strong>Days Until Failure:</strong> {days_until_failure}</p>
        #             <p><strong>Health Score:</strong> {health_score:.1f}/100</p>
        #             <p><strong>Confidence:</strong> {confidence}</p>
        #             <hr>
        #             <h3>Recommended Action:</h3>
        #             <p>{recommended_action}</p>
        #             <hr>
        #             <p><small>Alert ID: {alert_id}</small></p>
        #             <p><small>Generated: {timestamp}</small></p>
        #           </body>
        #         </html>
        #         """
        #         
        #         # Attach HTML body
        #         msg.attach(MIMEText(html_body, "html"))
        #         
        #         # Send email via SMTP
        #         with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        #             server.starttls()
        #             if SMTP_USER and SMTP_PASSWORD:
        #                 server.login(SMTP_USER, SMTP_PASSWORD)
        #             server.send_message(msg)
        #         
        #         logger.info(f"✓ Email sent to {EMAIL_TO}")
        #         result["status"] = "sent"
        #         result["recipient"] = EMAIL_TO
        #         
        #     except Exception as email_error:
        #         logger.error(f"Failed to send email: {email_error}")
        #         result["email_error"] = str(email_error)
        # ==================================================================
        
        return result
        
    except KeyError as e:
        error_msg = f"Missing required field in alert_data: {str(e)}"
        logger.error(f"Task failed: {error_msg}")
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"Email alert task failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@celery_app.task(name="send_batch_email_alerts", bind=True)
def send_batch_email_alerts(self, alerts_data: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send multiple email alerts in batch (OPTIONAL).
    
    Useful for processing multiple alerts efficiently.
    
    Args:
        alerts_data: List of alert data dictionaries
    
    Returns:
        Summary of batch processing results
    
    Example:
        >>> from app.tasks import send_batch_email_alerts
        >>> alerts = [alert_data_1, alert_data_2, alert_data_3]
        >>> result = send_batch_email_alerts.delay(alerts)
    """
    task_id = self.request.id
    timestamp = datetime.utcnow().isoformat()
    
    logger.info(f"Processing batch of {len(alerts_data)} email alerts")
    
    results = {
        "task_id": task_id,
        "timestamp": timestamp,
        "total": len(alerts_data),
        "success": 0,
        "failed": 0,
        "alerts": []
    }
    
    for alert_data in alerts_data:
        try:
            # Process each alert
            result = send_email_alert(alert_data)
            results["success"] += 1
            results["alerts"].append({
                "alert_id": alert_data.get("alert_id"),
                "status": "success"
            })
        except Exception as e:
            results["failed"] += 1
            results["alerts"].append({
                "alert_id": alert_data.get("alert_id"),
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Failed to process alert: {str(e)}")
    
    logger.info(
        f"Batch processing complete: "
        f"{results['success']} succeeded, "
        f"{results['failed']} failed"
    )
    
    return results


# ==================================================================
# TASK UTILITIES
# ==================================================================

def queue_alert_email(alert_data: Dict[str, Any]) -> str:
    """
    Helper function to queue email alert task.
    
    Args:
        alert_data: Alert information dictionary
    
    Returns:
        Task ID (UUID)
    
    Example:
        >>> task_id = queue_alert_email(alert_data)
        >>> print(f"Task queued: {task_id}")
    """
    result = send_email_alert.delay(alert_data)
    logger.info(f"Email alert task queued: {result.id}")
    return result.id


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a queued task.
    
    Args:
        task_id: Task UUID
    
    Returns:
        Dictionary with task status information
    
    Example:
        >>> status = get_task_status(task_id)
        >>> print(f"Task state: {status['state']}")
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() else None,
        "info": str(result.info) if result.info else None
    }
