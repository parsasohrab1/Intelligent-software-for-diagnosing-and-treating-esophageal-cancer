# مدیریت داده‌های داشبورد
# Dashboard Data Management

راهنمای کامل برای ذخیره، پاک‌سازی و بازیابی داده‌های داشبورد

## خلاصه

این اسکریپت‌ها به شما امکان می‌دهند:
1. **ذخیره** تمام داده‌های فعلی دیتابیس
2. **پاک‌سازی** داده‌های غیرضروری
3. **بازیابی** داده‌های ذخیره شده
4. **تنظیم** داشبورد برای اجرای زنده با داده‌های ثابت

## اسکریپت‌ها

### 1. `save_current_data.py` - ذخیره داده‌های فعلی

تمام داده‌های فعلی دیتابیس را در یک فایل JSON ذخیره می‌کند.

```bash
python scripts/save_current_data.py
```

یا با نام فایل سفارشی:
```bash
python scripts/save_current_data.py --output my_data.json
```

**خروجی:** فایل `data_snapshot.json` شامل:
- تمام بیماران (Patients)
- تمام داده‌های تصویربرداری (Imaging Data)
- تمام داده‌های بالینی (Clinical Data)
- تمام داده‌های ژنومیک (Genomic Data)
- تمام داده‌های درمان (Treatment Data)
- تمام کاربران (Users)

### 2. `clear_unnecessary_data.py` - پاک‌سازی داده‌های غیرضروری

داده‌های غیرضروری را از دیتابیس پاک می‌کند:
- بیماران تکراری
- داده‌های بدون بیمار مرتبط (orphaned data)
- داده‌های تست (اختیاری)

```bash
# پاک‌سازی با حفظ داده‌های سنتتیک (CAN/NOR)
python scripts/clear_unnecessary_data.py

# پاک‌سازی کامل (حتی داده‌های سنتتیک)
python scripts/clear_unnecessary_data.py --no-synthetic
```

### 3. `restore_saved_data.py` - بازیابی داده‌های ذخیره شده

داده‌های ذخیره شده را از فایل snapshot بازیابی می‌کند.

```bash
# بازیابی بدون پاک‌سازی داده‌های موجود
python scripts/restore_saved_data.py

# بازیابی با پاک‌سازی داده‌های موجود
python scripts/restore_saved_data.py --clear

# استفاده از فایل سفارشی
python scripts/restore_saved_data.py --file my_data.json --clear
```

### 4. `setup_live_dashboard_data.py` - تنظیم داشبورد زنده

این اسکریپت تمام مراحل را به صورت خودکار انجام می‌دهد:
1. ذخیره داده‌های فعلی
2. پاک‌سازی داده‌های غیرضروری
3. بازیابی داده‌های ذخیره شده

```bash
python scripts/setup_live_dashboard_data.py
```

## استفاده

### سناریو 1: ذخیره و تنظیم داده‌های فعلی

```bash
# 1. ذخیره داده‌های فعلی
python scripts/save_current_data.py

# 2. پاک‌سازی داده‌های غیرضروری
python scripts/clear_unnecessary_data.py

# 3. بازیابی داده‌های پاک شده (اختیاری)
python scripts/restore_saved_data.py --clear
```

یا به صورت یکجا:
```bash
python scripts/setup_live_dashboard_data.py
```

### سناریو 2: بازیابی داده‌ها در هر بار اجرا

پس از اجرای `setup_live_dashboard_data.py`، سیستم به صورت خودکار:
- در هر بار راه‌اندازی داشبورد، ابتدا سعی می‌کند داده‌ها را از `data_snapshot.json` بازیابی کند
- اگر snapshot موجود نباشد یا بازیابی ناموفق باشد، داده‌های جدید تولید می‌کند

### سناریو 3: به‌روزرسانی داده‌ها

```bash
# 1. ذخیره داده‌های جدید
python scripts/save_current_data.py

# 2. تنظیم مجدد
python scripts/setup_live_dashboard_data.py
```

## ساختار فایل Snapshot

فایل `data_snapshot.json` شامل:

```json
{
  "metadata": {
    "created_at": "2024-01-01T12:00:00",
    "version": "1.0",
    "description": "Complete database snapshot"
  },
  "data": {
    "patients": [...],
    "imaging_data": [...],
    "clinical_data": [...],
    "genomic_data": [...],
    "treatment_data": [...],
    "users": [...]
  }
}
```

## نکات مهم

1. **پشتیبان‌گیری:** همیشه قبل از پاک‌سازی، داده‌ها را ذخیره کنید
2. **فایل Snapshot:** فایل `data_snapshot.json` را در سیستم کنترل نسخه (git) نگه دارید
3. **امنیت:** فایل snapshot شامل پسورد کاربران نیست (برای امنیت)
4. **بازیابی خودکار:** سیستم به صورت خودکار در هر بار راه‌اندازی، داده‌ها را از snapshot بازیابی می‌کند

## عیب‌یابی

### خطا در ذخیره داده
- بررسی اتصال به دیتابیس
- بررسی دسترسی نوشتن در مسیر فایل

### خطا در بازیابی
- بررسی وجود فایل snapshot
- بررسی فرمت JSON فایل
- بررسی اتصال به دیتابیس

### داده‌ها نمایش داده نمی‌شوند
- بررسی لاگ‌های سیستم
- بررسی وجود snapshot
- اجرای دستی `restore_saved_data.py`

## مثال کامل

```bash
# 1. ذخیره داده‌های فعلی
python scripts/save_current_data.py

# 2. تنظیم داشبورد زنده
python scripts/setup_live_dashboard_data.py

# 3. راه‌اندازی داشبورد
# Backend:
python -m uvicorn app.main:app --reload

# Frontend:
cd frontend
npm start
```

## فایل‌های مرتبط

- `data_snapshot.json` - فایل ذخیره داده‌ها
- `app/core/database.py` - منطق بازیابی خودکار
- `scripts/seed_initial_data.py` - تولید داده‌های اولیه
