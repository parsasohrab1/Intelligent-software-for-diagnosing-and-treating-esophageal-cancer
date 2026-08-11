# راهنمای رفع مشکل: داده‌ها در Dashboard نمایش داده نمی‌شوند

## مشکل

داده‌ها در Dashboard نمایش داده نمی‌شوند یا خالی هستند.

## علل احتمالی

1. **Backend در حال اجرا نیست**
2. **API endpoints در دسترس نیستند**
3. **Frontend نمی‌تواند به Backend متصل شود**
4. **Database خالی است (هیچ داده‌ای وجود ندارد)**
5. **API Base URL اشتباه است**
6. **CORS issue**

## راه‌حل‌های گام به گام

### Step 1: بررسی Backend

```powershell
# تست Health endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# اگر خطا می‌دهد، Backend را راه‌اندازی کنید:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Step 2: بررسی API Endpoints

```powershell
# Patients
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients"

# Data Collection
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/data-collection/metadata/statistics"

# ML Models
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/ml-models/models"
```

### Step 3: بررسی Frontend Configuration

```powershell
# بررسی فایل .env
Get-Content frontend/.env

# اگر وجود ندارد، ایجاد کنید:
Set-Content -Path "frontend/.env" -Value "VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1"
```

**مهم:** بعد از تغییر `.env`، Frontend را restart کنید!

### Step 4: بررسی Database

```powershell
# بررسی وجود داده
python scripts/check_mri_data.py

# اگر خالی است، تولید کنید:
python scripts/generate_and_display_mri_data.py
```

### Step 5: بررسی Browser

1. **DevTools را باز کنید (F12)**
2. **Console tab:**
   - خطاهای JavaScript را بررسی کنید
   - خطاهای API را بررسی کنید
3. **Network tab:**
   - Request به `/api/v1/patients` را بررسی کنید
   - Status code را بررسی کنید
   - Response را بررسی کنید
4. **Hard Refresh:**
   - `Ctrl + F5` یا `Ctrl + Shift + R`

## استفاده از Script

```powershell
.\scripts\fix_dashboard_data.ps1
```

این script به صورت خودکار:
- Backend را بررسی می‌کند
- API endpoints را تست می‌کند
- Frontend .env را بررسی/ایجاد می‌کند
- Database data را بررسی می‌کند

## مشکلات رایج

### مشکل 1: "Network Error" یا "Failed to fetch"

**علت:** Backend در حال اجرا نیست یا Frontend نمی‌تواند به آن متصل شود

**راه‌حل:**
```powershell
# 1. بررسی Backend
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# 2. راه‌اندازی Backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# 3. بررسی API URL در frontend/.env
# باید باشد: VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

### مشکل 2: "404 Not Found"

**علت:** API endpoint اشتباه است یا route ثبت نشده

**راه‌حل:**
```powershell
# بررسی routes در Swagger UI
Start-Process "http://127.0.0.1:8001/docs"
```

### مشکل 3: "CORS Error"

**علت:** CORS configuration مشکل دارد

**راه‌حل:**
- بررسی `app/main.py` برای CORS settings
- بررسی `settings.CORS_ORIGINS` در `app/core/config.py`
- باید شامل `http://localhost:3000` باشد

### مشکل 4: Dashboard خالی است اما API کار می‌کند

**علت:** 
- Frontend component مشکل دارد
- Data format اشتباه است
- Error handling مشکل دارد

**راه‌حل:**
1. Browser DevTools را بررسی کنید
2. Console errors را بررسی کنید
3. Network tab را بررسی کنید
4. Response data را بررسی کنید

### مشکل 5: "0" برای همه statistics

**علت:** Database خالی است

**راه‌حل:**
```powershell
# تولید داده
python scripts/generate_and_display_mri_data.py
```

## بهبودهای انجام شده

### Dashboard Component

1. **Error Handling بهتر:**
   - `.catch()` برای هر API call
   - Default values در صورت خطا

2. **Cancer Patients Calculation:**
   - از `has_cancer` field استفاده می‌کند
   - به صورت خودکار محاسبه می‌شود

3. **Data Validation:**
   - بررسی می‌کند که data array است
   - Fallback values در صورت undefined

## Checklist

- [ ] Backend در حال اجرا است (پورت 8001)
- [ ] Frontend در حال اجرا است (پورت 3000)
- [ ] `frontend/.env` موجود است و صحیح است
- [ ] API endpoints کار می‌کنند
- [ ] Database دارای داده است
- [ ] Browser DevTools خطایی نشان نمی‌دهد
- [ ] Network requests موفق هستند
- [ ] CORS settings صحیح است

## تست نهایی

```powershell
# 1. Backend Health
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# 2. Patients Data
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients"

# 3. Frontend
Start-Process "http://localhost:3000"
```

## اگر هنوز کار نمی‌کند

1. تمام logs را بررسی کنید (Backend و Frontend)
2. Browser DevTools را بررسی کنید
3. Database را مستقیماً بررسی کنید
4. API را مستقیماً تست کنید (Postman یا curl)
5. Frontend code را بررسی کنید

## نکات مهم

1. **همیشه از `http://` استفاده کنید** (نه `https://`)
2. **Backend روی `127.0.0.1` است** (نه `localhost`)
3. **Frontend روی `localhost` است**
4. **بعد از تغییر `.env`، Frontend را restart کنید**
5. **Hard Refresh بعد از تغییرات**

