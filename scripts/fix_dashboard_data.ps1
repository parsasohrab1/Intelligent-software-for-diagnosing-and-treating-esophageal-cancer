# Script to fix dashboard data issues
Write-Host "=========================================="
Write-Host "Fix Dashboard Data Issues"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check Backend
Write-Host "Step 1: Checking Backend..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "✅ Backend is running (Status: $($response.StatusCode))"
} catch {
    Write-Host "❌ Backend is not running"
    Write-Host "   Please start Backend:"
    Write-Host "   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
    exit 1
}
Write-Host ""

# Step 2: Check API Endpoints
Write-Host "Step 2: Checking API Endpoints..."
$endpoints = @(
    "/api/v1/patients",
    "/api/v1/data-collection/metadata/statistics",
    "/api/v1/ml-models/models"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001$endpoint" -TimeoutSec 3 -UseBasicParsing
        Write-Host "✅ $endpoint - OK (Status: $($response.StatusCode))"
    } catch {
        Write-Host "❌ $endpoint - Error: $($_.Exception.Message)"
    }
}
Write-Host ""

# Step 3: Check Frontend .env
Write-Host "Step 3: Checking Frontend Configuration..."
if (Test-Path "frontend/.env") {
    Write-Host "✅ frontend/.env exists"
    Get-Content "frontend/.env"
} else {
    Write-Host "⚠️  frontend/.env not found, creating..."
    Set-Content -Path "frontend/.env" -Value "VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1"
    Write-Host "✅ Created frontend/.env"
}
Write-Host ""

# Step 4: Check if data exists
Write-Host "Step 4: Checking Database Data..."
try {
    $patients = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients" -TimeoutSec 3 -UseBasicParsing
    $data = $patients.Content | ConvertFrom-Json
    Write-Host "   Patients in database: $($data.Count)"
    
    if ($data.Count -eq 0) {
        Write-Host ""
        Write-Host "⚠️  No data in database!"
        Write-Host "   To generate data, run:"
        Write-Host "   python scripts/generate_and_display_mri_data.py"
    }
} catch {
    Write-Host "   ⚠️  Could not check database data"
}
Write-Host ""

# Step 5: Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host ""
Write-Host "If dashboard still doesn't show data:"
Write-Host "1. Make sure Backend is running on port 8001"
Write-Host "2. Make sure Frontend .env is configured correctly"
Write-Host "3. Generate data if database is empty"
Write-Host "4. Check Browser DevTools (F12) for errors"
Write-Host "5. Hard refresh the page (Ctrl + F5)"
Write-Host ""

