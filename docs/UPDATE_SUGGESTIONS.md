# پیشنهادات به‌روزرسانی و چک‌لیست فایل‌ها

این سند نتیجهٔ بررسی کامل کدبیس برای هماهنگی فایل‌ها و پیشنهادات به‌روزرسانی است.

---

## ۱. وضعیت فعلی و اصلاحات انجام‌شده

### ۱.۱ Cache Warming Service (`app/services/cache_warming_service.py`)

| مورد | وضعیت قبل | اصلاح |
|------|-----------|--------|
| `_load_dashboard_stats` | استفاده از `Patient.id` و `ImagingStudy` | مدل Patient فقط `patient_id` (PK) دارد؛ مدل تصویربرداری `ImagingData` است نه `ImagingStudy`. به `func.count(Patient.patient_id)` و `func.count(ImagingData.image_id)` تغییر داده شد. |
| `_load_patients_list` | استفاده از `p.id` و `first_name`/`last_name` | مدل Patient فیلد `id` و نام جداگانه ندارد. به `p.patient_id` و نمایش `"Patient {patient_id}"` و وضعیت بر اساس `has_cancer` تغییر داده شد. |
| `_load_synthetic_stats` | استفاده از `SyntheticDataGenerator` و `get_statistics` | کلاس واقعی `EsophagealCancerSyntheticData` است و متد `get_statistics` ندارد. با کوئری مستقیم روی Patient و ImagingData و برگرداندن آمار جایگزین شد. |
| `_load_health_metrics` | استفاده از `HealthChecker` و `get_quick_status` | کلاس واقعی `HealthCheckService` است و متد `get_quick_status` وجود ندارد. به `HealthCheckService().get_readiness()` تغییر داده شد. |

### ۱.۲ Database Indexes (`app/core/database_indexes.py`)

- **Import اضافی:** `inspect` از sqlalchemy استفاده نمی‌شد → حذف شد.
- **فراخوانی در startup:** ماژول فقط توابع ایجاد ایندکس را تعریف می‌کرد و در startup صدا زده نمی‌شد → در `app/main.py` داخل lifespan تابع `initialize_indexes()` فراخوانی شد.

### ۱.۳ Main (`app/main.py`)

- در رویداد startup، بعد از `init_db()` فراخوانی `initialize_indexes()` اضافه شد تا ایندکس‌های استراتژیک (از جمله partial indexes در PostgreSQL) پس از ایجاد جداول ساخته شوند.

---

## ۲. چک‌لیست فایل‌های مرتبط با قابلیت‌های اضافه‌شده

| فایل | نقش | وضعیت |
|------|-----|--------|
| `app/core/config.py` | تنظیمات Cache و Cache Warming | ✅ تنظیمات CACHE_* و CACHE_TTL_* وجود دارد |
| `app/core/advanced_cache.py` | کش چندسطحی (L1/L2)، فشرده‌سازی، دکوراتور `ml_cached` | ✅ پیاده‌سازی کامل |
| `app/core/cache.py` | کش قدیمی فقط Redis | ✅ برای سازگاری با عقب ماندگی نگه داشته شده؛ endpointها هنوز از CacheManager استفاده می‌کنند |
| `app/core/redis_client.py` | اتصال Redis | ✅ بدون تغییر |
| `app/core/database_indexes.py` | ایندکس استراتژیک، partial indexes، گزارش سلامت | ✅ اصلاح import و فراخوانی از main |
| `app/services/cache_warming_service.py` | گرم کردن کش برای endpointهای پرتردد | ✅ اصلاح مدل‌ها و سرویس سلامت و آمار |
| `app/main.py` | Startup: init_db، initialize_indexes، cache warming | ✅ فراخوانی initialize_indexes و cache warming اضافه شده |
| `app/models/patient.py` | ایندکس روی has_cancer، created_at، age، و غیره | ✅ `__table_args__` با Indexها |
| `app/models/imaging_data.py` | ایندکس روی patient_id، modality، date | ✅ `__table_args__` با Indexها |
| `app/models/clinical_data.py` | ایندکس روی patient_id، TNM، tumor_location | ✅ `__table_args__` با Indexها |
| `app/models/treatment_data.py` | ایندکس روی patient_id، response، survival، dates | ✅ `__table_args__` با Indexها |
| `app/models/genomic_data.py` | ایندکس روی patient_id، pdl1، msi، platform | ✅ `__table_args__` با Indexها (به‌روزرسانی شده) |

---

## ۳. پیشنهادات به‌روزرسانی بعدی

### ۳.۱ یکپارچه‌سازی کش در API

- **وضعیت:** endpointهای `patients`، `ml_models`، `synthetic_data` از `app.core.cache.CacheManager` (فقط Redis) استفاده می‌کنند.
- **پیشنهاد:** برای endpointهای پرتردد (مثلاً dashboard، لیست بیماران، لیست مدل‌ها) استفاده از `app.core.advanced_cache.get_cache_manager()` (کش چندسطحی + فشرده‌سازی) در نظر گرفته شود.
- **فایل‌ها:** `app/api/v1/endpoints/patients.py`, `app/api/v1/endpoints/ml_models.py`, `app/api/v1/endpoints/synthetic_data.py`.

### ۳.۲ ایندکس در سطح مدل برای treatment و genomic

- **وضعیت:** ایندکس‌های `treatment_data` و `genomic_data` در مدل‌ها با `__table_args__` تعریف شده‌اند (treatment_data از قبل، genomic_data در این به‌روزرسانی اضافه شد). ماژول `app.core.database_indexes` همچنان برای partial indexes (مثلاً `ix_treatment_complications` با `WHERE treatment_complications = true`) و ایندکس‌های اضافی در PostgreSQL، و برای `create_all_indexes` / گزارش سلامت ایندکس مفید است.

### ۳.۳ Read Replicas

- **وضعیت:** پیاده‌سازی شده. در `app/core/config.py` تنظیم اختیاری `DATABASE_READ_REPLICA_URL` اضافه شده؛ در `app/core/database.py` موتور و session جدا برای خواندن (`read_engine`, `SessionLocalRead`, `get_read_db`) تعریف شده و در صورت تنظیم replica، کوئری‌های فقط-خواندنی از آن استفاده می‌کنند.
- **استفاده:** در production با تنظیم env مثلاً `DATABASE_READ_REPLICA_URL=postgresql://user:pass@replica-host:5432/db` داشبورد، آمار، گزارش‌ها و لیست‌های فقط-خواندنی از replica استفاده می‌کنند. در صورت عدم تنظیم، همان primary استفاده می‌شود.

### ۳.۴ API برای وضعیت کش و ایندکس

- **وضعیت:** پیاده‌سازی شده. در `app/api/v1/endpoints/admin.py` دو endpoint تعریف شده‌اند:
  - **GET /api/v1/admin/cache/stats** — آمار کش چندسطحی (L1، L2، فشرده‌سازی و نسبت hit).
  - **GET /api/v1/admin/database/index-health** — گزارش سلامت ایندکس (`get_index_health_report`: وضعیت ایندکس‌های استراتژیک، پوشش، و در PostgreSQL تحلیل استفاده).

### ۳.۵ تست‌ها

- **وضعیت:** پیاده‌سازی شده.
  - **`tests/test_cache_warming_service.py`:** تست واحد برای `CacheWarmingService` با mock برای DB و Redis (ثبت warmerها، `warm_startup`، `get_warming_status`، `get_cache_stats`، `_load_cds_services`، غیرفعال بودن با `CACHE_WARMING_ENABLED=False`).
  - **`tests/test_database_indexes.py`:** تست برای `create_all_indexes` با SQLite در حافظه، `create_index_sql`، `get_database_type`، و ساختار `get_index_health_report`.

---

## ۴. خلاصه اصلاحات اعمال‌شده در این به‌روزرسانی

1. **cache_warming_service.py:** اصلاح ارجاع به مدل‌ها و سرویس‌ها (Patient/ImagingData، patient_id، HealthCheckService، آمار synthetic با کوئری مستقیم).
2. **database_indexes.py:** حذف import استفاده‌نشده `inspect`.
3. **main.py:** فراخوانی `initialize_indexes()` در lifespan هنگام startup.

با این تغییرات، گرم کردن کش و ایجاد ایندکس‌های استراتژیک با مدل‌ها و سرویس‌های فعلی سازگار شده و در راه‌اندازی اپلیکیشن اجرا می‌شوند.
