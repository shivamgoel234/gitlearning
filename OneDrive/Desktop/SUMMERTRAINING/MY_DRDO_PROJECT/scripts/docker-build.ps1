# ═══════════════════════════════════════════════════════════════════
# Docker Build Script for DRDO Equipment Maintenance System
# Builds all microservice images with security best practices
# ═══════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🐳 Building DRDO Equipment Maintenance Docker Images" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_NAME = "drdo-equipment-maintenance"
$REGISTRY = $env:REGISTRY ?? "localhost"
$VERSION = "v1.0.0"

# Enable Docker BuildKit for better caching and security
$env:DOCKER_BUILDKIT = "1"
$env:BUILDKIT_PROGRESS = "auto"

# Services to build
$SERVICES = @("sensor-ingestion", "ml-prediction", "alert-maintenance", "dashboard")

$SUCCESS_COUNT = 0
$FAILED_COUNT = 0
$START_TIME = Get-Date

foreach ($service in $SERVICES) {
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Blue
    Write-Host "🔨 Building: $service" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Blue
    
    $servicePath = ".\services\$service"
    
    if (-Not (Test-Path $servicePath)) {
        Write-Host "❌ ERROR: Service directory not found: $servicePath" -ForegroundColor Red
        $FAILED_COUNT++
        continue
    }
    
    $imageTag = "${REGISTRY}/${PROJECT_NAME}-${service}"
    
    try {
        # Build with multi-stage Dockerfile
        docker build `
            --tag "${imageTag}:latest" `
            --tag "${imageTag}:${VERSION}" `
            --build-arg BUILDKIT_INLINE_CACHE=1 `
            --compress `
            $servicePath
        
        if ($LASTEXITCODE -eq 0) {
            # Get image size
            $imageInfo = docker images --format "{{.Size}}" "${imageTag}:latest" | Select-Object -First 1
            
            Write-Host "✅ SUCCESS: $service built (Size: $imageInfo)" -ForegroundColor Green
            $SUCCESS_COUNT++
        } else {
            Write-Host "❌ FAILED: $service build failed with exit code $LASTEXITCODE" -ForegroundColor Red
            $FAILED_COUNT++
        }
    }
    catch {
        Write-Host "❌ EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
        $FAILED_COUNT++
    }
    
    Write-Host ""
}

# Build summary
$END_TIME = Get-Date
$DURATION = ($END_TIME - $START_TIME).TotalSeconds

Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📊 Build Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Successful: $SUCCESS_COUNT" -ForegroundColor Green
Write-Host "❌ Failed: $FAILED_COUNT" -ForegroundColor Red
Write-Host "⏱️  Duration: $([math]::Round($DURATION, 2)) seconds" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($FAILED_COUNT -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Some builds failed. Check the errors above." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host ""
    Write-Host "🎉 All services built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: docker-compose up -d" -ForegroundColor White
    Write-Host "  2. Check status: docker-compose ps" -ForegroundColor White
    Write-Host "  3. View logs: docker-compose logs -f" -ForegroundColor White
    exit 0
}
