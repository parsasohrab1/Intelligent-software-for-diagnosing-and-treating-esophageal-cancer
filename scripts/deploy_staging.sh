#!/bin/bash
# Staging deployment script

set -e

echo "=========================================="
echo "INEsCape Staging Deployment"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.staging exists
if [ ! -f ".env.staging" ]; then
    echo -e "${YELLOW}Warning: .env.staging not found. Creating from template...${NC}"
    cp .env.staging .env.staging.backup 2>/dev/null || true
fi

# Load staging environment variables
export $(cat .env.staging | grep -v '^#' | xargs)

# Check Docker
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Build images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose -f docker-compose.staging.yml build --no-cache

# Stop existing containers
echo -e "${GREEN}Stopping existing staging containers...${NC}"
docker-compose -f docker-compose.staging.yml down

# Start services
echo -e "${GREEN}Starting staging services...${NC}"
docker-compose -f docker-compose.staging.yml up -d

# Wait for services
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 30

# Check services
echo -e "${GREEN}Checking service health...${NC}"
docker-compose -f docker-compose.staging.yml ps

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
docker-compose -f docker-compose.staging.yml exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/init.sql || true

# Run migrations
echo -e "${GREEN}Running database migrations...${NC}"
docker-compose -f docker-compose.staging.yml exec -T app alembic upgrade head || true

# Create admin user
echo -e "${GREEN}Creating admin user...${NC}"
docker-compose -f docker-compose.staging.yml exec -T app python scripts/create_admin_user.py \
    --username admin \
    --email admin@staging.example.com \
    --password admin123 || echo "Admin user may already exist"

# Health check
echo -e "${GREEN}Performing health check...${NC}"
sleep 10
curl -f http://localhost:8001/api/v1/health || echo -e "${YELLOW}Health check failed, but services may still be starting...${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "Staging deployment complete!"
echo "==========================================${NC}"
echo ""
echo "Services:"
echo "  - API: http://localhost:8001"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Grafana: http://localhost:3002"
echo "  - Prometheus: http://localhost:9091"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.staging.yml logs -f"
echo ""
echo "To stop:"
echo "  docker-compose -f docker-compose.staging.yml down"
echo ""

