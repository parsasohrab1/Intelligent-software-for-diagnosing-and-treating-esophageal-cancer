# Script to load all data for dashboard
Write-Host "=========================================="
Write-Host "Load All Dashboard Data"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check Backend
Write-Host "Step 1: Checking Backend..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "✅ Backend is running (Status: $($response.StatusCode))"
} catch {
    Write-Host "❌ Backend is not running"
    Write-Host ""
    Write-Host "Starting Backend..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
    Write-Host "⏳ Waiting for Backend to start (10 seconds)..."
    Start-Sleep -Seconds 10
    
    # Retry
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Backend is now running"
    } catch {
        Write-Host "❌ Backend failed to start. Please start manually:"
        Write-Host "   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
        exit 1
    }
}
Write-Host ""

# Step 2: Check Docker Services
Write-Host "Step 2: Checking Docker Services..."
try {
    $dockerStatus = docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running"
        $postgresRunning = $dockerStatus | Select-String -Pattern "postgres"
        if ($postgresRunning) {
            Write-Host "✅ PostgreSQL container is running"
        } else {
            Write-Host "⚠️  PostgreSQL container not found"
            Write-Host "   Starting Docker services..."
            docker-compose up -d
            Start-Sleep -Seconds 5
        }
    } else {
        Write-Host "⚠️  Docker may not be running or accessible"
    }
} catch {
    Write-Host "⚠️  Could not check Docker status"
}
Write-Host ""

# Step 3: Check existing data
Write-Host "Step 3: Checking existing data..."
try {
    $patients = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients" -TimeoutSec 5 -UseBasicParsing
    $data = $patients.Content | ConvertFrom-Json
    $patientCount = if ($data -is [array]) { $data.Count } else { 0 }
    Write-Host "   Patients in database: $patientCount"
    
    if ($patientCount -eq 0) {
        Write-Host ""
        Write-Host "⚠️  No data found. Generating data..."
        Write-Host ""
        
        # Generate data using Python script
        Write-Host "Generating synthetic data..."
        python scripts/generate_and_display_mri_data.py
        
        Write-Host ""
        Write-Host "⏳ Waiting for data to be saved (3 seconds)..."
        Start-Sleep -Seconds 3
        
        # Verify data was created
        try {
            $patients = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients" -TimeoutSec 5 -UseBasicParsing
            $data = $patients.Content | ConvertFrom-Json
            $newCount = if ($data -is [array]) { $data.Count } else { 0 }
            Write-Host "✅ Data generated! Patients: $newCount"
        } catch {
            Write-Host "⚠️  Could not verify data generation"
        }
    } else {
        Write-Host "✅ Data already exists"
    }
} catch {
    Write-Host "⚠️  Could not check data. Error: $($_.Exception.Message)"
    Write-Host "   This might be normal if database is empty or not connected"
    Write-Host ""
    Write-Host "Attempting to generate data anyway..."
    python scripts/generate_and_display_mri_data.py
}
Write-Host ""

# Step 4: Test all dashboard endpoints
Write-Host "Step 4: Testing Dashboard API Endpoints..."
$endpoints = @(
    @{ Name = "Patients"; Url = "/api/v1/patients" },
    @{ Name = "Data Collection Stats"; Url = "/api/v1/data-collection/metadata/statistics" },
    @{ Name = "ML Models"; Url = "/api/v1/ml-models/models" },
    @{ Name = "MRI Images"; Url = "/api/v1/imaging/mri" },
    @{ Name = "MRI Reports"; Url = "/api/v1/imaging/mri/reports" }
)

$allWorking = $true
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001$($endpoint.Url)" -TimeoutSec 5 -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        $count = if ($data -is [array]) { $data.Count } else { if ($data.count) { $data.count } else { "N/A" } }
        Write-Host "   ✅ $($endpoint.Name): OK (Status: $($response.StatusCode), Count: $count)"
    } catch {
        Write-Host "   ⚠️  $($endpoint.Name): Error - $($_.Exception.Message)"
        $allWorking = $false
    }
}
Write-Host ""

# Step 5: Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host ""

if ($allWorking) {
    Write-Host "✅ All endpoints are working"
} else {
    Write-Host "⚠️  Some endpoints have issues"
}

Write-Host ""
Write-Host "🌐 Access Dashboard:"
Write-Host "   Frontend: http://localhost:3000/dashboard"
Write-Host "   Backend API: http://127.0.0.1:8001/docs"
Write-Host ""
Write-Host "📝 Next Steps:"
Write-Host "   1. Make sure Frontend is running"
Write-Host "   2. Open Dashboard: http://localhost:3000/dashboard"
Write-Host "   3. Hard refresh if needed"
Write-Host ""
