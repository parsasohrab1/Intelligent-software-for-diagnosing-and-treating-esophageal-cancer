# Script to generate all data for dashboard
Write-Host "=========================================="
Write-Host "Generate All Dashboard Data"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check Backend
Write-Host "Step 1: Checking Backend..."
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "✅ Backend is running"
    $backendRunning = $true
} catch {
    Write-Host "❌ Backend is not running"
    Write-Host "   Starting Backend..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
    Write-Host "⏳ Waiting for Backend to start (15 seconds)..."
    Start-Sleep -Seconds 15
    
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Backend is now running"
        $backendRunning = $true
    } catch {
        Write-Host "❌ Backend failed to start"
        Write-Host "   Please start manually: python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
    }
}
Write-Host ""

# Step 2: Check Docker
Write-Host "Step 2: Checking Docker Services..."
try {
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $postgresRunning = $dockerStatus | Select-String -Pattern "postgres"
        if (-not $postgresRunning) {
            Write-Host "⚠️  Starting Docker services..."
            docker-compose up -d
            Start-Sleep -Seconds 10
        } else {
            Write-Host "✅ Docker services are running"
        }
    }
} catch {
    Write-Host "⚠️  Could not check Docker"
}
Write-Host ""

# Step 3: Generate data using API
if ($backendRunning) {
    Write-Host "Step 3: Generating data via API..."
    Write-Host ""
    
    $body = @{
        n_patients = 100
        cancer_ratio = 0.4
        save_to_db = $true
        seed = 42
    } | ConvertTo-Json
    
    try {
        Write-Host "   Sending request to generate 100 patients..."
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/synthetic-data/generate" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 300
        
        if ($response.StatusCode -eq 200) {
            $result = $response.Content | ConvertFrom-Json
            Write-Host "✅ Data generated successfully!"
            Write-Host "   Patients: $($result.n_patients)"
            Write-Host "   Cancer: $($result.n_cancer)"
            Write-Host "   Normal: $($result.n_normal)"
        }
    } catch {
        Write-Host "❌ Error generating data via API: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "   Trying alternative method (direct database)..."
        Write-Host ""
        python scripts/generate_and_display_mri_data.py
    }
} else {
    Write-Host "Step 3: Generating data directly (Backend not available)..."
    Write-Host ""
    python scripts/generate_and_display_mri_data.py
}
Write-Host ""

# Step 4: Verify data
Write-Host "Step 4: Verifying generated data..."
Start-Sleep -Seconds 3

$endpoints = @(
    @{ Name = "Patients"; Url = "/api/v1/patients" },
    @{ Name = "MRI Images"; Url = "/api/v1/imaging/mri" },
    @{ Name = "MRI Reports"; Url = "/api/v1/imaging/mri/reports" }
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001$($endpoint.Url)" -TimeoutSec 5 -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        $count = if ($data -is [array]) { $data.Count } else { if ($data.count) { $data.count } else { 0 } }
        Write-Host "   ✅ $($endpoint.Name): $count items"
    } catch {
        Write-Host "   ⚠️  $($endpoint.Name): Error"
    }
}
Write-Host ""

# Step 5: Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host ""
Write-Host "✅ Data generation complete!"
Write-Host ""
Write-Host "🌐 Next Steps:"
Write-Host "   1. Refresh Frontend: http://localhost:3000"
Write-Host "   2. Check Dashboard: http://localhost:3000/dashboard"
Write-Host "   3. Check Patients: http://localhost:3000/patients"
Write-Host "   4. Check MRI Report: http://localhost:3000/mri"
Write-Host ""
Write-Host "💡 If data still doesn't show:"
Write-Host "   - Hard refresh: Ctrl+F5"
Write-Host "   - Check Browser DevTools (F12) for errors"
Write-Host "   - Verify Backend is running: http://127.0.0.1:8001/api/v1/health"
Write-Host ""

