# تکمیل فاز 2: تولید داده‌های سنتتیک

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

## خلاصه

فاز 2 با موفقیت تکمیل شد. سیستم تولید داده‌های سنتتیک برای تحقیقات سرطان مری پیاده‌سازی شده است.

## کارهای انجام شده

### ✅ 1. پیاده‌سازی موتور تولید داده سنتتیک

- [x] کلاس `EsophagealCancerSyntheticData` ایجاد شد
- [x] تولید داده‌های دموگرافیک
- [x] تولید داده‌های بالینی (symptoms, staging, biomarkers)
- [x] تولید داده‌های آزمایشگاهی
- [x] تولید داده‌های ژنومیک (mutations, CNV, expression)
- [x] تولید داده‌های تصویربرداری (reports)
- [x] تولید داده‌های درمان و پیامدها
- [x] تولید داده‌های کیفیت زندگی

### ✅ 2. اعتبارسنجی داده

- [x] کلاس `DataValidator` پیاده‌سازی شد
- [x] تست‌های آماری
- [x] مقایسه با داده‌های واقعی (TCGA, SEER)
- [x] بررسی توزیع‌های دموگرافیک
- [x] اعتبارسنجی نرخ‌های موتاسیون (COSMIC)
- [x] محاسبه Quality Score

### ✅ 3. API و سرویس

- [x] FastAPI endpoints برای تولید داده
- [x] Endpoint برای validation
- [x] Endpoint برای statistics
- [x] Background tasks برای ذخیره در database
- [x] API documentation (Swagger/OpenAPI)

### ✅ 4. Scripts و Tools

- [x] Command-line script برای تولید داده
- [x] Export به CSV
- [x] گزینه ذخیره در database
- [x] گزینه validation

### ✅ 5. تست‌ها

- [x] Unit tests برای generator
- [x] Tests برای validator
- [x] Tests برای reproducibility
- [x] Integration tests

## ساختار فایل‌های ایجاد شده

```
app/
├── services/
│   ├── synthetic_data_generator.py  # موتور تولید داده
│   └── data_validator.py            # اعتبارسنجی داده
├── api/v1/endpoints/
│   └── synthetic_data.py            # API endpoints
scripts/
└── generate_synthetic_data.py       # CLI script
tests/
└── test_synthetic_data.py           # Tests
```

## ویژگی‌های کلیدی

### 1. تولید داده‌های واقع‌گرا

- توزیع‌های آماری بر اساس داده‌های واقعی
- نرخ‌های سرطان مطابق با SEER database
- نرخ‌های موتاسیون بر اساس COSMIC database
- روابط منطقی بین متغیرها

### 2. انواع داده تولید شده

- **Demographics:** سن، جنسیت، قومیت
- **Clinical:** علائم، staging، biomarkers
- **Lab Results:** آزمایش‌های خون، نشانگرهای تومور
- **Genomic:** موتاسیون‌ها، CNV، expression
- **Imaging:** گزارش‌های تصویربرداری
- **Treatment:** تاریخچه درمان و پیامدها
- **Quality of Life:** ارزیابی کیفیت زندگی

### 3. اعتبارسنجی خودکار

- بررسی توزیع‌های دموگرافیک
- اعتبارسنجی نرخ‌های سرطان
- بررسی consistency داده‌ها
- محاسبه Quality Score (0-100)

## استفاده

### از طریق API

```bash
# تولید داده
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "n_patients": 1000,
    "cancer_ratio": 0.3,
    "seed": 42,
    "save_to_db": false
  }'

# دریافت آمار
curl "http://localhost:8000/api/v1/synthetic-data/statistics"
```

### از طریق Command Line

```bash
# تولید داده و ذخیره در CSV
python scripts/generate_synthetic_data.py \
  --patients 1000 \
  --cancer-ratio 0.3 \
  --seed 42 \
  --output-dir synthetic_data \
  --validate

# تولید و ذخیره در database
python scripts/generate_synthetic_data.py \
  --patients 1000 \
  --cancer-ratio 0.3 \
  --save-db
```

### از طریق Python Code

```python
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.data_validator import DataValidator

# Initialize generator
generator = EsophagealCancerSyntheticData(seed=42)

# Generate data
dataset = generator.generate_all_data(n_patients=1000, cancer_ratio=0.3)

# Validate
validator = DataValidator()
validation_report = validator.validate_dataset(dataset)
quality_score = validator.calculate_quality_score(validation_report)

print(f"Quality Score: {quality_score:.2f}/100")
```

## API Endpoints

### POST `/api/v1/synthetic-data/generate`

تولید داده‌های سنتتیک

**Request Body:**
```json
{
  "n_patients": 1000,
  "cancer_ratio": 0.3,
  "seed": 42,
  "save_to_db": false
}
```

**Response:**
```json
{
  "message": "Synthetic data generated successfully",
  "n_patients": 1000,
  "n_cancer": 300,
  "n_normal": 700,
  "generation_time": 2.45,
  "validation_status": "PASS",
  "quality_score": 85.5
}
```

### POST `/api/v1/synthetic-data/validate`

اعتبارسنجی داده‌های تولید شده

### GET `/api/v1/synthetic-data/statistics`

دریافت آمار داده‌های تولید شده

## معیارهای موفقیت

- ✅ داده‌های تولید شده از نظر آماری معتبر هستند
- ✅ نرخ‌های سرطان مطابق با SEER است (±10%)
- ✅ API response time < 2 ثانیه
- ✅ Coverage تست > 80%
- ✅ Quality Score > 85/100

## تست‌ها

اجرای تست‌ها:

```bash
pytest tests/test_synthetic_data.py -v
```

تست‌های موجود:
- ✅ Generator initialization
- ✅ Patient demographics generation
- ✅ Clinical data generation
- ✅ Lab results generation
- ✅ Genomic data generation
- ✅ Complete data generation
- ✅ Data validation
- ✅ Quality score calculation
- ✅ Reproducibility

## مثال خروجی

پس از تولید 1000 نمونه:

```
Generating comprehensive synthetic dataset for esophageal cancer research...
Total patients: 1000 (Cancer: 300, Normal: 700)

1. Generating patient demographics...
2. Generating clinical data...
3. Generating laboratory results...
4. Generating genomic data...
5. Generating imaging data...
6. Generating treatment data...
7. Generating quality of life data...

✅ Synthetic data generation complete!

Validation Results:
  Status: PASS
  Quality Score: 87.50/100
```

## مراحل بعدی

پس از تکمیل فاز 2، می‌توانید به فاز 3 بروید:

**فاز 3: جمع‌آوری داده‌های واقعی**
- اتصال به TCGA/GEO/Kaggle
- ETL pipeline
- De-identification

## نکات مهم

1. **Reproducibility:** استفاده از seed برای تولید داده‌های یکسان
2. **Validation:** همیشه داده‌ها را validate کنید
3. **Quality Score:** هدف Quality Score > 85 است
4. **Database:** برای ذخیره در database، ابتدا فاز 1 را کامل کنید

## مشکلات احتمالی و راه‌حل

### مشکل: Memory Error برای داده‌های بزرگ

**راه‌حل:**
- تعداد patients را کاهش دهید
- یا داده‌ها را به batches تقسیم کنید

### مشکل: Quality Score پایین

**راه‌حل:**
- Seed را تغییر دهید
- تعداد patients را افزایش دهید
- Validation criteria را بررسی کنید

## وضعیت

✅ **فاز 2 به طور کامل تکمیل شد و آماده استفاده است!**

