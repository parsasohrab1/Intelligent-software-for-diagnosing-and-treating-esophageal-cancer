# راهنمای مدیریت سیستم

این راهنمای جامع برای مدیران سیستم و توسعه‌دهندگان تهیه شده است.

## فهرست مطالب

1. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
2. [مدیریت دیتابیس](#مدیریت-دیتابیس)
3. [Migration](#migration)
4. [مدیریت کاربران](#مدیریت-کاربران)
5. [پیکربندی سیستم](#پیکربندی-سیستم)
6. [نظارت و مانیتورینگ](#نظارت-و-مانیتورینگ)
7. [پشتیبان‌گیری](#پشتیبان‌گیری)

---

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.8+
- PostgreSQL 12+ یا SQLite
- Docker (اختیاری)
- MongoDB (برای Model Registry)

### نصب

```bash
# Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### راه‌اندازی دیتابیس

```bash
# Create database
createdb inescape_db

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_initial_data.py
```

---

## مدیریت دیتابیس

### Migration

#### ایجاد Migration جدید

```bash
alembic revision --autogenerate -m "Description"
```

#### اعمال Migration

```bash
alembic upgrade head
```

#### Rollback

```bash
alembic downgrade -1
```

### Backup

```bash
# PostgreSQL
pg_dump -U username inescape_db > backup.sql

# Restore
psql -U username inescape_db < backup.sql
```

---

## مدیریت کاربران

### ایجاد کاربر جدید

```bash
python scripts/create_admin_user.py \
    --username newuser \
    --email user@example.com \
    --password password123 \
    --role physician
```

### نقش‌های موجود

- `admin`: مدیر سیستم
- `physician`: پزشک
- `radiologist`: رادیولوژیست
- `nurse`: پرستار
- `researcher`: محقق
- `developer`: توسعه‌دهنده

---

## پیکربندی سیستم

### تنظیمات اصلی

فایل `.env` شامل:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/inescape_db

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# API
API_V1_PREFIX=/api/v1

# Features
REALTIME_ENABLED=true
XAI_ENABLED=true
```

---

## نظارت و مانیتورینگ

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Logs

```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log
```

---

## پشتیبان‌گیری

### Backup روزانه

```bash
# Database backup
pg_dump -U username inescape_db > backup_$(date +%Y%m%d).sql

# Model files backup
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
```

---

**نسخه:** 1.0  
**تاریخ به‌روزرسانی:** 2024-12-19

