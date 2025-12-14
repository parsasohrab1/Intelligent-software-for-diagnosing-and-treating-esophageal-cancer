# Dashboard Startup Script
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting INEsCape Dashboard" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "c:\Users\asus\Documents\companies\ithub\AI\products\clones\cancer diagnosing\Intelligent-software-for-diagnosing-and-treating-esophageal-cancer"

# Stop any existing processes
Write-Host "Stopping existing processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check and free ports
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($port8001) {
    Write-Host "Port 8001 is in use. Freeing..." -ForegroundColor Yellow
    $port8001 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "Port 3000 is in use. Freeing..." -ForegroundColor Yellow
    $port3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

# Start Backend
Write-Host ""
Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host "Backend will be available at: http://127.0.0.1:8001" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; Write-Host 'Starting Backend...' -ForegroundColor Green; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload" -WindowStyle Normal

# Wait for backend
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; Write-Host 'Starting Frontend...' -ForegroundColor Green; npm run dev" -WindowStyle Normal

# Wait and check
Write-Host ""
Write-Host "Waiting for servers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check status
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Server Status" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$backendRunning = $false
$frontendRunning = $false

# Check backend
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
    $backendRunning = $true
    Write-Host "✅ Backend: Running on http://127.0.0.1:8001" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend: Not responding (check the backend window for errors)" -ForegroundColor Red
}

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    $frontendRunning = $true
    Write-Host "✅ Frontend: Running on http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend: Not responding (check the frontend window for errors)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Access URLs" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Dashboard:    http://localhost:3000/dashboard" -ForegroundColor White
Write-Host "Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "Backend API:  http://127.0.0.1:8001" -ForegroundColor White
Write-Host "API Docs:     http://127.0.0.1:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "Two PowerShell windows have been opened:" -ForegroundColor Yellow
Write-Host "  - One for Backend (port 8001)" -ForegroundColor White
Write-Host "  - One for Frontend (port 3000)" -ForegroundColor White
Write-Host ""
Write-Host "If servers are not running, check those windows for error messages." -ForegroundColor Yellow
Write-Host ""
