# راهنمای سریع راه‌اندازی INEsCape

## پیش‌نیازها

1. ✅ Python 3.9+ نصب شده
2. ✅ وابستگی‌های Python نصب شده (`pip install -r requirements.txt`)
3. ⚠️ Docker Desktop باید در حال اجرا باشد

## مراحل راه‌اندازی

### مرحله 1: راه‌اندازی Docker Desktop

1. Docker Desktop را از منوی Start باز کنید
2. صبر کنید تا کاملاً راه‌اندازی شود (آیکون Docker در system tray سبز شود)
3. بررسی کنید که Docker در حال اجرا است:
   ```bash
   docker ps
   ```

### مرحله 2: بررسی وضعیت سرویس‌ها

```bash
python scripts/check_services.py
```

این اسکریپت وضعیت PostgreSQL، MongoDB و Redis را بررسی می‌کند.

### مرحله 3: راه‌اندازی سرویس‌های Docker

```bash
docker-compose up -d
```

این دستور سرویس‌های زیر را راه‌اندازی می‌کند:
- PostgreSQL (پورت 5432)
- MongoDB (پورت 27017)
- Redis (پورت 6379)
- MinIO (پورت 9000, 9001)
- Prometheus (پورت 9090)
- Grafana (پورت 3000)

### مرحله 4: بررسی وضعیت Containers

```bash
docker-compose ps
```

همه containers باید `Up` باشند.

### مرحله 5: راه‌اندازی پایگاه داده

```bash
python scripts/init_database.py
```

این اسکریپت:
- تمام جداول پایگاه داده را ایجاد می‌کند
- Schema را راه‌اندازی می‌کند

### مرحله 6: اجرای سرور

```bash
python scripts/run_server.py
```

یا:

```bash
uvicorn app.main:app --reload
```

### مرحله 7: دسترسی به API

- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Root:** http://localhost:8000/

## عیب‌یابی

### مشکل: Docker Desktop در حال اجرا نیست

**خطا:**
```
error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/...
```

**راه‌حل:**
1. Docker Desktop را باز کنید
2. صبر کنید تا کاملاً راه‌اندازی شود
3. دوباره `docker-compose up -d` را اجرا کنید

### مشکل: پورت در حال استفاده است

**خطا:**
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**راه‌حل:**
1. بررسی کنید که چه process‌ای از پورت استفاده می‌کند:
   ```powershell
   netstat -ano | findstr :5432
   ```
2. یا پورت را در `docker-compose.yml` تغییر دهید

### مشکل: اتصال به پایگاه داده

**خطا:**
```
connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**راه‌حل:**
1. بررسی کنید که PostgreSQL container در حال اجرا است:
   ```bash
   docker-compose ps postgres
   ```
2. بررسی لاگ‌ها:
   ```bash
   docker-compose logs postgres
   ```
3. Container را دوباره راه‌اندازی کنید:
   ```bash
   docker-compose restart postgres
   ```

### مشکل: فایل .env وجود ندارد

**راه‌حل:**
```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید و مقادیر مناسب را تنظیم کنید.

## دستورات مفید

### مشاهده لاگ‌ها
```bash
docker-compose logs -f
```

### توقف سرویس‌ها
```bash
docker-compose down
```

### توقف و حذف volumes
```bash
docker-compose down -v
```

### بازسازی containers
```bash
docker-compose up -d --build
```

### تست اتصال به پایگاه داده
```bash
python scripts/test_db_connection.py
```

## مراحل بعدی

پس از راه‌اندازی موفق:

1. ✅ بررسی کنید که API در http://localhost:8000/docs در دسترس است
2. ✅ Health check را تست کنید: http://localhost:8000/health
3. ✅ به فاز 2 (تولید داده سنتتیک) بروید

## پشتیبانی

در صورت بروز مشکل:
1. بررسی کنید که Docker Desktop در حال اجرا است
2. بررسی لاگ‌های Docker: `docker-compose logs`
3. بررسی وضعیت سرویس‌ها: `python scripts/check_services.py`

