#!/bin/bash
# Run Live: Backend, Frontend & Dashboard
# اجرای Live: Backend، Frontend و Dashboard

set -e

echo "========================================"
echo "  INEsCape Live Server Startup"
echo "  Backend + Frontend + Dashboard"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "${YELLOW}Checking Docker services...${NC}"
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is running${NC}"
else
    echo -e "${YELLOW}⚠️  Docker is not running. Starting Docker services...${NC}"
    docker-compose up -d postgres mongodb redis
    sleep 10
fi

# Wait for databases
echo ""
echo -e "${YELLOW}Waiting for databases to be ready...${NC}"
sleep 5

# Step 1: Setup Database
echo ""
echo -e "${CYAN}Step 1: Setting up database...${NC}"
if [ -f "scripts/create_migration.py" ]; then
    echo -e "${YELLOW}Creating database tables...${NC}"
    python scripts/create_migration.py || echo -e "${YELLOW}⚠️  Database setup may have issues, continuing...${NC}"
fi

# Step 2: Seed initial data
echo ""
echo -e "${CYAN}Step 2: Seeding initial data...${NC}"
if [ -f "scripts/seed_initial_data.py" ]; then
    echo -e "${YELLOW}Seeding initial data...${NC}"
    python scripts/seed_initial_data.py || echo -e "${YELLOW}⚠️  Data seeding may have issues, continuing...${NC}"
fi

# Step 3: Start Backend
echo ""
echo -e "${CYAN}Step 3: Starting Backend Server...${NC}"
echo -e "${GREEN}Backend will run on: http://localhost:8000${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"
echo ""

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use!${NC}"
    echo -e "${YELLOW}Stopping existing backend processes...${NC}"
    pkill -f "uvicorn app.main:app" || true
    sleep 2
fi

# Start backend in background
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend server starting (PID: $BACKEND_PID)...${NC}"
sleep 5

# Step 4: Start Frontend
echo ""
echo -e "${CYAN}Step 4: Starting Frontend (Dashboard)...${NC}"
echo -e "${GREEN}Frontend will run on: http://localhost:5173${NC}"
echo ""

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${YELLOW}❌ Frontend directory not found!${NC}"
    echo -e "${YELLOW}Please make sure you're in the project root directory${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check if port 5173 is in use
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 5173 is already in use!${NC}"
fi

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend server starting (PID: $FRONTEND_PID)...${NC}"
sleep 5

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ All Services Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📍 Access Points:${NC}"
echo -e "  Backend API:    http://localhost:8000"
echo -e "  API Docs:       http://localhost:8000/docs"
echo -e "  Frontend:       http://localhost:5173"
echo -e "  Dashboard:      http://localhost:5173 (Dashboard page)"
echo ""
echo -e "${CYAN}🔐 Default Login:${NC}"
echo -e "  Username: admin"
echo -e "  Password: admin123"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop all services${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn app.main:app" || true
    pkill -f "vite" || true
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait
wait

