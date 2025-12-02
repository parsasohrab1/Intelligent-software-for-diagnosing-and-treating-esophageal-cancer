#!/bin/bash
# Development startup script

echo "=========================================="
echo "INEsCape Development Environment"
echo "=========================================="

# Check Docker
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Check services
python scripts/check_services.py

# Initialize if needed
if [ ! -f ".db_initialized" ]; then
    echo "Initializing database..."
    python scripts/init_database.py
    touch .db_initialized
fi

# Create admin user if needed
echo "Checking admin user..."
python scripts/create_admin_user.py \
    --username admin \
    --email admin@example.com \
    --password admin123 || true

# Start server
echo "Starting development server..."
echo "API will be available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

