# Simple Live Run Script
# اجرای ساده Backend و Frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INEsCape Live - Simple Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Check if frontend exists
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    Write-Host "Please make sure you're in the project root" -ForegroundColor Yellow
    exit 1
}

# Start Backend
Write-Host "Starting Backend on http://localhost:8001" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8001/docs" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload" -WindowStyle Normal

# Wait a bit
Start-Sleep -Seconds 3

# Check if node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host ""
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location $projectRoot
}

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend (Dashboard) on http://localhost:3000" -ForegroundColor Green
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm run dev" -WindowStyle Normal
Set-Location $projectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "  Backend API:    http://localhost:8001" -ForegroundColor White
Write-Host "  API Docs:       http://localhost:8001/docs" -ForegroundColor White
Write-Host "  Frontend:       http://localhost:3000" -ForegroundColor White
Write-Host "  Dashboard:      http://localhost:3000 (Dashboard page)" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Default Login:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Each service runs in a separate window" -ForegroundColor Yellow
Write-Host "   Close the windows to stop the services" -ForegroundColor Yellow

