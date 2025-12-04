# Simple Backend Startup Script
Write-Host "=========================================="
Write-Host "Starting INEsCape Backend (Simple Mode)"
Write-Host "=========================================="
Write-Host ""

# Stop existing processes
Write-Host "Stopping existing Python processes..."
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check if port is available
$portCheck = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "⚠️  Port 8001 is in use. Trying to free it..."
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Starting backend server on http://127.0.0.1:8001"
Write-Host "Press Ctrl+C to stop"
Write-Host ""
Write-Host "If you see errors, check:"
Write-Host "  1. PostgreSQL is running (docker-compose up -d postgres)"
Write-Host "  2. All dependencies are installed (pip install -r requirements.txt)"
Write-Host "  3. No syntax errors in code"
Write-Host ""

# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload --log-level warning

