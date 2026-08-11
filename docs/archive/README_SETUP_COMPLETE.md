# راهنمای کامل راه‌اندازی سیستم

این راهنمای جامع برای راه‌اندازی کامل سیستم است.

## 🚀 راه‌اندازی سریع

### تمام مراحل در یک دستور

**Windows PowerShell:**
```powershell
# 1. Migration
.\scripts\run_migrations.ps1

# 2. Seed initial data
python scripts/seed_initial_data.py

# 3. Create training modules
python scripts/create_initial_training_modules.py

# 4. Start server
uvicorn app.main:app --reload
```

**Linux/Mac:**
```bash
# 1. Migration
chmod +x scripts/run_migrations.sh
./scripts/run_migrations.sh

# 2. Seed initial data
python scripts/seed_initial_data.py

# 3. Create training modules
python scripts/create_initial_training_modules.py

# 4. Start server
uvicorn app.main:app --reload
```

---

## 📋 مراحل تفصیلی

### 1. Migration: ایجاد جداول دیتابیس

#### پیش‌نیازها
- PostgreSQL یا SQLite
- Alembic نصب شده: `pip install alembic`

#### اجرا

**روش 1: استفاده از Script**
```bash
# Windows
.\scripts\run_migrations.ps1

# Linux/Mac
./scripts/run_migrations.sh
```

**روش 2: دستی**
```bash
# ایجاد migration اولیه
alembic revision --autogenerate -m "Initial migration: Create all tables"

# اعمال migrations
alembic upgrade head
```

#### بررسی
```bash
# وضعیت فعلی
alembic current

# تاریخچه
alembic history
```

---

### 2. Initial Setup: وارد کردن داده‌های اولیه

#### اجرا
```bash
python scripts/seed_initial_data.py
```

#### چه چیزی ایجاد می‌شود؟

**کاربران:**
- `admin` / `admin123` (Admin)
- `doctor1` / `doctor123` (Physician)
- `radiologist1` / `radio123` (Radiologist)
- `nurse1` / `nurse123` (Nurse)
- `researcher1` / `research123` (Researcher)

**داده‌ها:**
- 50 بیمار نمونه
- داده‌های بالینی
- نتایج آزمایش
- تصاویر پزشکی
- داده‌های compliance

⚠️ **مهم:** در production حتماً رمزهای عبور را تغییر دهید!

---

### 3. Training: آموزش تیم

#### ایجاد ماژول‌های آموزش
```bash
python scripts/create_initial_training_modules.py
```

#### ماژول‌های ایجاد شده

1. **معرفی سیستم** (30 دقیقه)
   - آشنایی کلی با سیستم
   - ویژگی‌های اصلی

2. **مدیریت بیماران** (45 دقیقه)
   - افزودن و مدیریت بیماران
   - داده‌های بالینی

3. **تحلیل تصاویر پزشکی** (60 دقیقه)
   - آپلود و تحلیل تصاویر
   - Explainable AI

4. **پشتیبانی از تصمیم‌گیری بالینی** (45 دقیقه)
   - پیش‌بینی ریسک
   - توصیه‌های درمانی

5. **راهنمای جراحی Real-Time** (60 دقیقه)
   - استفاده در حین عمل
   - تفسیر نتایج

6. **امنیت و حریم خصوصی** (30 دقیقه)
   - اصول امنیت
   - انطباق با استانداردها

7. **استفاده از API** (90 دقیقه)
   - برای توسعه‌دهندگان
   - یکپارچه‌سازی

#### استفاده از API

```bash
# لیست ماژول‌ها
GET /api/v1/training/modules

# ثبت‌نام
POST /api/v1/training/enroll
{
  "module_id": "TRAIN_system_overview_..."
}

# پیشرفت
GET /api/v1/training/progress
```

---

### 4. Documentation: تکمیل مستندات کاربری

#### مستندات موجود

**برای کاربران:**
- `docs/USER_GUIDE.md` - راهنمای کاربری کامل
- `docs/TRAINING_GUIDE.md` - راهنمای آموزش

**برای مدیران:**
- `docs/ADMIN_GUIDE.md` - راهنمای مدیریت
- `SETUP_COMPLETE.md` - راهنمای راه‌اندازی

**برای توسعه‌دهندگان:**
- `/docs` - Swagger UI
- `/redoc` - ReDoc

**مستندات تخصصی:**
- `docs/DATA_SECURITY.md`
- `docs/REGULATORY_COMPLIANCE.md`
- `docs/REALTIME_PROCESSING.md`
- `docs/MLOPS_CICD_PIPELINE.md`
- `docs/CLINICAL_INTEGRATION.md`
- `docs/EXPLAINABLE_AI.md`
- `docs/TREATMENT_RESPONSE_PREDICTION.md`
- `docs/SURGICAL_GUIDANCE.md`
- `docs/MULTIMODAL_FUSION.md`
- `docs/FEW_SHOT_LEARNING.md`

---

## ✅ Checklist راه‌اندازی

- [ ] نصب dependencies
- [ ] پیکربندی `.env`
- [ ] اجرای migrations
- [ ] Seed داده‌های اولیه
- [ ] ایجاد ماژول‌های آموزش
- [ ] تغییر رمزهای عبور
- [ ] بررسی Health Check
- [ ] بررسی API Documentation
- [ ] تست ورود
- [ ] بررسی دسترسی‌ها

---

## 🔍 بررسی راه‌اندازی

### 1. بررسی دیتابیس
```bash
psql -U username -d inescape_db -c "SELECT COUNT(*) FROM users;"
psql -U username -d inescape_db -c "SELECT COUNT(*) FROM patients;"
```

### 2. بررسی API
```bash
curl http://localhost:8000/api/v1/health
```

### 3. بررسی آموزش
```bash
curl -X GET "http://localhost:8000/api/v1/training/modules" \
  -H "Authorization: Bearer <token>"
```

---

## 📞 پشتیبانی

برای مشکلات:
1. بررسی مستندات
2. بررسی لاگ‌ها
3. تماس با تیم توسعه

---

**تاریخ:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

