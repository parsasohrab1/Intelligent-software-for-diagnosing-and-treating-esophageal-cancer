# راهنمای راه‌اندازی Backend

## مشکل
Dashboard داده‌ها را نمایش نمی‌دهد چون Backend در حال اجرا نیست.

## راه‌حل

### 1. راه‌اندازی Backend

در یک ترمینال PowerShell، دستور زیر را اجرا کنید:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

یا:

```powershell
python scripts/run_server.py
```

**نکته:** اگر از `scripts/run_server.py` استفاده می‌کنید، باید پورت را در `app/core/config.py` به 8001 تغییر دهید یا مستقیماً با uvicorn اجرا کنید.

### 2. بررسی وضعیت Backend

پس از راه‌اندازی، باید پیام زیر را ببینید:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. تست Backend

در ترمینال دیگر، دستور زیر را اجرا کنید:

```powershell
python -c "import requests; r = requests.get('http://localhost:8001/api/v1/patients/'); print('Status:', r.status_code); print('Count:', len(r.json()) if r.status_code == 200 else 0)"
```

باید `Status: 200` و `Count: 50` را ببینید.

### 4. Restart Frontend

اگر Frontend در حال اجرا است، آن را متوقف کنید (Ctrl+C) و دوباره اجرا کنید:

```powershell
cd frontend
npm run dev
```

### 5. بررسی Dashboard

به http://localhost:3000 بروید و Dashboard را بررسی کنید.

## مشکلات احتمالی

### Backend راه‌اندازی نمی‌شود
- بررسی کنید که PostgreSQL در حال اجرا است: `docker-compose ps`
- بررسی کنید که پورت 8001 آزاد است
- لاگ‌های خطا را بررسی کنید

### خطای 500 از API
- بررسی کنید که Redis/MongoDB در دسترس نیستند (این OK است، cache غیرفعال می‌شود)
- بررسی کنید که PostgreSQL در حال اجرا است

### Frontend داده نمی‌گیرد
- Console مرورگر را باز کنید (F12) و خطاها را بررسی کنید
- بررسی کنید که Backend روی پورت 8001 در حال اجرا است
- بررسی کنید که `frontend/vite.config.ts` و `frontend/src/services/api.ts` به پورت 8001 اشاره می‌کنند

