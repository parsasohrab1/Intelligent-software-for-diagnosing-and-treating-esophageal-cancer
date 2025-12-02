# راهنمای تولید داده MRI و نمایش در Dashboard

## 📋 مراحل راه‌اندازی

### مرحله 1: راه‌اندازی Docker Desktop

1. **Docker Desktop را باز کنید**
2. **منتظر بمانید** تا Docker engine شروع شود (آیکون سبز شود)

### مرحله 2: راه‌اندازی Services

```powershell
# Start all Docker services (PostgreSQL, MongoDB, Redis)
docker-compose up -d

# Wait for services to be ready (30 seconds)
timeout /t 30

# Check services status
docker-compose ps
```

### مرحله 3: Initialize Database

```powershell
# Initialize database tables
python scripts/init_database.py

# Create admin user (optional)
python scripts/create_admin_user.py --username admin --email admin@example.com --password admin123
```

### مرحله 4: تولید داده Synthetic با MRI

**روش 1: استفاده از Script (پیشنهادی)**

```powershell
python scripts/generate_and_display_mri_data.py
```

**روش 2: استفاده از API (بعد از راه‌اندازی سرور)**

```powershell
# First, start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Then in another terminal, use the API script
python scripts/generate_mri_data.py
```

**روش 3: استفاده مستقیم از API**

```powershell
# Using curl or Postman
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "n_patients": 50,
    "cancer_ratio": 0.4,
    "seed": 42,
    "save_to_db": true
  }'
```

### مرحله 5: راه‌اندازی FastAPI Server

```powershell
# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the script
.\scripts\start_server.ps1
```

### مرحله 6: راه‌اندازی Frontend (اختیاری)

```powershell
cd frontend
npm install
npm run dev
```

## ✅ بررسی داده‌ها

### بررسی از طریق API

```powershell
# Check MRI images
curl http://localhost:8000/api/v1/imaging/mri

# Check MRI reports
curl http://localhost:8000/api/v1/imaging/mri/reports
```

### بررسی از طریق Browser

- **API Docs:** http://localhost:8000/docs
- **MRI API:** http://localhost:8000/api/v1/imaging/mri
- **Frontend Dashboard:** http://localhost:3000/mri (اگر frontend اجرا است)

## 🎯 دستورات سریع (یکجا)

```powershell
# 1. Start Docker services
docker-compose up -d

# 2. Wait 30 seconds
timeout /t 30

# 3. Initialize database
python scripts/init_database.py

# 4. Generate data
python scripts/generate_and_display_mri_data.py

# 5. Start server (in new terminal)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 داده‌های تولید شده

بعد از تولید داده، شما خواهید داشت:

- **50 بیمار** با اطلاعات کامل
- **40% با سرطان** (20 بیمار)
- **60% بدون سرطان** (30 بیمار)
- **تصاویر MRI** برای هر بیمار
- **گزارش‌های MRI** با findings و impression
- **اندازه‌گیری‌ها:** Tumor Length, Wall Thickness, Lymph Nodes

## 🔍 Troubleshooting

### خطا: Connection refused to PostgreSQL

**راه‌حل:**
```powershell
# Check if Docker is running
docker ps

# If not, start Docker Desktop and then:
docker-compose up -d
```

### خطا: Port 8000 already in use

**راه‌حل:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### خطا: No MRI data in dashboard

**راه‌حل:**
1. بررسی کنید که `save_to_db: true` در request باشد
2. بررسی کنید که database initialized شده باشد
3. دوباره داده تولید کنید

## 📝 نکات مهم

1. **Docker Desktop باید در حال اجرا باشد** قبل از هر کاری
2. **Services باید fully started باشند** قبل از تولید داده
3. **Database باید initialized باشد** قبل از save کردن داده
4. **Server باید در حال اجرا باشد** برای دسترسی به API و Dashboard

