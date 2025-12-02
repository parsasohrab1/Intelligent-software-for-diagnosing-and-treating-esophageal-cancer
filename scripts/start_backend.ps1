# Script to start backend server correctly
Write-Host "=========================================="
Write-Host "INEsCape Backend Server Startup"
Write-Host "=========================================="
Write-Host ""

# Check if port 8000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Port 8000 is in use. Stopping existing processes..."
    $processes = $portInUse | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $processes) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "   Stopped process $pid"
        } catch {
            Write-Host "   Could not stop process $pid"
        }
    }
    Start-Sleep -Seconds 2
}

# Check Docker (optional, for database)
Write-Host "Checking Docker..."
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running"
    Write-Host "Starting Docker services..."
    docker-compose up -d
    Start-Sleep -Seconds 5
} catch {
    Write-Host "⚠️  Docker might not be running (database features may not work)"
}

# Start server
Write-Host ""
Write-Host "Starting FastAPI server..."
Write-Host "Server will be available at: http://localhost:8000"
Write-Host "API Documentation: http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

# Check if port 8000 is available, otherwise use 8001
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "⚠️  Port 8000 is in use. Using port 8001 instead..."
    $port = 8001
} else {
    $port = 8000
}

Write-Host "Starting server on port $port..."
Write-Host ""

# Start uvicorn with correct settings
uvicorn app.main:app --reload --host 127.0.0.1 --port $port

