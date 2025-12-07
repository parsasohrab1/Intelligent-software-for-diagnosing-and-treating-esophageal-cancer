# Run Live: Backend, Frontend & Dashboard
# اجرای Live: Backend، Frontend و Dashboard

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INEsCape Live Server Startup" -ForegroundColor Cyan
Write-Host "  Backend + Frontend + Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running (for databases)
Write-Host "Checking Docker services..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Docker is not running. Starting Docker services..." -ForegroundColor Yellow
    Write-Host "Starting PostgreSQL, MongoDB, Redis..." -ForegroundColor Yellow
    docker-compose up -d postgres mongodb redis
    Start-Sleep -Seconds 10
}

# Check if databases are ready
Write-Host ""
Write-Host "Waiting for databases to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 1: Setup Database (if needed)
Write-Host ""
Write-Host "Step 1: Setting up database..." -ForegroundColor Cyan
if (Test-Path "scripts\create_migration.py") {
    Write-Host "Creating database tables..." -ForegroundColor Yellow
    python scripts\create_migration.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database tables created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database setup may have issues, continuing..." -ForegroundColor Yellow
    }
}

# Step 2: Seed initial data (if needed)
Write-Host ""
Write-Host "Step 2: Seeding initial data..." -ForegroundColor Cyan
if (Test-Path "scripts\seed_initial_data.py") {
    Write-Host "Seeding initial data..." -ForegroundColor Yellow
    python scripts\seed_initial_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Initial data seeded" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Data seeding may have issues, continuing..." -ForegroundColor Yellow
    }
}

# Step 3: Start Backend
Write-Host ""
Write-Host "Step 3: Starting Backend Server..." -ForegroundColor Cyan
Write-Host "Backend will run on: http://localhost:8001" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8001/docs" -ForegroundColor Green
Write-Host ""

# Check if port 8001 is in use
$backendPort = netstat -ano | Select-String -Pattern ":8001.*LISTENING"
if ($backendPort) {
    Write-Host "⚠️  Port 8001 is already in use!" -ForegroundColor Yellow
    Write-Host "Stopping existing backend processes..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
}

Write-Host "✅ Backend server starting..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Step 4: Start Frontend (Dashboard)
Write-Host ""
Write-Host "Step 4: Starting Frontend (Dashboard)..." -ForegroundColor Cyan
Write-Host "Frontend will run on: http://localhost:3000" -ForegroundColor Green
Write-Host ""

# Check if frontend directory exists
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    Write-Host "Please make sure you're in the project root directory" -ForegroundColor Yellow
    Stop-Job $backendJob
    Remove-Job $backendJob
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# Check if port 3000 is in use
$frontendPort = netstat -ano | Select-String -Pattern ":3000.*LISTENING"
if ($frontendPort) {
    Write-Host "⚠️  Port 3000 is already in use!" -ForegroundColor Yellow
}

# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location frontend
    npm run dev
}

Write-Host "✅ Frontend server starting..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Display status
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ All Services Started!" -ForegroundColor Green
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
Write-Host "⚠️  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if jobs are still running
        $backendStatus = Get-Job -Id $backendJob.Id | Select-Object -ExpandProperty State
        $frontendStatus = Get-Job -Id $frontendJob.Id | Select-Object -ExpandProperty State
        
        if ($backendStatus -eq "Failed" -or $frontendStatus -eq "Failed") {
            Write-Host ""
            Write-Host "❌ One or more services failed!" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host ""
    Write-Host "Stopping all services..." -ForegroundColor Yellow
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    
    # Kill any remaining processes
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

