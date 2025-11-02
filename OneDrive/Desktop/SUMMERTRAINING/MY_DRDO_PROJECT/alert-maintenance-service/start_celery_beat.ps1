# Start Celery Beat Scheduler for Alert & Maintenance Service
# Run this in a separate terminal window
# This handles periodic tasks (cron-like scheduling)

Write-Host "Starting Celery Beat Scheduler..." -ForegroundColor Cyan

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Start Celery beat
celery -A app.celery_app beat --loglevel=info
