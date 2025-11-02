# DRDO Equipment Maintenance Prediction System - Start Services Script (Windows PowerShell)
# Starts all microservices in separate PowerShell windows

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Starting DRDO Equipment Maintenance Prediction System" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker services are running
Write-Host "[1/5] Checking Docker services..." -ForegroundColor Yellow
try {
    $postgresRunning = docker ps | Select-String "drdo_postgres"
    $redisRunning = docker ps | Select-String "drdo_redis"
    
    if (-not $postgresRunning -or -not $redisRunning) {
        Write-Host "Starting PostgreSQL and Redis..." -ForegroundColor Yellow
        docker-compose up -d postgres redis
        Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        Write-Host "PostgreSQL and Redis are already running" -ForegroundColor Green
    }
} catch {
    Write-Host "Warning: Could not check Docker services. Make sure Docker is running." -ForegroundColor Yellow
}

# Start Service 1: Sensor Data Ingestion (Port 8001)
Write-Host "`n[2/5] Starting Sensor Data Ingestion Service (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd sensor-data-ingestion-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8001"

Start-Sleep -Seconds 2

# Start Service 2: ML Prediction (Port 8002)
Write-Host "[3/5] Starting ML Prediction Service (Port 8002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd ml-prediction-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8002"

Start-Sleep -Seconds 2

# Start Service 3: Alert & Maintenance (Port 8003)
Write-Host "[4/5] Starting Alert & Maintenance Service (Port 8003)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd alert-maintenance-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8003"

Start-Sleep -Seconds 2

# Start Service 4: Dashboard (Port 8004)
Write-Host "[5/5] Starting Dashboard Service (Port 8004)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd dashboard-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8004"

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services are running at:" -ForegroundColor Yellow
Write-Host "  - Sensor Ingestion API: http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "  - ML Prediction API:    http://localhost:8002/docs" -ForegroundColor Cyan
Write-Host "  - Alert/Maintenance API: http://localhost:8003/docs" -ForegroundColor Cyan
Write-Host "  - Dashboard:            http://localhost:8004/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  Run .\scripts\stop_services.ps1 or close the PowerShell windows" -ForegroundColor Yellow
Write-Host ""
Write-Host "Logs are visible in each service window" -ForegroundColor Yellow
Write-Host ""
