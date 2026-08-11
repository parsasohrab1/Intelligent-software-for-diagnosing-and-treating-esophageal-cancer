# INEsCape MVP - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Prerequisites Check

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python --version  # Should be 3.11+

# Check Node.js (for frontend)
node --version  # Should be 18+
```

### Step 2: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# Create .env file
cp .env.example .env

# Edit .env - Set at minimum:
# SECRET_KEY=your-secret-key-here
# POSTGRES_PASSWORD=your-password
# MONGODB_PASSWORD=your-password
```

### Step 3: Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Wait 30-60 seconds for services to start
# Check status
docker-compose ps
```

### Step 4: Initialize

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_database.py

# Create admin user
python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password Admin123!
```

### Step 5: Start Application

```bash
# Terminal 1: Start backend
python scripts/run_server.py

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev
```

### Step 6: Access

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Login:** admin / Admin123!

## ✅ Verification

```bash
# Check all services
python scripts/check_services.py

# Test API
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"1.0.0"}
```

## 🎯 First Steps

### 1. Generate Test Data

In browser: http://localhost:3000/data-generation
- Set patients: 100
- Click "Generate Data"

### 2. View Dashboard

Navigate to: http://localhost:3000/dashboard
- See statistics
- View charts

### 3. Test CDS

Navigate to: http://localhost:3000/cds
- Enter patient info
- Click "Predict Risk"
- View recommendations

## 🐛 Common Issues

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill process or change port in .env
```

### Docker Not Running

```bash
# Start Docker Desktop
# Then retry:
docker-compose up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

## 📝 Quick Commands

```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f app

# Restart service
docker-compose restart app

# Check health
curl http://localhost:8000/api/v1/health
```

## 🎓 Next Steps

1. Read `MVP_README.md` for full documentation
2. Explore API at http://localhost:8000/docs
3. Review `docs/USER_MANUAL.md`
4. Run tests: `pytest`

---

**Ready to use!** 🎉

