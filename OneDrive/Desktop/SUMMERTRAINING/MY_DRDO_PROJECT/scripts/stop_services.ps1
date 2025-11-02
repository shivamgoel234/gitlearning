# DRDO Equipment Maintenance Prediction System - Stop Services Script (Windows PowerShell)
# Stops all running microservices

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Stopping DRDO Equipment Maintenance Prediction System" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Stop Python/Uvicorn processes
Write-Host "[1/2] Stopping microservices..." -ForegroundColor Yellow

$ports = @(8001, 8002, 8003, 8004)

foreach ($port in $ports) {
    try {
        $connections = netstat -ano | Select-String ":$port" | Select-String "LISTENING"
        
        foreach ($connection in $connections) {
            $processId = ($connection -split '\s+')[-1]
            if ($processId -and $processId -match '^\d+$') {
                Write-Host "  Stopping process on port $port (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Host "  No process found on port $port" -ForegroundColor Gray
    }
}

Write-Host "All microservices stopped" -ForegroundColor Green

# Optionally stop Docker services
Write-Host "`n[2/2] Docker services..." -ForegroundColor Yellow
Write-Host "Docker services (PostgreSQL, Redis) are still running." -ForegroundColor Yellow
Write-Host "To stop them, run: docker-compose down" -ForegroundColor Cyan
Write-Host "To keep data, run: docker-compose stop" -ForegroundColor Cyan

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host "Services stopped successfully!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
