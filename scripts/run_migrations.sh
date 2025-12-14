#!/bin/bash
# Script to run database migrations

set -e

echo "=========================================="
echo "Database Migration Script"
echo "=========================================="

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Error: Alembic is not installed"
    echo "Install with: pip install alembic"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your settings."
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Create initial migration if needed
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "📝 Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration: Create all tables"
fi

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head

echo "✅ Migrations completed successfully!"
echo "=========================================="

