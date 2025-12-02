# Staging Environment Test Script for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "INEsCape Staging Environment Test"
Write-Host "=========================================="
Write-Host ""

# Check Docker
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check .env.staging
if (-not (Test-Path ".env.staging")) {
    Write-Host "❌ .env.staging not found. Please create it." -ForegroundColor Red
    exit 1
}
Write-Host "✅ .env.staging exists" -ForegroundColor Green

# Load environment variables
$envVars = Get-Content .env.staging | Where-Object { $_ -match '^[^#]' -and $_ -match '=' }
foreach ($line in $envVars) {
    $parts = $line -split '=', 2
    if ($parts.Length -eq 2) {
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Check services status
Write-Host ""
Write-Host "Checking services status..." -ForegroundColor Yellow
$services = docker-compose -f docker-compose.staging.yml ps --services
$runningServices = docker-compose -f docker-compose.staging.yml ps --services --filter "status=running"

if ($runningServices.Count -eq 0) {
    Write-Host "⚠️  No services are running. Starting services..." -ForegroundColor Yellow
    docker-compose -f docker-compose.staging.yml up -d
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
} else {
    Write-Host "✅ Services are running: $($runningServices -join ', ')" -ForegroundColor Green
}

# Wait for services to be healthy
Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
$allHealthy = $false

while ($waited -lt $maxWait -and -not $allHealthy) {
    Start-Sleep -Seconds 5
    $waited += 5
    
    $healthStatus = docker-compose -f docker-compose.staging.yml ps
    $unhealthy = $healthStatus | Select-String -Pattern "unhealthy|starting"
    
    if (-not $unhealthy) {
        $allHealthy = $true
        Write-Host "✅ All services are healthy" -ForegroundColor Green
    } else {
        Write-Host "  Waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
    }
}

# Test API Health Endpoint
Write-Host ""
Write-Host "Testing API health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API health check passed" -ForegroundColor Green
        $response.Content | ConvertFrom-Json | Format-List
    } else {
        Write-Host "⚠️  API returned status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ API health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Make sure the app service is running and healthy" -ForegroundColor Yellow
}

# Test API Docs
Write-Host ""
Write-Host "Testing API documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/docs" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API documentation is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  API documentation check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test OpenAPI Schema
Write-Host ""
Write-Host "Testing OpenAPI schema..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/openapi.json" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OpenAPI schema is accessible" -ForegroundColor Green
        $schema = $response.Content | ConvertFrom-Json
        Write-Host "   Version: $($schema.info.version)" -ForegroundColor Gray
        Write-Host "   Endpoints: $($schema.paths.PSObject.Properties.Count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  OpenAPI schema check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Check database connections
Write-Host ""
Write-Host "Testing database connections..." -ForegroundColor Yellow

# PostgreSQL
try {
    $pgResult = docker-compose -f docker-compose.staging.yml exec -T postgres pg_isready -U inescape_staging_user
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PostgreSQL check failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  PostgreSQL check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# MongoDB
try {
    $mongoResult = docker-compose -f docker-compose.staging.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  MongoDB check failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  MongoDB check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Redis
try {
    $redisResult = docker-compose -f docker-compose.staging.yml exec -T redis redis-cli ping
    if ($redisResult -match "PONG") {
        Write-Host "✅ Redis is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis check failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Redis check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Service status summary
Write-Host ""
Write-Host "=========================================="
Write-Host "Service Status Summary"
Write-Host "=========================================="
docker-compose -f docker-compose.staging.yml ps

Write-Host ""
Write-Host "=========================================="
Write-Host "Test Complete"
Write-Host "=========================================="
Write-Host ""
Write-Host "Access URLs:"
Write-Host "  - API: http://localhost:8001"
Write-Host "  - API Docs: http://localhost:8001/docs"
Write-Host "  - Grafana: http://localhost:3002"
Write-Host "  - Prometheus: http://localhost:9091"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker-compose -f docker-compose.staging.yml logs -f"
Write-Host ""

