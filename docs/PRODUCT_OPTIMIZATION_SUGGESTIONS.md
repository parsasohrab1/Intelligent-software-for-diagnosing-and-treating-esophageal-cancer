# پیشنهادات بهینه‌سازی محصول INEsCape

این سند پیشنهادات بهینه‌سازی در حوزه‌های **عملکرد، مقیاس‌پذیری، UX/UI، امنیت و زیرساخت** را برای محصول INEsCape (تشخیص و درمان سرطان مری) گردآوری کرده است.

---

## ۱. بهینه‌سازی Backend و API

### ۱.۱ کش و داده‌یابی

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **یکپارچه‌سازی کش چندسطحی در API** | استفاده از `advanced_cache.get_cache_manager()` (L1+L2+compression) در endpointهای پرتردد به‌جای فقط Redis | بالا | انجام شد: health_check و endpointهای پرتردد از `get_cache_manager()` استفاده می‌کنند |
| **API آمار کش و سلامت ایندکس** | Endpointهای `/api/v1/admin/cache/stats` و `/api/v1/admin/database/index-health` برای مانیتورینگ | متوسط | انجام شد: router ادمین اضافه شد |
| **Read Replicas** | برای گزارش‌ها و داشبورد از replica خواندن؛ تنظیم `DATABASE_READ_REPLICA_URL` در config | متوسط | پشتیبانی وجود دارد: `get_read_db()` و `SessionLocalRead`؛ dashboard و dashboard/stats از replica استفاده می‌کنند |
| **Pagination یکنواخت** | استاندارد کردن cursor/offset و حداکثر اندازه صفحه در همهٔ لیست‌ها | متوسط | انجام شد: `app.core.pagination` با `DEFAULT_PAGE_SIZE=20` و `MAX_PAGE_SIZE=100`؛ patients و imaging به‌روز شدند |

### ۱.۲ پردازش ناهمزمان و صف‌ها

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Kafka/RabbitMQ برای پردازش async** | صف برای: پردازش تصاویر MRI، اعلان‌های real-time، همگام‌سازی داده بین سرویس‌ها | بالا | زیرساخت وجود دارد: `app.services.messaging.message_queue` (Kafka/RabbitMQ)؛ MLOps از آن استفاده می‌کند؛ job نوع `mri_processing` می‌تواند به صف `imaging_data` publish کند |
| **Celery یا Background Tasks** | برای: ML model inference سنگین، گزارش‌گیری‌های سنگین، ارسال notificationها؛ جلوگیری از block شدن API | بالا | FastAPI BackgroundTasks در synthetic-data و data-collection؛ سرویس job با پس‌زمینه برای report/inference/mri_processing اضافه شد |
| **Job status و نتیجه** | Endpoint برای وضعیت job (pending/running/done) و دریافت نتیجهٔ نهایی (مثلاً `/jobs/{id}`) | متوسط | انجام شد: `POST /api/v1/jobs` و `GET /api/v1/jobs/{job_id}`؛ وضعیت pending/running/done/failed و نتیجه در `app.services.job_store` |

### ۱.۳ دیتابیس و کوئری

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Partial indexes (PostgreSQL)** | ایندکس‌های شرطی از طریق `database_indexes.create_all_indexes()` در startup؛ اطمینان از اجرا در production | بالا | انجام شد: `main.py` در startup فراخوانی `initialize_indexes()` می‌کند |
| **Eager loading / جلوگیری از N+1** | استفاده از `joinedload`/`selectinload` در کوئری‌های مربوط به patient + imaging + clinical | متوسط | انجام شد: endpoint `GET /patients/{id}/combined` با `selectinload(Patient.imaging_data, ...)` یک کوئری برای patient + روابط |
| **Query timeout** | تنظیم timeout برای کوئری‌های سنگین تا از hang شدن connection جلوگیری شود | پایین | انجام شد: `QUERY_TIMEOUT_SECONDS` در config؛ در `get_db()` و `get_read_db()` برای PostgreSQL مقدار `statement_timeout` تنظیم می‌شود |
| **آمار استفاده از ایندکس** | استفاده از `database_indexes.analyze_index_usage()` در محیط production و حذف ایندکس‌های بی‌استفاده | پایین | در دسترس: خروجی `GET /api/v1/admin/database/index-health` شامل `usage_analysis` (PostgreSQL) برای بررسی ایندکس‌های بی‌استفاده |

### ۱.۴ ML و Inference

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Model caching / warm-up** | بارگذاری مدل‌های پرکاربرد در حافظه هنگام startup و نگه‌داری در cache | بالا | انجام شد: کش درون‌حافظهٔ مدل‌های لودشده (`_loaded_models`)؛ `warm_up_best_model()` در startup؛ `/predict` از همان کش استفاده می‌کند |
| **Inference در worker** | انتقال inference سنگین به Celery/worker تا API سبک بماند | بالا | مسیر job وجود دارد: `POST /api/v1/jobs` با `type: "inference"` و polling با `GET /api/v1/jobs/{id}`؛ inference سنگین را می‌توان به job داد |
| **Batching برای inference** | در صورت امکان، پردازش دسته‌ای تصاویر برای بهره‌وری بهتر GPU/CPU | متوسط | انجام شد: `/predict/batch` با یک بار لود مدل و `model.predict(feature_df)` روی دسته؛ پشتیبانی از `features_list` یا `data_path` (CSV) |
| **ONNX / TensorRT** | صادر کردن مدل به ONNX یا بهینه‌سازی با TensorRT برای inference سریع‌تر | متوسط | فقط stub: در `edge_computing.py` ارجاع به TensorRT/ONNX؛ پیاده‌سازی واقعی صادر/بهینه‌سازی مدل انجام نشده |

---

## ۲. بهینه‌سازی Frontend

### ۲.۱ عملکرد و Data Fetching

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **React Query یا SWR** | کش سمت کلاینت، retry، revalidation و کاهش درخواست‌های تکراری | بالا | انجام شد: React Query در main؛ Dashboard با useQuery برای stats؛ Patients با useQuery برای list و invalidateQueries پس از generate |
| **Code splitting و Lazy loading** | `React.lazy` و `Suspense` برای routeها و کامپوننت‌های سنگین؛ کاهش bundle اولیه | بالا | انجام شد: همهٔ صفحه‌ها با `React.lazy` و `Suspense` با fallback در `App.tsx` |
| **Virtual scrolling** | برای لیست‌های طولانی (بیماران، مدل‌ها، تصاویر) با کتابخانه‌ای مثل react-window یا TanStack Virtual | بالا | انجام شد: `@tanstack/react-virtual` در صفحهٔ Patients؛ برای لیست >۸۰ مورد فقط ردیف‌های visible رندر می‌شوند |
| **Image optimization** | استفاده از WebP، lazy loading تصاویر، اندازه‌های مناسب و در صورت امکان CDN | متوسط | انجام شد: `loading="lazy"` برای تصاویر MRI در MRIDashboard؛ WebP/CDN در backend سروینگ قابل اضافه‌سازی است |

### ۲.۲ UX/UI

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Dark mode** | در roadmap است؛ یکپارچه با theme و ذخیره ترجیح کاربر | متوسط | theme در `theme.ts` وجود دارد؛ toggle و ذخیرهٔ ترجیح کاربر پیاده نشده |
| **Progressive Web App (PWA)** | Service worker، نصب روی دستگاه، بهبود تجربه موبایل | متوسط | پیاده‌سازی نشده (بدون manifest یا service worker) |
| **Offline capability** | مشاهده داده‌های کش‌شده و وضعیت «offline» با راهنمای کاربر | متوسط | پیاده‌سازی نشده |
| **Accessibility (WCAG 2.1)** | contrast، focus، نقش‌های ARIA، کیبورد، و تست با screen reader | بالا (برای محصول پزشکی) | MUI تا حدی دسترسی‌پذیری فراهم می‌کند؛ بررسی رسمی WCAG و ARIA انجام نشده |
| **Skeleton / Loading states** | جایگزینی اسپینر با skeleton برای درک بهتر ساختار صفحه | پایین | در بیشتر صفحات از CircularProgress استفاده می‌شود؛ skeleton استفاده نشده |
| **Error boundaries و پیام‌های خطا** | پیام‌های قابل فهم و راهنمای رفع مشکل برای کاربر | متوسط | `ErrorBoundary` در `App.tsx` برای route CDS استفاده شده؛ گسترش به بقیه و پیام‌های راهنما قابل اضافه‌سازی است |

### ۲.۳ معماری و نگهداری

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **ساختار state سراسری** | در صورت رشد، استفاده از Zustand/Redux برای state مشترک و جلوگیری از prop drilling | پایین | Zustand در وابستگی‌ها هست؛ state سراسری مشترک استفاده نشده (فعلاً state محلی و React Query) |
| **TypeScript strict** | فعال‌سازی strict mode و کاهش `any` برای قابلیت نگهداری بهتر | متوسط | انجام شد: در `tsconfig.json` مقدار `strict: true` و `noUnusedLocals`/`noUnusedParameters` فعال است |

---

## ۳. امنیت و انطباق

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Rate limiting دقیق‌تر** | محدودیت بر اساس endpoint و نقش کاربر (مثلاً محدودیت بیشتر برای export و inference) | بالا | انجام شد: `RateLimitMiddleware` با محدودیت per-endpoint؛ محدودیت بر اساس نقش کاربر قابل اضافه‌سازی است |
| **Audit log برای دسترسی به داده حساس** | ثبت دسترسی به پرونده بیمار و تصاویر برای HIPAA/GDPR | بالا | انجام شد: `audit_logger` و endpointهای `/api/v1/audit`؛ دسترسی بیمار در dependencies ثبت می‌شود |
| **Input validation و sanitization** | اعتبارسنجی و پاکسازی ورودی در همهٔ endpointهای عمومی و مدیریت فایل | بالا | Pydantic برای validation؛ sanitization صریح در endpointهای حساس قابل بازبینی است |
| **Security headers** | HSTS، CSP، X-Frame-Options و غیره از طریق middleware (تا حدی وجود دارد؛ بازبینی لیست) | متوسط | انجام شد: `security_headers.apply_security_headers` در middleware؛ HSTS، CSP، X-Frame-Options در config |
| **رمزنگاری داده در حالت استراحت** | برای فیلدهای حساس در DB و فایل‌های ذخیره‌شده (با توجه به USE_AES256_ENCRYPTION) | متوسط | `USE_AES256_ENCRYPTION` در config؛ پیاده‌سازی واقعی در لایهٔ ذخیره‌سازی قابل گسترش است |

---

## ۴. زیرساخت و عملیات

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **Health check تفکیک‌شده** | جدا کردن liveness (سریع) از readiness (وابسته به DB/Redis/MQ) برای Kubernetes | متوسط | انجام شد: `/api/v1/health/liveness` (سریع) و `/api/v1/health/readiness` (وابسته به DB/Redis/Mongo) در `health.py` |
| **Distributed tracing** | OpenTelemetry یا Jaeger برای ردیابی درخواست در چند سرویس | متوسط | پیاده‌سازی نشده |
| **Structured logging** | JSON log با correlation id برای جستجو و تحلیل در محیط production | متوسط | لاگ استاندارد Python؛ JSON و correlation id پیاده نشده |
| **محدودیت منابع در K8s** | تعریف request/limit برای CPU و memory برای API و workerها | متوسط | در repo تعریف نشده؛ در k8s/ قابل اضافه‌سازی است |
| **Backup و بازیابی** | استراتژی backup برای PostgreSQL و MongoDB و تست بازیابی | بالا | در repo پیاده نشده؛ استراتژی و اسکریپت‌ها قابل مستندسازی است |
| **Feature flags** | برای rollout تدریجی قابلیت‌های جدید و A/B تست (با توجه به AB_TESTING_ENABLED) | پایین | `AB_TESTING_ENABLED` در config؛ سرویس A/B در mlops وجود دارد |

---

## ۵. تجربه بالینی و دقت

| پیشنهاد | توضیح | اولویت | وضعیت فعلی |
|---------|--------|--------|------------|
| **توضیح خروجی مدل (XAI)** | نمایش دلیل پیشنهاد/تشخیص برای پزشک (بخش xai وجود دارد؛ یکپارچگی در UI) | بالا | انجام شد: endpointهای xai و `SHAPVisualization` در CDS؛ یکپارچگی در UI برای CDS وجود دارد |
| **Versioning مدل و نتیجه** | ذخیره نسخه مدل استفاده‌شده در هر پیش‌بینی برای قابلیت ردیابی و ممیزی | متوسط | Model registry و metadata مدل وجود دارد؛ ذخیرهٔ نسخه در هر پیش‌بینی در monitoring قابل گسترش است |
| **هشدار برای داده ناقص** | وقتی ورودی برای CDS ناقص است، نمایش هشدار واضح به کاربر | متوسط | در CDS و backend قابل اضافه‌سازی است |
| **محدودیت زمانی برای پیش‌بینی real-time** | رعایت REALTIME_MAX_LATENCY_MS و fallback در صورت تأخیر | متوسط | `REALTIME_MAX_LATENCY_MS` در config؛ رعایت و fallback در realtime endpoint قابل اضافه‌سازی است |

---

## ۶. اولویت‌بندی پیشنهادی (خلاصه)

### فاز ۱ (۱–۲ ماه) – عملکرد و پایداری
1. یکپارچه‌سازی کش چندسطحی در APIهای پرتردد  
2. Celery/Background Tasks برای inference و گزارش‌گیری سنگین  
3. React Query/SWR و lazy loading در frontend  
4. Virtual scrolling برای لیست‌های طولانی  
5. تست‌های واحد و یکپارچگی برای cache warming و ایندکس‌ها  

### فاز ۲ (۲–۴ ماه) – صف و real-time
1. استفاده از Kafka/RabbitMQ برای پردازش async تصاویر و notification  
2. API وضعیت job و نتیجه  
3. Read replicas و endpoint سلامت ایندکس/کش  
4. بهبود Accessibility (WCAG 2.1) و Dark mode  

### فاز ۳ (۴–۶ ماه) – مقیاس و تجربه
1. PWA و قابلیت offline  
2. Distributed tracing و structured logging  
3. بهینه‌سازی مدل (ONNX/TensorRT) و batching  
4. Backup و بازیابی و سخت‌گیری امنیتی (audit، rate limit، validation)  

---

## ۷. ارجاع به اسناد مرتبط

- **UPDATE_SUGGESTIONS.md** – پیشنهادات به‌روزرسانی فنی و چک‌لیست فایل‌ها  
- **PERFORMANCE_IMPROVEMENTS.md** – کارهای انجام‌شده در زمینه کش و connection pool  
- **DEVELOPMENT_ROADMAP.md** – نقشه راه توسعه  
- **NEXT_STEPS.md** – اولویت‌های کوتاه‌مدت  

با اجرای تدریجی این پیشنهادات، عملکرد، مقیاس‌پذیری و تجربهٔ کاربری محصول INEsCape به‌طور قابل توجهی بهبود خواهد یافت.
