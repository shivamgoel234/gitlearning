# ═══════════════════════════════════════════════════════════════════
# Docker Compose Start Script for DRDO Equipment Maintenance System
# Starts all microservices with dependency management
# ═══════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🚀 Starting DRDO Equipment Maintenance System" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose is available
if (-Not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: docker-compose not found!" -ForegroundColor Red
    Write-Host "Please install Docker Compose: https://docs.docker.com/compose/install/" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env file created" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Edit .env file with your settings before continuing!" -ForegroundColor Yellow
        Write-Host "   - Update POSTGRES_PASSWORD" -ForegroundColor White
        Write-Host "   - Configure email settings (SMTP)" -ForegroundColor White
        Write-Host "   - Set any other environment-specific values" -ForegroundColor White
        Write-Host ""
        
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "Exiting. Please edit .env and run again." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "❌ ERROR: .env.example not found either!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🐳 Starting services with Docker Compose..." -ForegroundColor Blue
Write-Host ""

# Start services in detached mode
try {
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: docker-compose up failed!" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📊 Service Status" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Show service status
docker-compose ps

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ System Started Successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   Sensor Ingestion API:  http://localhost:8001/docs" -ForegroundColor White
Write-Host "   ML Prediction API:     http://localhost:8002/docs" -ForegroundColor White
Write-Host "   Alert & Maintenance:   http://localhost:8003/docs" -ForegroundColor White
Write-Host "   Dashboard:             http://localhost:8004" -ForegroundColor White
Write-Host ""
Write-Host "📊 Database:" -ForegroundColor Cyan
Write-Host "   PostgreSQL:            localhost:5432" -ForegroundColor White
Write-Host "   Redis:                 localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs:             docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services:         docker-compose down" -ForegroundColor White
Write-Host "   Restart service:       docker-compose restart <service-name>" -ForegroundColor White
Write-Host "   View service status:   docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Ready to use!" -ForegroundColor Green
