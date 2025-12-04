# Script to setup database and generate data for dashboard
# This script will:
# 1. Check Docker Desktop status
# 2. Start Docker services
# 3. Initialize database
# 4. Generate sample data

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INEsCape Dashboard Data Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker Desktop
Write-Host "Step 1: Checking Docker Desktop..." -ForegroundColor Yellow
$dockerRunning = $false
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Desktop is running" -ForegroundColor Green
        $dockerRunning = $true
    } else {
        Write-Host "✗ Docker Desktop is not running" -ForegroundColor Red
        Write-Host "  Please start Docker Desktop and wait for it to fully start, then run this script again." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "✗ Docker Desktop is not running" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and wait for it to fully start, then run this script again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Start Docker services
Write-Host ""
Write-Host "Step 2: Starting Docker services (PostgreSQL, MongoDB, Redis)..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start Docker services" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker services started" -ForegroundColor Green
Write-Host "  Waiting for services to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 3: Check service status
Write-Host ""
Write-Host "Step 3: Checking service status..." -ForegroundColor Yellow
docker-compose ps

# Step 4: Initialize database
Write-Host ""
Write-Host "Step 4: Initializing database tables..." -ForegroundColor Yellow
python scripts/init_database.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to initialize database" -ForegroundColor Red
    Write-Host "  Waiting a bit longer for PostgreSQL to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    python scripts/init_database.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Still failed. Please check Docker services manually." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Database initialized" -ForegroundColor Green

# Step 5: Generate sample data
Write-Host ""
Write-Host "Step 5: Generating sample data for dashboard..." -ForegroundColor Yellow
Write-Host "  This will generate 50 patients with 40% cancer ratio..." -ForegroundColor Yellow

python scripts/generate_and_display_mri_data.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to generate data" -ForegroundColor Red
    Write-Host "  Trying alternative method via API..." -ForegroundColor Yellow
    
    # Try using API endpoint
    $body = @{
        n_patients = 50
        cancer_ratio = 0.4
        seed = 42
        save_to_db = $true
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/synthetic-data/generate" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body
        
        Write-Host "✓ Data generated via API" -ForegroundColor Green
        Write-Host "  Patients: $($response.n_patients)" -ForegroundColor Cyan
        Write-Host "  Cancer: $($response.n_cancer)" -ForegroundColor Cyan
        Write-Host "  Normal: $($response.n_normal)" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ API method also failed. Please check backend server is running." -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "✓ Data generated successfully" -ForegroundColor Green
}

# Step 6: Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  2. API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  3. Frontend Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "The dashboard should now show data!" -ForegroundColor Green
Write-Host ""

