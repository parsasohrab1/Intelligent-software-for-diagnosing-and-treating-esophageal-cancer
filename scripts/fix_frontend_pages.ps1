# Script to fix frontend pages (Patients & Dashboard)
Write-Host "=========================================="
Write-Host "Fix Frontend Pages (Patients & Dashboard)"
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
}
Write-Host ""

# Step 2: Check API Endpoints
Write-Host "Step 2: Testing API Endpoints..."
$endpoints = @(
    @{ Name = "Health"; Url = "/api/v1/health" },
    @{ Name = "Patients"; Url = "/api/v1/patients" },
    @{ Name = "Data Collection Stats"; Url = "/api/v1/data-collection/metadata/statistics" },
    @{ Name = "ML Models"; Url = "/api/v1/ml-models/models" }
)

$allWorking = $true
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001$($endpoint.Url)" -TimeoutSec 5 -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        $count = if ($data -is [array]) { $data.Count } else { if ($data.count) { $data.count } else { "OK" } }
        Write-Host "   ✅ $($endpoint.Name): OK (Count: $count)"
    } catch {
        Write-Host "   ❌ $($endpoint.Name): Error - $($_.Exception.Message)"
        $allWorking = $false
    }
}
Write-Host ""

# Step 3: Check Frontend Configuration
Write-Host "Step 3: Checking Frontend Configuration..."
if (Test-Path "frontend/.env") {
    Write-Host "✅ frontend/.env exists"
    $envContent = Get-Content "frontend/.env"
    $hasApiUrl = $envContent | Select-String -Pattern "VITE_API_BASE_URL"
    if ($hasApiUrl) {
        Write-Host "✅ API URL configured"
        $envContent | Select-String -Pattern "VITE_API_BASE_URL"
    } else {
        Write-Host "⚠️  API URL not found, adding..."
        Add-Content -Path "frontend/.env" -Value "`nVITE_API_BASE_URL=http://127.0.0.1:8001/api/v1"
        Write-Host "✅ API URL added"
    }
} else {
    Write-Host "⚠️  frontend/.env not found, creating..."
    Set-Content -Path "frontend/.env" -Value "VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1"
    Write-Host "✅ frontend/.env created"
}
Write-Host ""

# Step 4: Check Data
Write-Host "Step 4: Checking Database Data..."
try {
    $patients = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients" -TimeoutSec 5 -UseBasicParsing
    $data = $patients.Content | ConvertFrom-Json
    $count = if ($data -is [array]) { $data.Count } else { 0 }
    Write-Host "   Patients in database: $count"
    
    if ($count -eq 0) {
        Write-Host ""
        Write-Host "⚠️  No data found!"
        Write-Host "   To generate data:"
        Write-Host "   1. Go to: http://localhost:3000/data-generation"
        Write-Host "   2. Enter number of patients (e.g., 100)"
        Write-Host "   3. Check 'Save to Database'"
        Write-Host "   4. Click 'Generate Data'"
        Write-Host ""
        Write-Host "   Or use API:"
        Write-Host "   POST http://127.0.0.1:8001/api/v1/synthetic-data/generate"
    }
} catch {
    Write-Host "   ⚠️  Could not check data: $($_.Exception.Message)"
}
Write-Host ""

# Step 5: Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host ""

if ($allWorking) {
    Write-Host "✅ All API endpoints are working"
} else {
    Write-Host "⚠️  Some API endpoints have issues"
}

Write-Host ""
Write-Host "🌐 Next Steps:"
Write-Host "   1. Make sure Frontend is running: cd frontend; npm run dev"
Write-Host "   2. If .env was changed, restart Frontend"
Write-Host "   3. Generate data if database is empty"
Write-Host "   4. Hard refresh: Ctrl+F5"
Write-Host ""
Write-Host "📝 Access:"
Write-Host "   - Dashboard: http://localhost:3000/dashboard"
Write-Host "   - Patients: http://localhost:3000/patients"
Write-Host "   - Data Generation: http://localhost:3000/data-generation"
Write-Host ""

