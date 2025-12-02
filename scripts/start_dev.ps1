# Development startup script for Windows PowerShell

Write-Host "=========================================="
Write-Host "INEsCape Development Environment"
Write-Host "=========================================="

# Check Docker
try {
    docker ps | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop."
    exit 1
}

# Start services
Write-Host "Starting Docker services..."
docker-compose up -d

# Wait for services
Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Check services
python scripts/check_services.py

# Initialize if needed
if (-not (Test-Path ".db_initialized")) {
    Write-Host "Initializing database..."
    python scripts/init_database.py
    New-Item -ItemType File -Path ".db_initialized" | Out-Null
}

# Create admin user if needed
Write-Host "Checking admin user..."
python scripts/create_admin_user.py `
    --username admin `
    --email admin@example.com `
    --password admin123

# Start server
Write-Host "Starting development server..."
Write-Host "API will be available at: http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"
Write-Host ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

