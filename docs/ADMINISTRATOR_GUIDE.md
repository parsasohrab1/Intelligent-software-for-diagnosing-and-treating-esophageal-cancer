# راهنمای مدیر سیستم

این راهنما برای مدیران سیستم و تیم IT تهیه شده است.

## فهرست مطالب

1. [نصب و راه‌اندازی](#نصب-و-راهاندازی)
2. [Migration دیتابیس](#migration-دیتابیس)
3. [وارد کردن داده‌های اولیه](#وارد-کردن-دادههای-اولیه)
4. [مدیریت کاربران](#مدیریت-کاربران)
5. [پشتیبان‌گیری](#پشتیبانگیری)
6. [مانیتورینگ](#مانیتورینگ)
7. [عیب‌یابی](#عیبیابی)

## نصب و راه‌اندازی

### پیش‌نیازها

- Docker و Docker Compose
- PostgreSQL 12+
- MongoDB 4.4+
- Python 3.9+
- حداقل 8GB RAM
- حداقل 50GB فضای دیسک

### نصب

```bash
# Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Build and start services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Run setup script
python scripts/setup_production.py
```

## Migration دیتابیس

### ایجاد جداول

```bash
# Option 1: Using Alembic (recommended)
alembic upgrade head

# Option 2: Using script
python scripts/create_migration.py
```

### بررسی جداول

```bash
# Connect to database
psql -U your_user -d your_database

# List tables
\dt

# Check table structure
\d patients
```

### Rollback

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

## وارد کردن داده‌های اولیه

### Seed Data

```bash
# Run seed script
python scripts/seed_initial_data.py
```

این اسکریپت:
- ایجاد کاربر Admin (username: admin, password: admin123)
- ایجاد کاربر Doctor (username: doctor, password: doctor123)
- ایجاد 5 بیمار نمونه
- ایجاد داده‌های بالینی نمونه

**⚠️ مهم:** پس از اولین ورود، رمز عبور Admin را تغییر دهید!

### ایجاد کاربران اضافی

```bash
# Using script
python scripts/create_admin_user.py \
    --username new_admin \
    --email admin@hospital.com \
    --password secure_password
```

## مدیریت کاربران

### ایجاد کاربر جدید

1. ورود به سیستم به عنوان Admin
2. رفتن به "مدیریت کاربران"
3. کلیک روی "کاربر جدید"
4. پر کردن فرم:
   - نام کاربری
   - ایمیل
   - رمز عبور
   - نقش (Role)
   - نام کامل
5. کلیک روی "ذخیره"

### تغییر نقش کاربر

1. باز کردن "مدیریت کاربران"
2. پیدا کردن کاربر
3. کلیک روی "ویرایش"
4. تغییر نقش
5. ذخیره

### غیرفعال کردن کاربر

1. باز کردن "مدیریت کاربران"
2. پیدا کردن کاربر
3. کلیک روی "غیرفعال"
4. تأیید

## پشتیبان‌گیری

### Backup دیتابیس PostgreSQL

```bash
# Manual backup
pg_dump -U your_user -d your_database > backup_$(date +%Y%m%d).sql

# Restore
psql -U your_user -d your_database < backup_20241219.sql
```

### Backup خودکار

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup_script.sh
```

### Backup MongoDB

```bash
# Backup
mongodump --uri="mongodb://user:password@localhost:27017/database" --out=/backup

# Restore
mongorestore --uri="mongodb://user:password@localhost:27017/database" /backup
```

## مانیتورینگ

### Health Check

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check database connection
python -c "from app.core.database import engine; engine.connect()"
```

### Logs

```bash
# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f postgres

# View specific service
docker-compose logs -f <service_name>
```

### Performance Monitoring

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **API Metrics**: `/api/v1/metrics`

## عیب‌یابی

### مشکلات رایج

#### مشکل: دیتابیس متصل نمی‌شود

**راه‌حل:**
1. بررسی اجرای Docker containers
2. بررسی تنظیمات DATABASE_URL در .env
3. بررسی لاگ‌های PostgreSQL

```bash
docker-compose ps
docker-compose logs postgres
```

#### مشکل: جداول ایجاد نشده

**راه‌حل:**
1. اجرای migration
2. بررسی لاگ‌ها

```bash
alembic upgrade head
docker-compose logs app
```

#### مشکل: کاربر نمی‌تواند وارد شود

**راه‌حل:**
1. بررسی وجود کاربر
2. بررسی فعال بودن کاربر
3. Reset رمز عبور

```bash
python scripts/create_admin_user.py --username admin --password new_password
```

## امنیت

### تنظیمات امنیتی

1. **تغییر رمزهای پیش‌فرض**
   - Admin password
   - Database passwords
   - API keys

2. **فعال‌سازی SSL/TLS**
   - نصب certificate
   - تنظیم HTTPS

3. **فایروال**
   - محدود کردن دسترسی
   - Whitelist IPs

4. **Backup Encryption**
   - رمزگذاری backup files
   - Secure storage

## به‌روزرسانی

### به‌روزرسانی سیستم

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose build --no-cache

# Run migrations
alembic upgrade head

# Restart services
docker-compose restart
```

### به‌روزرسانی مدل‌های AI

1. آپلود مدل جدید به Model Registry
2. تست مدل
3. فعال‌سازی در production
4. مانیتورینگ عملکرد

## پشتیبانی

برای مشکلات فنی:
- **ایمیل**: admin@hospital.com
- **تلفن**: +1234567890
- **ساعات**: 24/7

---

**نسخه:** 1.0  
**آخرین به‌روزرسانی:** 2024-12-19

