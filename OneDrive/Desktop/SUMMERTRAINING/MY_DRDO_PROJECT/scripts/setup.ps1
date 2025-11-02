# DRDO Equipment Maintenance Prediction System - Setup Script (Windows PowerShell)
# Initializes the development environment

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "DRDO Equipment Maintenance Prediction System - Setup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
    
    # Check if Python 3.11+
    if ($pythonVersion -notmatch "Python 3\.1[1-9]") {
        Write-Host "Warning: Python 3.11+ is recommended" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Docker
Write-Host "`n[2/7] Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "Found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Warning: Docker not found. Docker Compose will not work." -ForegroundColor Yellow
}

# Create virtual environments for each service
Write-Host "`n[3/7] Creating virtual environments..." -ForegroundColor Yellow

$services = @("sensor-data-ingestion-service", "ml-prediction-service", "alert-maintenance-service", "dashboard-service")

foreach ($service in $services) {
    Write-Host "  Creating venv for $service..." -ForegroundColor Cyan
    Set-Location $service
    python -m venv venv
    Set-Location ..
}

Write-Host "Virtual environments created successfully!" -ForegroundColor Green

# Install dependencies
Write-Host "`n[4/7] Installing dependencies..." -ForegroundColor Yellow

foreach ($service in $services) {
    Write-Host "  Installing dependencies for $service..." -ForegroundColor Cyan
    Set-Location $service
    & .\venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    Set-Location ..
}

Write-Host "Dependencies installed successfully!" -ForegroundColor Green

# Create .env files from examples
Write-Host "`n[5/7] Creating environment files..." -ForegroundColor Yellow

foreach ($service in $services) {
    $envExample = "$service\.env.example"
    $envFile = "$service\.env"
    
    if (Test-Path $envExample) {
        if (-not (Test-Path $envFile)) {
            Copy-Item $envExample $envFile
            Write-Host "  Created $envFile" -ForegroundColor Green
        } else {
            Write-Host "  $envFile already exists, skipping..." -ForegroundColor Yellow
        }
    }
}

# Train ML model
Write-Host "`n[6/7] Training ML model..." -ForegroundColor Yellow
python scripts\train_model.py

# Create necessary directories
Write-Host "`n[7/7] Creating necessary directories..." -ForegroundColor Yellow

$directories = @(
    "ml-prediction-service\models",
    "logs",
    "data"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created directory: $dir" -ForegroundColor Green
    }
}

# Summary
Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env files in each service directory with your configuration"
Write-Host "  2. Start PostgreSQL and Redis: docker-compose up -d postgres redis"
Write-Host "  3. Run services: .\scripts\start_services.ps1"
Write-Host "  4. Access API documentation:"
Write-Host "     - Sensor Ingestion: http://localhost:8001/docs"
Write-Host "     - ML Prediction: http://localhost:8002/docs"
Write-Host "     - Alert Maintenance: http://localhost:8003/docs"
Write-Host "     - Dashboard: http://localhost:8004"
Write-Host ""
