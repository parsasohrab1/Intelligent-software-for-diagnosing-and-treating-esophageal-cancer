# Quick server startup script for Windows
Write-Host "=========================================="
Write-Host "INEsCape Server Startup"
Write-Host "=========================================="
Write-Host ""

# Check if port 8000 is in use
$portInUse = netstat -ano | findstr :8000
if ($portInUse) {
    Write-Host "⚠️  Port 8000 is already in use"
    Write-Host "Checking if it's our server..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 2 -UseBasicParsing
        Write-Host "✅ Server is already running at http://localhost:8000"
        Write-Host "API Docs: http://localhost:8000/docs"
        exit 0
    } catch {
        Write-Host "❌ Port 8000 is in use by another process"
        Write-Host "Please stop the process or change the port"
        exit 1
    }
}

# Check Docker
Write-Host "Checking Docker services..."
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running"
} catch {
    Write-Host "⚠️  Docker might not be running"
    Write-Host "Starting Docker services..."
    docker-compose up -d
    Start-Sleep -Seconds 5
}

# Start server
Write-Host ""
Write-Host "Starting FastAPI server..."
Write-Host "Server will be available at: http://localhost:8000"
Write-Host "API Documentation: http://localhost:8000/docs"
Write-Host "MRI Report API: http://localhost:8000/api/v1/imaging/mri"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

