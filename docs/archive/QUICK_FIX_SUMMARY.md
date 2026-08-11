# راهنمای رفع مشکل Dashboard

## مشکل
داده‌های Dashboard و Patients در Frontend نمایش داده نمی‌شدند.

## علت
1. Apache روی پورت 8000 در حال اجرا بود
2. Redis/MongoDB در دسترس نبود و باعث خطای 500 می‌شد

## راه‌حل‌های اعمال شده

### 1. تغییر پورت Backend
- Backend از پورت 8000 به **8001** تغییر کرد
- فایل‌های به‌روزرسانی شده:
  - `frontend/vite.config.ts` - proxy به پورت 8001
  - `frontend/src/services/api.ts` - baseURL به پورت 8001

### 2. رفع مشکل Cache
- `app/core/cache.py` - حالا بدون Redis کار می‌کند
- `app/core/redis_client.py` - در صورت عدم دسترسی به Redis، None برمی‌گرداند

## مراحل بعدی

### 1. Restart Frontend
```powershell
cd frontend
# اگر در حال اجرا است، Ctrl+C بزنید
npm run dev
```

### 2. بررسی Backend
Backend باید روی پورت 8001 در حال اجرا باشد:
```powershell
python scripts/run_server.py
# یا
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 3. دسترسی به Dashboard
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## وضعیت Database
- ✅ 50 بیمار در دیتابیس موجود است
- ✅ PostgreSQL در حال اجرا است (Docker)

## نکات
- اگر Redis/MongoDB در دسترس نباشد، cache غیرفعال می‌شود اما API کار می‌کند
- Frontend باید restart شود تا تغییرات پورت اعمال شود

