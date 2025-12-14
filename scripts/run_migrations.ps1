# PowerShell script to run database migrations

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "Database Migration Script"
Write-Host "=========================================="

# Check if alembic is installed
try {
    alembic --version | Out-Null
} catch {
    Write-Host "❌ Error: Alembic is not installed" -ForegroundColor Red
    Write-Host "Install with: pip install alembic"
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating from .env.example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file. Please edit it with your settings." -ForegroundColor Green
    } else {
        Write-Host "❌ Error: .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Create initial migration if needed
if (-not (Test-Path "alembic/versions") -or (Get-ChildItem "alembic/versions" -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "📝 Creating initial migration..." -ForegroundColor Cyan
    alembic revision --autogenerate -m "Initial migration: Create all tables"
}

# Run migrations
Write-Host "🔄 Running migrations..." -ForegroundColor Cyan
alembic upgrade head

Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
Write-Host "=========================================="

