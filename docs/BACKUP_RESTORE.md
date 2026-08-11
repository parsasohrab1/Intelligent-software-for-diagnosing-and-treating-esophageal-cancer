# پشتیبان‌گیری و بازیابی پایگاه‌های داده (Backup & Restore)

> **وضعیت:** اسکریپت‌های این سند تازه اضافه شده‌اند و **هنوز روی یک پایگاه‌دادهٔ واقعی (زنده) اجرا و تأیید نشده‌اند** (به دلیل نبود دسترسی Docker/DB در محیط توسعهٔ فعلی). پیش از تکیه‌کردن بر این ابزارها در عملیات واقعی، حتماً بخش «۶. رویهٔ تأیید دستی» را یک‌بار کامل اجرا کنید.

این سند نحوهٔ پشتیبان‌گیری و بازیابی پایگاه‌های داده PostgreSQL و MongoDB پروژه INEsCape را توضیح می‌دهد.

---

## ۱. چه چیزی پشتیبان‌گیری می‌شود و چه چیزی نه

| منبع داده | پشتیبان‌گیری می‌شود؟ | ابزار | توضیح |
|---|---|---|---|
| PostgreSQL (`POSTGRES_DB`) | ✅ بله | `pg_dump` / `pg_restore` | داده‌های بالینی بیماران (Patient، ClinicalData، TreatmentData، GenomicData و غیره) اینجا نگه‌داری می‌شود. |
| MongoDB (`MONGODB_DB`) | ✅ بله | `mongodump` / `mongorestore` | متادیتا/داده‌های تکمیلی که در Mongo نگه‌داری می‌شوند. |
| Redis (کش) | ❌ خیر | — | Redis صرفاً کش است (`app/core/cache.py`, `app/core/advanced_cache.py`). داده در آن دورریختنی و قابل بازسازی از PostgreSQL/Mongo است؛ پشتیبان‌گیری از آن لازم و ارزشمند نیست. |
| فایل‌های مدل ML / تصاویر MRI روی دیسک (`models/`, `data/`, `collected_data/`) | ❌ خیر (خارج از محدودهٔ این سند) | — | این‌ها فایل‌سیستمی هستند، نه پایگاه‌داده؛ نیاز به راهکار پشتیبان‌گیری فایل جداگانه (مثلاً rsync/snapshot دیسک) دارند که در این تغییر پیاده‌سازی نشده است. |

---

## ۲. اسکریپت‌ها

| اسکریپت | پلتفرم | کار |
|---|---|---|
| `scripts/backup_postgres.sh` / `.ps1` | Linux/macOS · Windows | گرفتن dump از PostgreSQL با `pg_dump -Fc` (فرمت custom) در `backups/postgres/<db>_<timestamp>.dump` |
| `scripts/restore_postgres.sh` / `.ps1` | Linux/macOS · Windows | بازیابی PostgreSQL از فایل dump با `pg_restore --clean --if-exists` |
| `scripts/backup_mongo.sh` / `.ps1` | Linux/macOS · Windows | گرفتن dump از MongoDB با `mongodump` در `backups/mongo/<timestamp>/` |
| `scripts/restore_mongo.sh` / `.ps1` | Linux/macOS · Windows | بازیابی MongoDB از پوشهٔ dump با `mongorestore --drop` |

### ۲.۱ متغیرهای محیطی مورد نیاز

همان نام‌هایی که در `app/core/config.py` و `docker-compose.prod.yml` استفاده شده‌اند:

**PostgreSQL:** `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

**MongoDB:** `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DB`, `MONGODB_USER`, `MONGODB_PASSWORD`
(اختیاری: `MONGODB_AUTH_DB` اگر کاربر Mongo روی دیتابیس دیگری غیر از `MONGODB_DB` احراز هویت می‌شود، مثلاً `admin`.)

اگر هرکدام از متغیرهای الزامی تنظیم نشده باشند، اسکریپت‌ها بلافاصله با پیام خطا و کد خروج غیرصفر متوقف می‌شوند (fail-fast).

### ۲.۲ نمونهٔ استفاده

```bash
# پشتیبان‌گیری PostgreSQL
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=inescape \
       POSTGRES_USER=inescape_user POSTGRES_PASSWORD=********
./scripts/backup_postgres.sh
# خروجی: backups/postgres/inescape_20260712T083000Z.dump

# بازیابی PostgreSQL (ابتدا بدون --yes برای پیش‌نمایش)
./scripts/restore_postgres.sh backups/postgres/inescape_20260712T083000Z.dump
./scripts/restore_postgres.sh backups/postgres/inescape_20260712T083000Z.dump --yes

# پشتیبان‌گیری MongoDB
export MONGODB_HOST=localhost MONGODB_PORT=27017 MONGODB_DB=inescape_metadata \
       MONGODB_USER=inescape_user MONGODB_PASSWORD=********
./scripts/backup_mongo.sh
# خروجی: backups/mongo/20260712T083000Z/

# بازیابی MongoDB
./scripts/restore_mongo.sh backups/mongo/20260712T083000Z
./scripts/restore_mongo.sh backups/mongo/20260712T083000Z --yes
```

معادل PowerShell همین دستورات با پسوند `.ps1` و همان آرگومان‌ها در دسترس است (مثلاً `.\scripts\backup_postgres.ps1`).

### ۲.۳ نکتهٔ ایمنی (Restore مخرب است)

هر دو اسکریپت `restore_*` **بدون آرگومان `--yes`** فقط توضیح می‌دهند چه کاری قرار است انجام شود و بدون هیچ تغییری در پایگاه‌داده خارج می‌شوند. اجرای واقعی (که داده‌های موجود را با `--clean --if-exists` / `--drop` پاک و جایگزین می‌کند) فقط با پاس‌دادن `--yes` انجام می‌شود.

---

## ۳. تفاوت نگه‌داری عملیاتی (Backup Retention) با نگه‌داری قانونی (Compliance Retention)

این دو مفهوم را نباید با هم اشتباه گرفت:

- **`DATA_RETENTION_DAYS = 2555` روز (۷ سال)** در `app/core/config.py` یک تنظیم **قانونی/انطباقی (HIPAA)** است: مدت‌زمانی که رکوردهای بیمار باید در سیستم production در دسترس/قابل‌بازیابی بمانند، نه سیاست نگه‌داری فایل‌های backup.
- **نگه‌داری فایل‌های backup عملیاتی** (خروجی همین اسکریپت‌ها) یک دغدغهٔ جداست: هدف آن بازیابی سریع در برابر خرابی/حذف تصادفی/فساد داده است، نه بایگانی قانونی بلندمدت. نگه‌داری همهٔ backupهای روزانه به مدت ۷ سال هم غیرضروری است و هم پرهزینه (فضای ذخیره‌سازی).

### پیشنهاد سیاست نگه‌داری backup عملیاتی

| نوع backup | فرکانس | نگه‌داری پیشنهادی |
|---|---|---|
| Daily (روزانه) | هر شب | ۱۴ روز |
| Weekly (هفتگی) | یکشنبه‌ها | ۸ هفته (۲ ماه) |
| Monthly (ماهانه) | اول هر ماه | ۱۲ ماه |

> نکته: اگر نیاز قانونی/انطباقی به نگه‌داری آرشیوی طولانی‌تر (هم‌راستا با ۷ سال `DATA_RETENTION_DAYS`) وجود دارد، آن باید به‌صورت جداگانه — مثلاً با انتقال دوره‌ای backupهای ماهانهٔ منتخب به یک storage آرشیوی ارزان و immutable (WORM) — پیاده‌سازی شود؛ این خارج از محدودهٔ اسکریپت‌های ساده‌ای است که در این تغییر اضافه شدند.

---

## ۴. زمان‌بندی پیشنهادی (cron)

نمونهٔ crontab برای اجرای روزانهٔ هر دو backup در ساعت کم‌ترافیک (مثلاً ۰۲:۳۰ بامداد به وقت سرور):

```cron
# پشتیبان‌گیری روزانهٔ PostgreSQL و MongoDB — ساعت 02:30
30 2 * * * cd /path/to/repo && \
  POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=inescape \
  POSTGRES_USER=inescape_user POSTGRES_PASSWORD=xxx \
  ./scripts/backup_postgres.sh >> /var/log/inescape/backup_postgres.log 2>&1

35 2 * * * cd /path/to/repo && \
  MONGODB_HOST=localhost MONGODB_PORT=27017 MONGODB_DB=inescape_metadata \
  MONGODB_USER=inescape_user MONGODB_PASSWORD=xxx \
  ./scripts/backup_mongo.sh >> /var/log/inescape/backup_mongo.log 2>&1
```

نکات:
- بهتر است رمزهای عبور به‌جای درج مستقیم در crontab، از یک فایل env محافظت‌شده (`chmod 600`) با `source` بارگذاری شوند.
- پاک‌سازی backupهای قدیمی‌تر از سیاست نگه‌داری بخش ۳ (مثلاً با یک job جداگانهٔ `find backups/postgres -mtime +14 -delete`) باید جدا از این job زمان‌بندی شود.
- برای سرورهای Windows معادل با Task Scheduler و اسکریپت‌های `.ps1` قابل انجام است.

---

## ۵. محل ذخیرهٔ فایل‌های backup

اسکریپت‌ها به‌صورت پیش‌فرض داخل مخزن در `backups/postgres/` و `backups/mongo/` می‌نویسند. **این پوشه‌ها نباید در سیستم production روی همان دیسک پایگاه‌داده باقی بمانند** — پیشنهاد می‌شود پس از هر اجرای موفق، فایل‌های تولیدشده به یک محل ذخیره‌سازی خارج از سرور (مثلاً S3/Object Storage یا یک سرور backup جدا) منتقل شوند تا در صورت از دست رفتن کامل سرور اصلی نیز backup در دسترس باشد. این انتقال در اسکریپت‌های فعلی پیاده‌سازی نشده و باید جداگانه اضافه شود.

---

## ۶. رویهٔ تأیید دستی (الزامی پیش از اتکا به این اسکریپت‌ها)

از آنجا که این اسکریپت‌ها هنوز روی یک پایگاه‌دادهٔ واقعی اجرا نشده‌اند، پیش از استفادهٔ عملیاتی حتماً مراحل زیر را یک‌بار به‌صورت دستی (روی یک محیط تست/staging، هرگز روی production) انجام دهید:

1. **آماده‌سازی داده نمونه:** یک نمونه از PostgreSQL و MongoDB با چند رکورد بیمار واقعی/synthetic آماده کنید (می‌توان از `scripts/seed_initial_data.py` یا `scripts/generate_synthetic_data.py` استفاده کرد).
2. **ثبت تعداد رکوردهای مرجع:** پیش از backup، تعداد ردیف‌های چند جدول کلیدی را ثبت کنید:
   ```sql
   SELECT count(*) FROM patients;
   SELECT count(*) FROM clinical_data;
   SELECT count(*) FROM treatment_data;
   ```
   و برای Mongo:
   ```js
   db.getCollectionNames().forEach(c => print(c, db[c].countDocuments()))
   ```
3. **اجرای backup:** `./scripts/backup_postgres.sh` و `./scripts/backup_mongo.sh` را اجرا کنید و مطمئن شوید فایل/پوشهٔ خروجی ساخته شده و حجم آن غیرصفر است.
4. **ساخت پایگاه‌دادهٔ scratch (آزمایشی) جدا:** یک دیتابیس PostgreSQL جدید و خالی (مثلاً `inescape_restore_test`) و یک نام‌دیتابیس Mongo جدید (مثلاً `inescape_metadata_restore_test`) بسازید. **هرگز backup را مستقیماً روی دیتابیس production بازیابی نکنید مگر در یک رویداد بازیابی واقعی و تأییدشده.**
5. **بازیابی روی scratch:**
   ```bash
   POSTGRES_DB=inescape_restore_test ./scripts/restore_postgres.sh backups/postgres/<file>.dump --yes
   MONGODB_DB=inescape_metadata_restore_test ./scripts/restore_mongo.sh backups/mongo/<timestamp> --yes
   ```
6. **مقایسهٔ تعداد رکوردها:** همان کوئری‌های شمارش مرحلهٔ ۲ را روی دیتابیس scratch اجرا کنید و مطمئن شوید اعداد دقیقاً با مقادیر مرجع یکسان است.
7. **بررسی نمونه‌ای محتوا (spot-check):** چند رکورد بیمار خاص را با `patient_id` مشخص در دیتابیس اصلی و scratch مقایسه کنید تا از صحت محتوا (نه فقط تعداد) مطمئن شوید.
8. **پاک‌سازی:** دیتابیس‌های scratch را پس از تأیید حذف کنید.
9. **ثبت نتیجه:** نتیجهٔ این تست (تاریخ، نسخهٔ اسکریپت، موفق/ناموفق) را در یک لاگ تیمی یا این سند ثبت کنید تا مرجع بعدی مشخص باشد که این ابزارها حداقل یک‌بار تأیید شده‌اند.

تا زمانی که مراحل بالا حداقل یک‌بار با موفقیت کامل انجام نشده، این اسکریپت‌ها باید «تأییدنشده» در نظر گرفته شوند و نباید تنها راه بازیابی فاجعه (disaster recovery) این پروژه باشند.
