# Script to start backend server
Write-Host "Starting INEsCape Backend Server..." -ForegroundColor Cyan
Write-Host ""

# Check if port 8001 is available
$portInUse = netstat -ano | Select-String -Pattern ":8001.*LISTENING"
if ($portInUse) {
    Write-Host "Port 8001 is already in use!" -ForegroundColor Yellow
    Write-Host "Stopping existing processes..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start the server
Write-Host "Starting server on http://localhost:8001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

