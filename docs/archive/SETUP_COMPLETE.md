# راهنمای کامل راه‌اندازی سیستم

این سند شامل تمام مراحل راه‌اندازی سیستم است.

## ✅ مراحل راه‌اندازی

### 1. Migration: ایجاد جداول دیتابیس ✅

#### روش 1: استفاده از Script

**Windows (PowerShell):**
```powershell
.\scripts\run_migrations.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/run_migrations.sh
./scripts/run_migrations.sh
```

#### روش 2: دستی

```bash
# ایجاد migration اولیه
alembic revision --autogenerate -m "Initial migration: Create all tables"

# اعمال migrations
alembic upgrade head
```

#### بررسی

```bash
# بررسی وضعیت migrations
alembic current

# مشاهده تاریخچه
alembic history
```

---

### 2. Initial Setup: وارد کردن داده‌های اولیه ✅

#### اجرای Script

```bash
python scripts/seed_initial_data.py
```

این script:
- ✅ ایجاد جداول (اگر وجود نداشته باشند)
- ✅ ایجاد کاربران اولیه (admin, doctor, radiologist, nurse, researcher)
- ✅ وارد کردن 50 بیمار نمونه
- ✅ ایجاد داده‌های compliance اولیه

#### کاربران پیش‌فرض

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| doctor1 | doctor123 | Physician |
| radiologist1 | radio123 | Radiologist |
| nurse1 | nurse123 | Nurse |
| researcher1 | research123 | Researcher |

⚠️ **مهم:** در production حتماً رمزهای عبور را تغییر دهید!

---

### 3. Training: آموزش تیم ✅

#### ایجاد ماژول‌های آموزش

```bash
python scripts/create_initial_training_modules.py
```

این script ماژول‌های زیر را ایجاد می‌کند:
1. معرفی سیستم (30 دقیقه)
2. مدیریت بیماران (45 دقیقه)
3. تحلیل تصاویر پزشکی (60 دقیقه)
4. پشتیبانی از تصمیم‌گیری بالینی (45 دقیقه)
5. راهنمای جراحی Real-Time (60 دقیقه)
6. امنیت و حریم خصوصی (30 دقیقه)
7. استفاده از API (90 دقیقه)

#### استفاده از سیستم آموزش

**API Endpoints:**
- `GET /api/v1/training/modules` - لیست ماژول‌ها
- `POST /api/v1/training/enroll` - ثبت‌نام در ماژول
- `GET /api/v1/training/progress` - پیشرفت کاربر
- `POST /api/v1/training/update-progress` - به‌روزرسانی پیشرفت
- `POST /api/v1/training/complete` - تکمیل آموزش

**مثال استفاده:**
```python
# ثبت‌نام در ماژول
POST /api/v1/training/enroll
{
  "module_id": "TRAIN_system_overview_20241219_120000"
}

# به‌روزرسانی پیشرفت
POST /api/v1/training/update-progress
{
  "enrollment_id": "ENR_user123_...",
  "progress_percentage": 50,
  "status": "in_progress"
}
```

---

### 4. Documentation: تکمیل مستندات کاربری ✅

#### مستندات موجود

1. **راهنمای کاربری** (`docs/USER_GUIDE.md`)
   - شروع کار
   - مدیریت بیماران
   - تحلیل تصاویر
   - استفاده از CDS
   - راهنمای جراحی

2. **راهنمای مدیریت** (`docs/ADMIN_GUIDE.md`)
   - نصب و راه‌اندازی
   - مدیریت دیتابیس
   - Migration
   - پیکربندی

3. **راهنمای آموزش** (`docs/TRAINING_GUIDE.md`)
   - ماژول‌های آموزش
   - برنامه آموزشی
   - آزمون‌ها

4. **مستندات API** (`/docs`)
   - Swagger UI در `/docs`
   - ReDoc در `/redoc`

#### مستندات تخصصی

- `docs/DATA_SECURITY.md` - امنیت داده
- `docs/REGULATORY_COMPLIANCE.md` - انطباق نظارتی
- `docs/REALTIME_PROCESSING.md` - پردازش Real-Time
- `docs/MLOPS_CICD_PIPELINE.md` - MLOps
- `docs/CLINICAL_INTEGRATION.md` - یکپارچه‌سازی بالینی
- `docs/EXPLAINABLE_AI.md` - Explainable AI
- `docs/TREATMENT_RESPONSE_PREDICTION.md` - پیش‌بینی پاسخ درمانی
- `docs/SURGICAL_GUIDANCE.md` - راهنمای جراحی
- `docs/MULTIMODAL_FUSION.md` - ادغام چندوجهی
- `docs/FEW_SHOT_LEARNING.md` - Few-Shot Learning

---

## 🚀 راه‌اندازی سریع

### تمام مراحل در یک دستور

**Windows:**
```powershell
# 1. Migration
.\scripts\run_migrations.ps1

# 2. Seed data
python scripts/seed_initial_data.py

# 3. Training modules
python scripts/create_initial_training_modules.py

# 4. Start server
uvicorn app.main:app --reload
```

**Linux/Mac:**
```bash
# 1. Migration
./scripts/run_migrations.sh

# 2. Seed data
python scripts/seed_initial_data.py

# 3. Training modules
python scripts/create_initial_training_modules.py

# 4. Start server
uvicorn app.main:app --reload
```

---

## ✅ بررسی راه‌اندازی

### 1. بررسی دیتابیس

```bash
# اتصال به دیتابیس
psql -U username -d inescape_db

# بررسی جداول
\dt

# بررسی کاربران
SELECT username, role FROM users;

# بررسی بیماران
SELECT COUNT(*) FROM patients;
```

### 2. بررسی API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API Documentation
open http://localhost:8000/docs
```

### 3. بررسی آموزش

```bash
# لیست ماژول‌ها
curl -X GET "http://localhost:8000/api/v1/training/modules" \
  -H "Authorization: Bearer <token>"
```

---

## 📋 Checklist راه‌اندازی

- [ ] نصب dependencies (`pip install -r requirements.txt`)
- [ ] پیکربندی `.env`
- [ ] اجرای migrations (`alembic upgrade head`)
- [ ] Seed داده‌های اولیه (`python scripts/seed_initial_data.py`)
- [ ] ایجاد ماژول‌های آموزش (`python scripts/create_initial_training_modules.py`)
- [ ] تغییر رمزهای عبور پیش‌فرض
- [ ] بررسی Health Check
- [ ] بررسی API Documentation
- [ ] تست ورود با کاربران مختلف
- [ ] بررسی دسترسی‌ها

---

## 🆘 عیب‌یابی

### مشکل: Migration اجرا نمی‌شود

**راه‌حل:**
1. بررسی اتصال دیتابیس در `.env`
2. بررسی وجود Alembic: `pip install alembic`
3. بررسی فایل `alembic.ini`

### مشکل: داده‌های اولیه وارد نمی‌شوند

**راه‌حل:**
1. بررسی لاگ‌ها
2. بررسی اتصال دیتابیس
3. اجرای دستی: `python scripts/seed_initial_data.py`

### مشکل: ماژول‌های آموزش ایجاد نمی‌شوند

**راه‌حل:**
1. بررسی جداول `training_modules` و `training_enrollments`
2. اجرای دستی: `python scripts/create_initial_training_modules.py`

---

## 📞 پشتیبانی

برای مشکلات و سوالات:
- بررسی مستندات
- بررسی لاگ‌ها
- تماس با تیم توسعه

---

**تاریخ ایجاد:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

