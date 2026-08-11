# Troubleshooting: Failed to Load MRI Data

## مشکل: "Failed to load MRI data"

این خطا معمولاً به این دلایل رخ می‌دهد:
1. هیچ MRI data در database نیست
2. Backend در حال اجرا نیست
3. API endpoint در دسترس نیست
4. مشکل در اتصال Frontend به Backend

## راه‌حل‌های سریع

### 1. بررسی وجود داده

```powershell
# بررسی MRI data در database
python scripts/check_mri_data.py
```

### 2. تولید داده‌های MRI

#### Option A: استفاده از Script (مستقیم در Database)

```powershell
python scripts/generate_and_display_mri_data.py
```

این script:
- داده‌های synthetic تولید می‌کند
- شامل MRI images می‌شود
- مستقیماً در database ذخیره می‌کند

#### Option B: استفاده از API

```powershell
# با curl
curl -X POST http://127.0.0.1:8001/api/v1/synthetic-data/generate `
  -H "Content-Type: application/json" `
  -d '{"n_patients": 50, "cancer_ratio": 0.4, "save_to_db": true}'

# یا با PowerShell
$body = @{
    n_patients = 50
    cancer_ratio = 0.4
    save_to_db = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/synthetic-data/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

#### Option C: استفاده از Script API-based

```powershell
python scripts/generate_mri_data.py
```

### 3. بررسی Backend

```powershell
# تست Health endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# تست MRI endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri"

# تست Reports endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri/reports"
```

### 4. بررسی Frontend

در Browser DevTools (F12):
1. **Console tab:** خطاها را بررسی کنید
2. **Network tab:** 
   - Request به `/api/v1/imaging/mri/reports` را بررسی کنید
   - Status code را بررسی کنید
   - Response را بررسی کنید

## مشکلات رایج

### مشکل 1: "No MRI data found"

**علت:** هیچ MRI data در database نیست

**راه‌حل:**
```powershell
# تولید داده
python scripts/generate_and_display_mri_data.py
```

### مشکل 2: "Network Error" یا "Failed to fetch"

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

### مشکل 3: "404 Not Found"

**علت:** API endpoint اشتباه است یا route ثبت نشده

**راه‌حل:**
```powershell
# بررسی routes
Invoke-WebRequest -Uri "http://127.0.0.1:8001/docs"
# در Swagger UI، endpoint /api/v1/imaging/mri/reports را بررسی کنید
```

### مشکل 4: "CORS Error"

**علت:** CORS configuration مشکل دارد

**راه‌حل:**
- بررسی `app/main.py` برای CORS settings
- بررسی `settings.CORS_ORIGINS` در `app/core/config.py`

### مشکل 5: "Database connection error"

**علت:** Docker services در حال اجرا نیستند

**راه‌حل:**
```powershell
# راه‌اندازی Docker services
docker-compose up -d

# بررسی services
docker ps
```

## بررسی کامل

### Step 1: بررسی Database

```powershell
python scripts/check_mri_data.py
```

### Step 2: بررسی Backend API

```powershell
# Health check
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# MRI endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri"

# Reports endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri/reports"
```

### Step 3: بررسی Frontend

1. Browser DevTools را باز کنید (F12)
2. Console tab را بررسی کنید
3. Network tab را بررسی کنید
4. Request به `/api/v1/imaging/mri/reports` را بررسی کنید

### Step 4: تولید داده (اگر لازم باشد)

```powershell
python scripts/generate_and_display_mri_data.py
```

## API Endpoints

### GET `/api/v1/imaging/mri`
لیست تمام MRI images

### GET `/api/v1/imaging/mri/reports`
لیست تمام MRI reports با patient details

### GET `/api/v1/imaging/mri/{image_id}`
MRI image خاص

### GET `/api/v1/imaging/mri/{image_id}/report`
MRI report خاص با patient details

## Frontend Code

Frontend از این endpoint استفاده می‌کند:
```typescript
// frontend/src/pages/MRIDashboard.tsx
const response = await api.get('/imaging/mri/reports', { params })
```

که به این URL تبدیل می‌شود:
```
http://127.0.0.1:8001/api/v1/imaging/mri/reports
```

## Checklist

- [ ] Docker services در حال اجرا هستند
- [ ] Backend در حال اجرا است (پورت 8001)
- [ ] Frontend در حال اجرا است (پورت 3000)
- [ ] MRI data در database وجود دارد
- [ ] API endpoint کار می‌کند
- [ ] Frontend می‌تواند به Backend متصل شود
- [ ] CORS settings صحیح است

## اگر هنوز کار نمی‌کند

1. تمام logs را بررسی کنید (Backend و Frontend)
2. Browser DevTools را بررسی کنید
3. Database را مستقیماً بررسی کنید
4. API را مستقیماً تست کنید (Postman یا curl)
5. Frontend code را بررسی کنید

