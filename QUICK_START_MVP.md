# راهنمای سریع MVP - INEsCape

## ⚡ شروع سریع در 5 دقیقه

### 1. نصب Docker (اگر ندارید)

```bash
# Windows: Download Docker Desktop
# Mac: brew install docker
# Linux: sudo apt-get install docker docker-compose
```

### 2. Clone و Setup

```bash
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
```

### 3. راه‌اندازی Services

```bash
# Start all services
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Check services
python scripts/check_services.py
```

### 4. Initialize

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_database.py

# Create admin user
python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password admin123
```

### 5. Start Server

```bash
# Start backend
python scripts/run_server.py

# در ترمینال دیگر: Start frontend (اختیاری)
cd frontend && npm install && npm run dev
```

### 6. تست کنید!

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Generate data
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Content-Type: application/json" \
  -d '{"n_patients": 10, "cancer_ratio": 0.3}'
```

## 🎯 MVP Features Checklist

- [x] Docker setup
- [x] Database initialization
- [x] Admin user creation
- [x] API server running
- [x] Health check passing
- [x] Synthetic data generation
- [x] Basic ML models
- [x] CDS functionality
- [x] Frontend (optional)

## 📱 دسترسی

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000
- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090

## 🔑 Default Credentials

```
Username: admin
Password: admin123
Email: admin@example.com
```

**⚠️ مهم:** در production حتماً password را تغییر دهید!

## 🐛 مشکلات رایج

### Services شروع نمی‌شوند
```bash
docker-compose down
docker-compose up -d
```

### Database connection error
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart
docker-compose restart postgres
```

### Port already in use
```bash
# Change ports in docker-compose.yml
# یا stop service که port را استفاده می‌کند
```

## ✅ Verification

پس از راه‌اندازی، این موارد را بررسی کنید:

```bash
# 1. Health check
curl http://localhost:8000/api/v1/health
# باید {"status": "healthy"} برگرداند

# 2. Database
python scripts/check_services.py
# باید همه services healthy باشند

# 3. API Documentation
# باز کردن http://localhost:8000/docs در browser
```

## 🎉 موفق باشید!

MVP شما آماده استفاده است! برای اطلاعات بیشتر:
- [MVP Guide](MVP_GUIDE.md)
- [Full Documentation](README.md)
- [API Docs](http://localhost:8000/docs)

