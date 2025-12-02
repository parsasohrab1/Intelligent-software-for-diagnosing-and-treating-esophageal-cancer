# Script to start both backend and frontend
Write-Host "=========================================="
Write-Host "INEsCape - Start Backend & Frontend"
Write-Host "=========================================="
Write-Host ""

# Check ports
Write-Host "Checking ports..."
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8001) {
    Write-Host "⚠️  Port 8001 is in use"
} else {
    Write-Host "✅ Port 8001 is available"
}

if ($port3000) {
    Write-Host "⚠️  Port 3000 is in use"
} else {
    Write-Host "✅ Port 3000 is available"
}

Write-Host ""

# Start Backend
Write-Host "Starting Backend (Port 8001)..."
$backendProcess = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8001" -PassThru -WindowStyle Normal
Write-Host "✅ Backend started (PID: $($backendProcess.Id))"
Write-Host "   URL: http://127.0.0.1:8001/docs"
Start-Sleep -Seconds 3

# Setup Frontend .env
Write-Host ""
Write-Host "Setting up Frontend..."
if (Test-Path "frontend") {
    $envFile = "frontend/.env"
    if (-not (Test-Path $envFile)) {
        Set-Content -Path $envFile -Value "VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1"
        Write-Host "✅ Created frontend/.env"
    }
    
    # Check if node_modules exists
    if (-not (Test-Path "frontend/node_modules")) {
        Write-Host "Installing Frontend dependencies..."
        Set-Location frontend
        npm install
        Set-Location ..
    }
    
    # Start Frontend
    Write-Host ""
    Write-Host "Starting Frontend (Port 3000)..."
    $frontendProcess = Start-Process npm -ArgumentList "run", "dev" -WorkingDirectory "frontend" -PassThru -WindowStyle Normal
    Write-Host "✅ Frontend started (PID: $($frontendProcess.Id))"
    Write-Host "   URL: http://localhost:3000"
} else {
    Write-Host "❌ Frontend directory not found"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "✅ Both servers are starting..."
Write-Host "=========================================="
Write-Host ""
Write-Host "🌐 Access:"
Write-Host "   - Frontend: http://localhost:3000"
Write-Host "   - Backend API: http://127.0.0.1:8001/docs"
Write-Host ""
Write-Host "⏳ Please wait a few seconds for servers to start"
Write-Host ""
Write-Host "Press any key to open Frontend in browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Start-Process "http://localhost:3000"

