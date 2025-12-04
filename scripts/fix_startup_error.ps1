# Script to fix application startup errors
Write-Host "=========================================="
Write-Host "Fix Application Startup Error"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check Docker
Write-Host "Step 1: Checking Docker Services..."
try {
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $postgresRunning = $dockerStatus | Select-String -Pattern "postgres"
        if ($postgresRunning) {
            Write-Host "✅ PostgreSQL is running"
        } else {
            Write-Host "❌ PostgreSQL is not running"
            Write-Host ""
            Write-Host "Starting Docker services..."
            docker-compose up -d
            Write-Host "⏳ Waiting for services to start (10 seconds)..."
            Start-Sleep -Seconds 10
        }
    } else {
        Write-Host "⚠️  Docker may not be running"
        Write-Host "   Please start Docker Desktop"
    }
} catch {
    Write-Host "⚠️  Could not check Docker"
}
Write-Host ""

# Step 2: Check .env file
Write-Host "Step 2: Checking .env file..."
if (Test-Path ".env") {
    Write-Host "✅ .env file exists"
    $envContent = Get-Content ".env"
    $hasDb = $envContent | Select-String -Pattern "DATABASE_URL|POSTGRES"
    if ($hasDb) {
        Write-Host "✅ Database configuration found"
    } else {
        Write-Host "⚠️  Database configuration not found in .env"
    }
} else {
    Write-Host "⚠️  .env file not found"
    Write-Host "   Creating from .env.example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env file created"
    } else {
        Write-Host "❌ .env.example not found"
    }
}
Write-Host ""

# Step 3: Test database connection
Write-Host "Step 3: Testing database connection..."
try {
    python -c "from app.core.database import engine; conn = engine.connect(); print('✅ Database connection successful'); conn.close()" 2>&1
} catch {
    Write-Host "❌ Database connection failed"
    Write-Host "   Error: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Possible solutions:"
    Write-Host "   1. Make sure Docker services are running: docker-compose up -d"
    Write-Host "   2. Check DATABASE_URL in .env file"
    Write-Host "   3. Wait a few seconds for PostgreSQL to fully start"
}
Write-Host ""

# Step 4: Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host ""
Write-Host "If startup still fails:"
Write-Host "1. Make sure Docker Desktop is running"
Write-Host "2. Run: docker-compose up -d"
Write-Host "3. Wait 10-15 seconds for PostgreSQL to start"
Write-Host "4. Check logs: docker-compose logs postgres"
Write-Host "5. Try starting Backend again"
Write-Host ""

