#!/bin/bash
# Staging Environment Test Script for Linux/Mac

set -e

echo "=========================================="
echo "INEsCape Staging Environment Test"
echo "=========================================="
echo ""

# Check Docker
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"

# Check .env.staging
if [ ! -f ".env.staging" ]; then
    echo "❌ .env.staging not found. Please create it."
    exit 1
fi
echo "✅ .env.staging exists"

# Check services status
echo ""
echo "Checking services status..."
SERVICES=$(docker-compose -f docker-compose.staging.yml ps --services)
RUNNING=$(docker-compose -f docker-compose.staging.yml ps --services --filter "status=running")

if [ -z "$RUNNING" ]; then
    echo "⚠️  No services are running. Starting services..."
    docker-compose -f docker-compose.staging.yml up -d
    echo "Waiting for services to start..."
    sleep 30
else
    echo "✅ Services are running: $RUNNING"
fi

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
MAX_WAIT=60
WAITED=0
ALL_HEALTHY=false

while [ $WAITED -lt $MAX_WAIT ] && [ "$ALL_HEALTHY" = false ]; do
    sleep 5
    WAITED=$((WAITED + 5))
    
    UNHEALTHY=$(docker-compose -f docker-compose.staging.yml ps | grep -E "unhealthy|starting" || true)
    
    if [ -z "$UNHEALTHY" ]; then
        ALL_HEALTHY=true
        echo "✅ All services are healthy"
    else
        echo "  Waiting... ($WAITED/$MAX_WAIT seconds)"
    fi
done

# Test API Health Endpoint
echo ""
echo "Testing API health endpoint..."
if curl -f -s http://localhost:8001/api/v1/health > /dev/null; then
    echo "✅ API health check passed"
    curl -s http://localhost:8001/api/v1/health | jq .
else
    echo "❌ API health check failed"
    echo "   Make sure the app service is running and healthy"
fi

# Test API Docs
echo ""
echo "Testing API documentation..."
if curl -f -s http://localhost:8001/docs > /dev/null; then
    echo "✅ API documentation is accessible"
else
    echo "⚠️  API documentation check failed"
fi

# Test OpenAPI Schema
echo ""
echo "Testing OpenAPI schema..."
if curl -f -s http://localhost:8001/api/v1/openapi.json > /dev/null; then
    echo "✅ OpenAPI schema is accessible"
    curl -s http://localhost:8001/api/v1/openapi.json | jq '.info'
else
    echo "⚠️  OpenAPI schema check failed"
fi

# Check database connections
echo ""
echo "Testing database connections..."

# PostgreSQL
if docker-compose -f docker-compose.staging.yml exec -T postgres pg_isready -U inescape_staging_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL check failed"
fi

# MongoDB
if docker-compose -f docker-compose.staging.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "✅ MongoDB is ready"
else
    echo "⚠️  MongoDB check failed"
fi

# Redis
if docker-compose -f docker-compose.staging.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis check failed"
fi

# Service status summary
echo ""
echo "=========================================="
echo "Service Status Summary"
echo "=========================================="
docker-compose -f docker-compose.staging.yml ps

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  - API: http://localhost:8001"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Grafana: http://localhost:3002"
echo "  - Prometheus: http://localhost:9091"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.staging.yml logs -f"
echo ""

