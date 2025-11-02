# Celery Background Tasks - Usage Guide

## 🎯 Overview

Minimal Celery setup for asynchronous email alerting. In **DEMO MODE**, emails are logged to console instead of being sent via SMTP.

## 🚀 Quick Start

### 1. Start Redis (Required)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or if Redis is already running locally
redis-cli ping  # Should return "PONG"
```

### 2. Start Celery Worker

```bash
# Navigate to service directory
cd services/alert-maintenance

# Start worker with INFO level logging
celery -A app.celery_app worker --loglevel=info

# For more verbose output (debugging)
celery -A app.celery_app worker --loglevel=debug

# On Windows (if you encounter issues)
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### 3. Queue Tasks from Python Code

```python
from app.tasks import send_email_alert, queue_alert_email

# Method 1: Direct delay() call
alert_data = {
    "alert_id": "550e8400-e29b-41d4-a716-446655440000",
    "equipment_id": "RADAR-LOC-001",
    "severity": "CRITICAL",
    "failure_probability": 0.82,
    "days_until_failure": 7,
    "recommended_action": "Schedule immediate maintenance",
    "health_score": 18.0,
    "confidence": "high"
}

# Queue task asynchronously
result = send_email_alert.delay(alert_data)
print(f"Task queued: {result.id}")

# Method 2: Using helper function
task_id = queue_alert_email(alert_data)
print(f"Task queued: {task_id}")
```

### 4. Check Task Status

```python
from app.tasks import get_task_status

# Get task status
status = get_task_status(task_id)
print(f"State: {status['state']}")
print(f"Ready: {status['ready']}")
print(f"Result: {status['result']}")
```

## 📝 Example Output (Demo Mode)

When a task is processed, you'll see this in the Celery worker logs:

```
======================================================================
📧 EMAIL ALERT NOTIFICATION
======================================================================
Task ID: 3a2e1d4c-7b5a-4f1e-9c8d-6e3f2a1b0c9d
Alert ID: 550e8400-e29b-41d4-a716-446655440000
Timestamp: 2025-11-02T10:30:00
----------------------------------------------------------------------
🚨 SEVERITY: CRITICAL
🔧 Equipment: RADAR-LOC-001
📊 Failure Probability: 82.00%
📅 Days Until Failure: 7
💊 Health Score: 18.0/100
🎯 Confidence: high
----------------------------------------------------------------------
📝 Recommended Action:
   Schedule immediate maintenance - equipment likely to fail within 7 days
======================================================================
✓ Email logged successfully (DEMO MODE)
======================================================================
```

## 🔧 Integration with FastAPI

### In your API endpoint:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import AlertGenerationService
from app.tasks import send_email_alert

router = APIRouter()

@router.post("/api/v1/alerts/generate")
async def generate_alert(
    equipment_id: str,
    sensor_data: dict,
    db: AsyncSession = Depends(get_db)
):
    # Generate alert using service
    service = AlertGenerationService(db)
    alert = await service.generate_alert_for_equipment(equipment_id, sensor_data)
    
    if alert:
        # Queue email alert task asynchronously
        alert_data = {
            "alert_id": alert.id,
            "equipment_id": alert.equipment_id,
            "severity": alert.severity,
            "failure_probability": alert.failure_probability,
            "days_until_failure": alert.days_until_failure,
            "recommended_action": alert.recommended_action,
            "health_score": alert.health_score,
            "confidence": alert.confidence
        }
        
        # Queue task (non-blocking)
        task_result = send_email_alert.delay(alert_data)
        
        return {
            "alert_id": alert.id,
            "status": "created",
            "email_task_id": task_result.id
        }
    
    return {"status": "no_alert_needed"}
```

## 🚀 Batch Processing

For processing multiple alerts:

```python
from app.tasks import send_batch_email_alerts

alerts_data = [alert_data_1, alert_data_2, alert_data_3]

# Queue batch task
result = send_batch_email_alerts.delay(alerts_data)
print(f"Batch task queued: {result.id}")

# Get result when ready
if result.ready():
    summary = result.get()
    print(f"Success: {summary['success']}, Failed: {summary['failed']}")
```

## 📊 Monitor Tasks

### Using Celery CLI

```bash
# Inspect active tasks
celery -A app.celery_app inspect active

# Inspect scheduled tasks
celery -A app.celery_app inspect scheduled

# Inspect registered tasks
celery -A app.celery_app inspect registered

# Get worker stats
celery -A app.celery_app inspect stats
```

### Using Flower (Optional Web UI)

```bash
# Install Flower
pip install flower

# Start Flower web interface
celery -A app.celery_app flower

# Access at: http://localhost:5555
```

## 🔐 Enable Production Email Sending

To enable actual SMTP email sending:

### 1. Update `.env` file:

```bash
EMAIL_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=alerts@drdo.gov.in
EMAIL_TO=maintenance@drdo.gov.in
```

### 2. Uncomment SMTP code in `app/tasks.py`:

Find the "PRODUCTION MODE" section (lines 112-177) and uncomment the code.

### 3. For Gmail, create App Password:

1. Go to Google Account Settings
2. Security → 2-Step Verification (enable if not enabled)
3. Security → App Passwords
4. Generate password for "Mail"
5. Use generated password as `SMTP_PASSWORD`

## ⚙️ Configuration

Key settings in `app/celery_app.py`:

```python
# Task time limits
task_time_limit=30          # 30 seconds max per task
task_soft_time_limit=25     # Soft limit at 25 seconds

# Result expiration
result_expires=3600         # Results expire after 1 hour

# Worker settings
worker_prefetch_multiplier=4
worker_max_tasks_per_child=1000
```

## 🐛 Troubleshooting

### Issue: "No connection to Redis"

```bash
# Check Redis is running
redis-cli ping

# Check Redis URL in .env
REDIS_URL=redis://localhost:6379/0
```

### Issue: "Tasks not executing"

```bash
# Restart Celery worker
# Press Ctrl+C to stop, then restart
celery -A app.celery_app worker --loglevel=info
```

### Issue: "Import errors"

```bash
# Make sure you're in the correct directory
cd services/alert-maintenance

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
$env:PYTHONPATH="$(pwd);$env:PYTHONPATH"  # Windows PowerShell
```

## 📈 Performance Tips

1. **Multiple Workers**: Start multiple workers for better throughput
   ```bash
   celery -A app.celery_app worker --concurrency=4 --loglevel=info
   ```

2. **Autoscaling**: Enable autoscaling based on load
   ```bash
   celery -A app.celery_app worker --autoscale=10,3 --loglevel=info
   ```

3. **Separate Queues**: Use different queues for priority tasks (advanced)

## 🧪 Testing Tasks

### Test task directly (synchronous):

```python
from app.tasks import send_email_alert

# Call directly (blocking)
result = send_email_alert(alert_data)
print(result)
```

### Test with pytest:

```python
import pytest
from app.tasks import send_email_alert

def test_send_email_alert():
    alert_data = {
        "alert_id": "test-123",
        "equipment_id": "TEST-001",
        "severity": "HIGH",
        "failure_probability": 0.75,
        "days_until_failure": 10,
        "recommended_action": "Test action"
    }
    
    # Call task directly (synchronous for testing)
    result = send_email_alert(alert_data)
    
    assert result["status"] == "logged"
    assert result["alert_id"] == "test-123"
```

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## ✅ Checklist for Production

- [ ] Redis is running and accessible
- [ ] Celery worker is running
- [ ] SMTP credentials configured (if email enabled)
- [ ] Worker monitoring setup (Flower/logs)
- [ ] Error alerting configured
- [ ] Task result cleanup scheduled
- [ ] Worker auto-restart configured (systemd/supervisor)

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-02
