# راهنمای رفع مشکل: داده در تب‌ها نیست

## مشکل

تمام تب‌ها در sidebar داده ندارند:
- Dashboard has no data
- Patients has no data
- Data generation has no data
- ML model has no data
- MRI report has no data

## علل

1. **Backend در حال اجرا نیست**
2. **Docker services (PostgreSQL) در حال اجرا نیستند**
3. **Database خالی است (هیچ داده‌ای تولید نشده)**
4. **Frontend نمی‌تواند به Backend متصل شود**

## راه‌حل گام به گام

### Step 1: راه‌اندازی Docker Services

```powershell
# بررسی Docker
docker ps

# راه‌اندازی Docker services
docker-compose up -d

# بررسی وضعیت
docker ps
```

**نکته:** باید PostgreSQL container در حال اجرا باشد.

### Step 2: راه‌اندازی Backend

```powershell
# در یک Terminal جدید
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**یا از script:**
```powershell
.\scripts\start_backend.ps1
```

**بررسی:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"
```

### Step 3: تولید داده

#### Option A: استفاده از API (پیشنهادی)

```powershell
$body = @{
    n_patients = 100
    cancer_ratio = 0.4
    save_to_db = $true
    seed = 42
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/synthetic-data/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -TimeoutSec 300
```

#### Option B: استفاده از Script

```powershell
.\scripts\generate_all_data.ps1
```

#### Option C: استفاده از Frontend

1. به صفحه **Data Generation** بروید: http://localhost:3000/data-generation
2. تعداد patients را وارد کنید (مثلاً 100)
3. Cancer ratio را تنظیم کنید (مثلاً 0.4)
4. **مهم:** تیک **Save to Database** را بزنید
5. روی **Generate Data** کلیک کنید

### Step 4: بررسی داده‌های تولید شده

```powershell
# بررسی Patients
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/patients"

# بررسی MRI Images
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri"

# بررسی MRI Reports
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/imaging/mri/reports"
```

### Step 5: Refresh Frontend

1. **Hard Refresh:** `Ctrl + F5`
2. یا Browser را ببندید و دوباره باز کنید
3. یا Frontend را restart کنید

## استفاده از Script یکپارچه

```powershell
.\scripts\start_all.ps1
```

این script:
- Docker services را راه‌اندازی می‌کند
- Backend را راه‌اندازی می‌کند
- Frontend را راه‌اندازی می‌کند

**اما داده را تولید نمی‌کند!** باید بعد از راه‌اندازی، داده را تولید کنید.

## Checklist

قبل از بررسی Frontend، مطمئن شوید:

- [ ] Docker services در حال اجرا هستند (`docker ps`)
- [ ] Backend در حال اجرا است (پورت 8001)
- [ ] Frontend در حال اجرا است (پورت 3000)
- [ ] داده در database وجود دارد
- [ ] API endpoints کار می‌کنند
- [ ] Frontend `.env` صحیح است (`VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1`)

## Troubleshooting

### مشکل 1: Backend شروع نمی‌شود

**علل:**
- Docker services در حال اجرا نیستند
- پورت 8001 در حال استفاده است
- Dependencies نصب نشده‌اند

**راه‌حل:**
```powershell
# 1. بررسی Docker
docker ps

# 2. راه‌اندازی Docker
docker-compose up -d

# 3. بررسی پورت
netstat -ano | findstr :8001

# 4. راه‌اندازی Backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### مشکل 2: داده تولید نمی‌شود

**علل:**
- Backend در حال اجرا نیست
- Database connection error
- API endpoint مشکل دارد

**راه‌حل:**
```powershell
# 1. بررسی Backend
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# 2. بررسی Database
docker ps | Select-String postgres

# 3. تولید داده با API
$body = @{ n_patients = 100; cancer_ratio = 0.4; save_to_db = $true } | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/synthetic-data/generate" -Method POST -ContentType "application/json" -Body $body
```

### مشکل 3: Frontend داده نمی‌بیند

**علل:**
- API URL اشتباه است
- CORS issue
- Browser cache

**راه‌حل:**
1. بررسی `frontend/.env`:
   ```
   VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
   ```

2. Frontend را restart کنید

3. Browser cache را پاک کنید:
   - `Ctrl + Shift + Delete`
   - یا Hard Refresh: `Ctrl + F5`

4. Browser DevTools (F12) را بررسی کنید:
   - Console tab: خطاها
   - Network tab: API requests

## دستورات سریع

### راه‌اندازی کامل (3 Terminal)

**Terminal 1 - Docker:**
```powershell
docker-compose up -d
```

**Terminal 2 - Backend:**
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**Terminal 3 - Frontend:**
```powershell
cd frontend
npm run dev
```

**Terminal 4 - تولید داده:**
```powershell
$body = @{ n_patients = 100; cancer_ratio = 0.4; save_to_db = $true } | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/synthetic-data/generate" -Method POST -ContentType "application/json" -Body $body
```

## بعد از تولید داده

1. **Dashboard:** http://localhost:3000/dashboard
   - باید تعداد patients نمایش داده شود

2. **Patients:** http://localhost:3000/patients
   - باید لیست patients نمایش داده شود

3. **Data Generation:** http://localhost:3000/data-generation
   - می‌توانید داده بیشتر تولید کنید

4. **ML Models:** http://localhost:3000/ml-models
   - اگر model train کرده‌اید، نمایش داده می‌شود

5. **MRI Report:** http://localhost:3000/mri
   - باید MRI images و reports نمایش داده شوند

## نکات مهم

1. **همیشه ابتدا Docker را راه‌اندازی کنید**
2. **سپس Backend را راه‌اندازی کنید**
3. **بعد داده تولید کنید**
4. **در آخر Frontend را refresh کنید**

5. **مهم:** در Data Generation page، حتماً **Save to Database** را فعال کنید!

## اگر هنوز کار نمی‌کند

1. تمام logs را بررسی کنید
2. Browser DevTools را بررسی کنید
3. API endpoints را مستقیماً تست کنید
4. Database را مستقیماً بررسی کنید

