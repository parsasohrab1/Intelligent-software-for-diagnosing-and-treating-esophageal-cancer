# Script to start both backend and frontend servers
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "INEsCape - Starting All Servers" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get the project root directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# Stop any existing processes
Write-Host "Stopping existing processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check ports
Write-Host "Checking ports..." -ForegroundColor Yellow
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8001) {
    Write-Host "⚠️  Port 8001 is in use. Stopping process..." -ForegroundColor Yellow
    $processes = $port8001 | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processes) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

if ($port3000) {
    Write-Host "⚠️  Port 3000 is in use. Stopping process..." -ForegroundColor Yellow
    $processes = $port3000 | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processes) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Start Backend
Write-Host ""
Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host "Backend will be available at: http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "API Docs: http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host ""

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
}

# Wait for backend to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test backend
$backendReady = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/patients/dashboard-simple" -Method Get -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✅ Backend is running!" -ForegroundColor Green
        $backendReady = $true
        break
    } catch {
        Write-Host "Waiting for backend... ($($i + 1)/10)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start. Check logs above." -ForegroundColor Red
    Write-Host "You can check backend logs with: Get-Job -Id $($backendJob.Id) | Receive-Job" -ForegroundColor Yellow
}

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:projectRoot\frontend"
    npm run dev
}

# Wait for frontend to start
Write-Host "Waiting for frontend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Test frontend
$frontendReady = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✅ Frontend is running!" -ForegroundColor Green
        $frontendReady = $true
        break
    } catch {
        Write-Host "Waiting for frontend... ($($i + 1)/10)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $frontendReady) {
    Write-Host "❌ Frontend failed to start. Check logs above." -ForegroundColor Red
    Write-Host "You can check frontend logs with: Get-Job -Id $($frontendJob.Id) | Receive-Job" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Server Status Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend:  $(if ($backendReady) { '✅ Running' } else { '❌ Not Ready' })" -ForegroundColor $(if ($backendReady) { 'Green' } else { 'Red' })
Write-Host "Frontend: $(if ($frontendReady) { '✅ Running' } else { '❌ Not Ready' })" -ForegroundColor $(if ($frontendReady) { 'Green' } else { 'Red' })
Write-Host ""
Write-Host "Backend URL:  http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Dashboard:    http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  Backend:  Get-Job -Id $($backendJob.Id) | Receive-Job" -ForegroundColor White
Write-Host "  Frontend: Get-Job -Id $($frontendJob.Id) | Receive-Job" -ForegroundColor White
Write-Host ""
Write-Host "To stop servers:" -ForegroundColor Yellow
Write-Host "  Stop-Job -Id $($backendJob.Id), $($frontendJob.Id)" -ForegroundColor White
Write-Host "  Remove-Job -Id $($backendJob.Id), $($frontendJob.Id)" -ForegroundColor White
Write-Host ""

# Keep script running and show logs
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 5
        # Show any new output from jobs
        $backendOutput = Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        $frontendOutput = Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
        
        if ($backendOutput) {
            Write-Host "[Backend] $backendOutput" -ForegroundColor Magenta
        }
        if ($frontendOutput) {
            Write-Host "[Frontend] $frontendOutput" -ForegroundColor Blue
        }
    }
} finally {
    Write-Host ""
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "Servers stopped." -ForegroundColor Green
}
