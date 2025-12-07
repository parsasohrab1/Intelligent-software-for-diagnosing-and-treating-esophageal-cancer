# راهنمای اجرای Live: Backend + Frontend + Dashboard

این راهنما برای اجرای سریع سیستم به صورت live است.

## روش 1: اجرای ساده (Windows PowerShell)

```powershell
# اجرای ساده - هر سرویس در پنجره جداگانه
.\scripts\run_live_simple.ps1
```

این اسکریپت:
- Backend را در یک پنجره PowerShell باز می‌کند
- Frontend را در یک پنجره PowerShell دیگر باز می‌کند
- می‌توانید هر پنجره را جداگانه ببندید

## روش 2: اجرای کامل (Windows PowerShell)

```powershell
# اجرای کامل با مدیریت خودکار
.\scripts\run_live.ps1
```

این اسکریپت:
- بررسی و راه‌اندازی Docker services
- ایجاد جداول دیتابیس
- وارد کردن داده‌های اولیه
- اجرای Backend و Frontend
- مدیریت خودکار cleanup

## روش 3: اجرای دستی

### 1. راه‌اندازی دیتابیس (Docker)

```powershell
# Start Docker services
docker-compose up -d postgres mongodb redis

# Wait for services
Start-Sleep -Seconds 10
```

### 2. ایجاد جداول

```powershell
python scripts\create_migration.py
```

### 3. وارد کردن داده‌های اولیه

```powershell
python scripts\seed_initial_data.py
```

### 4. اجرای Backend

```powershell
# Terminal 1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 5. اجرای Frontend

```powershell
# Terminal 2
cd frontend
npm install  # اگر node_modules وجود ندارد
npm run dev
```

## دسترسی

پس از اجرا:

- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Frontend/Dashboard**: http://localhost:3000

### ورود به سیستم

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **مهم**: پس از اولین ورود، رمز عبور را تغییر دهید!

## Linux/Mac

برای Linux یا Mac، از اسکریپت bash استفاده کنید:

```bash
chmod +x scripts/run_live.sh
./scripts/run_live.sh
```

## توقف سرویس‌ها

### Windows PowerShell

```powershell
# توقف Backend
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process

# توقف Frontend
Get-Process node | Where-Object { $_.Path -like "*frontend*" } | Stop-Process

# توقف Docker services
docker-compose down
```

### Linux/Mac

```bash
# توقف همه
pkill -f "uvicorn app.main:app"
pkill -f "vite"
```

## عیب‌یابی

### مشکل: Port در حال استفاده است

```powershell
# Windows: بررسی port
netstat -ano | findstr :8001
netstat -ano | findstr :3000

# Linux/Mac: بررسی port
lsof -i :8001
lsof -i :3000
```

### مشکل: Backend اجرا نمی‌شود

1. بررسی کنید که Python نصب است: `python --version`
2. بررسی کنید که dependencies نصب شده: `pip install -r requirements.txt`
3. بررسی لاگ‌ها برای خطاها

### مشکل: Frontend اجرا نمی‌شود

1. بررسی کنید که Node.js نصب است: `node --version`
2. نصب dependencies: `cd frontend && npm install`
3. بررسی لاگ‌ها

### مشکل: دیتابیس متصل نمی‌شود

1. بررسی کنید که Docker در حال اجرا است: `docker ps`
2. بررسی کنید که containers در حال اجرا هستند: `docker-compose ps`
3. بررسی لاگ‌های PostgreSQL: `docker-compose logs postgres`

## نکات مهم

- Backend روی پورت **8001** اجرا می‌شود (طبق config.py)
- Frontend روی پورت **3000** اجرا می‌شود (طبق vite.config.ts)
- برای تغییر پورت‌ها، فایل‌های config را ویرایش کنید
- در حالت development، هر دو سرویس auto-reload دارند

---

**نسخه:** 1.0  
**آخرین به‌روزرسانی:** 2024-12-19

