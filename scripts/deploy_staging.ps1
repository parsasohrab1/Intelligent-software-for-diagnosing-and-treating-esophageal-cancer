# Staging deployment script for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "INEsCape Staging Deployment"
Write-Host "=========================================="

# Check if .env.staging exists
if (-not (Test-Path ".env.staging")) {
    Write-Host "Warning: .env.staging not found. Please create it from .env.staging template." -ForegroundColor Yellow
    exit 1
}

# Check Docker
try {
    docker ps | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Build images
Write-Host "Building Docker images..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml build --no-cache

# Stop existing containers
Write-Host "Stopping existing staging containers..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml down

# Start services
Write-Host "Starting staging services..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml up -d

# Wait for services
Write-Host "Waiting for services to be ready..." -ForegroundColor Green
Start-Sleep -Seconds 30

# Check services
Write-Host "Checking service health..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml ps

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml exec -T postgres psql -U inescape_staging_user -d inescape_staging -f /docker-entrypoint-initdb.d/init.sql

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml exec -T app alembic upgrade head

# Create admin user
Write-Host "Creating admin user..." -ForegroundColor Green
docker-compose -f docker-compose.staging.yml exec -T app python scripts/create_admin_user.py `
    --username admin `
    --email admin@staging.example.com `
    --password admin123

# Health check
Write-Host "Performing health check..." -ForegroundColor Green
Start-Sleep -Seconds 10
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/health" -UseBasicParsing
    Write-Host "Health check passed!" -ForegroundColor Green
} catch {
    Write-Host "Health check failed, but services may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Staging deployment complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Services:"
Write-Host "  - API: http://localhost:8001"
Write-Host "  - API Docs: http://localhost:8001/docs"
Write-Host "  - Grafana: http://localhost:3002"
Write-Host "  - Prometheus: http://localhost:9091"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker-compose -f docker-compose.staging.yml logs -f"
Write-Host ""
Write-Host "To stop:"
Write-Host "  docker-compose -f docker-compose.staging.yml down"
Write-Host ""

