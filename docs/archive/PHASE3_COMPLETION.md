# تکمیل فاز 3: جمع‌آوری داده‌های واقعی

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

## خلاصه

فاز 3 با موفقیت تکمیل شد. سیستم جمع‌آوری داده‌های واقعی از منابع خارجی پیاده‌سازی شده است.

## کارهای انجام شده

### ✅ 1. اتصال به Data Repositories

- [x] **TCGA Collector** - اتصال به GDC API
  - کشف datasets
  - دانلود داده‌های بالینی
  - اعتبارسنجی داده

- [x] **GEO Collector** - اتصال به NCBI API
  - جستجو در Gene Expression Omnibus
  - دانلود datasets
  - پردازش metadata

- [x] **Kaggle Collector** - اتصال به Kaggle API
  - جستجو در datasets
  - دانلود datasets
  - مدیریت credentials

### ✅ 2. ETL Pipeline

- [x] **Extract Layer** - استخراج داده از منابع
- [x] **Transform Layer** - تبدیل و normalization
- [x] **Load Layer** - ذخیره در storage
- [x] مدیریت errors و retries
- [x] Batch processing

### ✅ 3. De-identification

- [x] کلاس `DataDeidentifier` پیاده‌سازی شد
- [x] حذف direct identifiers
- [x] Generalization quasi-identifiers
- [x] افزودن noise به dates
- [x] تولید hash identifiers
- [x] اعتبارسنجی de-identification

### ✅ 4. Quality Control

- [x] کلاس `DataQualityAssessor` پیاده‌سازی شد
- [x] بررسی completeness
- [x] بررسی consistency
- [x] بررسی accuracy
- [x] بررسی timeliness
- [x] بررسی relevance
- [x] محاسبه overall quality score

### ✅ 5. Metadata Management

- [x] کلاس `MetadataManager` پیاده‌سازی شد
- [x] ذخیره metadata در MongoDB
- [x] جستجو و فیلتر metadata
- [x] آمار و گزارش‌گیری

## ساختار فایل‌های ایجاد شده

```
app/
├── services/
│   ├── data_collectors/
│   │   ├── base_collector.py      # Base class
│   │   ├── tcga_collector.py      # TCGA collector
│   │   ├── geo_collector.py       # GEO collector
│   │   └── kaggle_collector.py    # Kaggle collector
│   ├── data_deidentifier.py       # De-identification
│   ├── etl_pipeline.py            # ETL pipeline
│   ├── data_quality.py            # Quality assessment
│   └── metadata_manager.py        # Metadata management
├── api/v1/endpoints/
│   └── data_collection.py         # API endpoints
scripts/
└── collect_real_data.py            # CLI script
```

## ویژگی‌های کلیدی

### 1. اتصال به منابع متعدد

- **TCGA:** داده‌های ژنومیک و بالینی سرطان
- **GEO:** داده‌های expression و microarray
- **Kaggle:** datasets عمومی

### 2. ETL Pipeline کامل

- Extract از منابع مختلف
- Transform به format یکپارچه
- Load به storage (CSV, Parquet)
- Error handling و retry logic

### 3. De-identification پیشرفته

- حذف کامل direct identifiers
- Generalization برای privacy
- Hash identifiers برای tracking
- Verification system

### 4. Quality Assessment

- 5 معیار کیفیت
- Overall quality score
- گزارش‌های تفصیلی

### 5. Metadata Management

- ذخیره در MongoDB
- جستجوی پیشرفته
- آمار و گزارش‌گیری

## استفاده

### از طریق API

```bash
# جمع‌آوری داده از TCGA
curl -X POST "http://localhost:8000/api/v1/data-collection/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "tcga",
    "query": "esophageal cancer",
    "auto_download": false
  }'

# دریافت metadata
curl "http://localhost:8000/api/v1/data-collection/metadata?source=tcga"

# ارزیابی کیفیت
curl -X POST "http://localhost:8000/api/v1/data-collection/quality-assessment" \
  -H "Content-Type: application/json" \
  -d '{"dataset_path": "collected_data/tcga/dataset.csv"}'
```

### از طریق Command Line

```bash
# جمع‌آوری از TCGA
python scripts/collect_real_data.py \
  --source tcga \
  --query "esophageal cancer" \
  --save-metadata

# جمع‌آوری از GEO
python scripts/collect_real_data.py \
  --source geo \
  --query "esophageal cancer" \
  --auto-download

# جمع‌آوری از Kaggle
python scripts/collect_real_data.py \
  --source kaggle \
  --query "cancer dataset" \
  --dataset-ids dataset1 dataset2
```

### از طریق Python Code

```python
from app.services.etl_pipeline import ETLPipeline
from app.services.data_quality import DataQualityAssessor

# Initialize pipeline
pipeline = ETLPipeline()

# Run ETL
result = pipeline.run_pipeline(
    source="tcga",
    query="esophageal cancer",
    auto_download=False
)

# Assess quality
assessor = DataQualityAssessor()
quality_report = assessor.assess_quality(data)
```

## API Endpoints

### POST `/api/v1/data-collection/collect`

جمع‌آوری داده از منابع خارجی

**Request Body:**
```json
{
  "source": "tcga",
  "query": "esophageal cancer",
  "dataset_ids": null,
  "auto_download": false
}
```

**Response:**
```json
{
  "message": "Data collection from tcga completed",
  "source": "tcga",
  "datasets_discovered": 150,
  "datasets_processed": 10,
  "datasets_failed": 0,
  "output_files": ["collected_data/tcga/dataset1.csv"]
}
```

### POST `/api/v1/data-collection/quality-assessment`

ارزیابی کیفیت داده

### GET `/api/v1/data-collection/metadata`

دریافت metadata

### GET `/api/v1/data-collection/metadata/statistics`

دریافت آمار metadata

### POST `/api/v1/data-collection/deidentify`

De-identify کردن داده

## تنظیمات API Keys

برای استفاده از collectors، باید API keys را در `.env` تنظیم کنید:

```env
TCGA_API_KEY=your_tcga_api_key
GEO_API_KEY=your_geo_api_key
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key
```

**نکته:** برای TCGA و GEO معمولاً API key لازم نیست، اما برای rate limiting بهتر است.

## معیارهای موفقیت

- ✅ نرخ موفقیت جمع‌آوری داده ≥ 95%
- ✅ تمام داده‌ها de-identified شده باشند
- ✅ Quality score > 85/100
- ✅ Metadata برای ≥ 95% datasets موجود باشد

## تست‌ها

اجرای تست‌ها:

```bash
pytest tests/test_data_collection.py -v
```

## مثال خروجی

پس از جمع‌آوری از TCGA:

```
==================================================
Running ETL Pipeline for tcga
==================================================

Extracting data from tcga...
Found 150 datasets from tcga

Processing dataset: TCGA-ESCA-001...
Dataset TCGA-ESCA-001 downloaded successfully

==================================================
ETL Pipeline completed for tcga
Discovered: 150
Processed: 10
Failed: 0
==================================================
```

## مراحل بعدی

پس از تکمیل فاز 3، می‌توانید به فاز 4 بروید:

**فاز 4: یکپارچه‌سازی و پردازش داده**
- یکپارچه‌سازی داده‌های سنتتیک و واقعی
- Feature Engineering
- آماده‌سازی برای ML

## نکات مهم

1. **API Keys:** برای استفاده کامل، API keys را تنظیم کنید
2. **Rate Limiting:** GEO و TCGA rate limits دارند
3. **Storage:** داده‌های جمع‌آوری شده در `collected_data/` ذخیره می‌شوند
4. **De-identification:** همیشه داده‌ها را de-identify کنید قبل از استفاده

## مشکلات احتمالی و راه‌حل

### مشکل: API Key Invalid

**راه‌حل:**
- بررسی کنید که API keys در `.env` درست تنظیم شده‌اند
- برای Kaggle، credentials را در `~/.kaggle/kaggle.json` قرار دهید

### مشکل: Rate Limiting

**راه‌حل:**
- بین requests تاخیر اضافه کنید
- از API keys استفاده کنید (rate limit بالاتر)

### مشکل: Download Failed

**راه‌حل:**
- اتصال اینترنت را بررسی کنید
- فایل‌های بزرگ ممکن است timeout شوند

## وضعیت

✅ **فاز 3 به طور کامل تکمیل شد و آماده استفاده است!**

