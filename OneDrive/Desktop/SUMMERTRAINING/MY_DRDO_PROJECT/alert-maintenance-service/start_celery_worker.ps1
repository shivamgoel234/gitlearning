# Start Celery Worker for Alert & Maintenance Service
# Run this in a separate terminal window

Write-Host "Starting Celery Worker..." -ForegroundColor Cyan

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Start Celery worker
celery -A app.celery_app worker --loglevel=info --pool=solo -Q notifications,maintenance,periodic,reports

# Note: Use --pool=solo on Windows (gevent/eventlet don't work well on Windows)
# For production on Linux, use: celery -A app.celery_app worker --loglevel=info
