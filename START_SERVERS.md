# راهنمای راه‌اندازی سرورها

## مشکل: ERR_CONNECTION_REFUSED یا ERR_FAILED

این خطا زمانی رخ می‌دهد که Backend در حال اجرا نیست یا به درستی پاسخ نمی‌دهد.

## راه‌حل: راه‌اندازی دستی

### مرحله 1: راه‌اندازی Backend

در یک ترمینال PowerShell جدید:

```powershell
# اطمینان حاصل کنید که در دایرکتوری پروژه هستید
cd "C:\Users\asus\Documents\companies\ithub\AI\products\clones\cancer diagnosing\Intelligent-software-for-diagnosing-and-treating-esophageal-cancer"

# راه‌اندازی Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**نکته:** باید پیام زیر را ببینید:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### مرحله 2: راه‌اندازی Frontend

در یک ترمینال PowerShell دیگر:

```powershell
# رفتن به دایرکتوری frontend
cd frontend

# راه‌اندازی Frontend
npm run dev
```

**نکته:** باید پیام زیر را ببینید:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

### مرحله 3: بررسی

1. Backend را بررسی کنید: http://localhost:8001/health
   - باید `{"status":"healthy",...}` را ببینید

2. Frontend را بررسی کنید: http://localhost:3000
   - Dashboard باید باز شود

3. Console مرورگر را بررسی کنید (F12):
   - اگر خطای ERR_FAILED می‌بینید، Backend در حال اجرا نیست
   - اگر خطای 500 می‌بینید، PostgreSQL در حال اجرا نیست

## مشکلات رایج

### Backend راه‌اندازی نمی‌شود
- بررسی کنید که Python نصب است: `python --version`
- بررسی کنید که dependencies نصب شده‌اند: `pip install -r requirements.txt`
- بررسی کنید که پورت 8001 آزاد است

### Frontend به Backend متصل نمی‌شود
- بررسی کنید که Backend روی پورت 8001 در حال اجرا است
- بررسی کنید که Frontend از `/api/v1` استفاده می‌کند (نه `http://localhost:8001/api/v1`)
- Frontend را restart کنید

### خطای 500 از API
- PostgreSQL باید در حال اجرا باشد:
  ```powershell
  docker-compose up -d postgres
  ```
- 30 ثانیه صبر کنید تا PostgreSQL آماده شود
- Backend را restart کنید

## دستورات سریع

```powershell
# راه‌اندازی همه چیز
# ترمینال 1:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# ترمینال 2:
cd frontend
npm run dev

# ترمینال 3 (اگر PostgreSQL نیاز است):
docker-compose up -d postgres
```

