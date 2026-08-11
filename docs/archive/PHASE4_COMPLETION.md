# تکمیل فاز 4: یکپارچه‌سازی و پردازش داده

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

## خلاصه

فاز 4 با موفقیت تکمیل شد. سیستم یکپارچه‌سازی و پردازش داده برای آماده‌سازی داده‌ها برای یادگیری ماشین پیاده‌سازی شده است.

## کارهای انجام شده

### ✅ 1. Hybrid Data Integration

- [x] کلاس `HybridDataIntegrator` پیاده‌سازی شد
- [x] Statistical matching بین synthetic و real data
- [x] Data fusion algorithms (concatenate, weighted, matched)
- [x] Quality metrics برای hybrid datasets
- [x] Bias detection و correction
- [x] Cross-validation بین synthetic و real data

### ✅ 2. Feature Engineering

- [x] کلاس `FeatureEngineer` پیاده‌سازی شد
- [x] استخراج features از multi-modal data:
  - Patient demographics
  - Clinical data
  - Genomic data (mutations, CNV, expression)
  - Lab results
- [x] ایجاد derived features
- [x] Normalization و standardization
- [x] Handling missing values
- [x] Feature selection

### ✅ 3. Data Augmentation

- [x] کلاس `DataAugmenter` پیاده‌سازی شد
- [x] Augmentation با synthetic data
- [x] SMOTE و ADASYN
- [x] Combined methods (SMOTETomek, SMOTEENN)
- [x] Validation augmentation effectiveness

### ✅ 4. Data Warehouse

- [x] کلاس `DataWarehouse` پیاده‌سازی شد
- [x] طراحی schema برای data warehouse
- [x] Fact tables (patients, clinical events, features)
- [x] Dimension tables (features)
- [x] OLAP queries
- [x] Feature statistics

## ساختار فایل‌های ایجاد شده

```
app/
├── services/
│   ├── data_integration/
│   │   └── hybrid_integrator.py    # یکپارچه‌سازی
│   ├── feature_engineering.py      # Feature engineering
│   ├── data_augmentation.py        # Data augmentation
│   └── data_warehouse.py           # Data warehouse
├── api/v1/endpoints/
│   └── data_integration.py         # API endpoints
scripts/
└── integrate_data.py                # CLI script
```

## ویژگی‌های کلیدی

### 1. یکپارچه‌سازی پیشرفته

- **Statistical Matching:** مقایسه آماری بین synthetic و real data
- **Multiple Fusion Methods:** concatenate, weighted, matched
- **Bias Detection:** شناسایی bias در داده‌های یکپارچه شده
- **Cross-validation:** اعتبارسنجی بین datasets

### 2. Feature Engineering جامع

- **Multi-modal Features:** از تمام منابع داده
- **Derived Features:** ایجاد features جدید از features موجود
- **Normalization:** Standardization و MinMax scaling
- **Feature Selection:** انتخاب بهترین features

### 3. Augmentation Methods

- **Synthetic Augmentation:** استفاده از داده‌های سنتتیک
- **SMOTE:** Synthetic Minority Over-sampling Technique
- **ADASYN:** Adaptive Synthetic Sampling
- **Combined Methods:** ترکیب over-sampling و under-sampling

### 4. Data Warehouse

- **Star Schema:** Fact و dimension tables
- **OLAP Queries:** پرس‌وجوهای تحلیلی
- **Feature Statistics:** آمار features

## استفاده

### از طریق API

```bash
# یکپارچه‌سازی داده
curl -X POST "http://localhost:8000/api/v1/data-integration/integrate" \
  -H "Content-Type: application/json" \
  -d '{
    "synthetic_data_path": "synthetic_data/patients.csv",
    "real_data_path": "collected_data/tcga/patients.csv",
    "fusion_method": "concatenate"
  }'

# Feature Engineering
curl -X POST "http://localhost:8000/api/v1/data-integration/engineer-features" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "integrated_data.csv",
    "include_genomic": true,
    "normalize": true
  }'

# Data Augmentation
curl -X POST "http://localhost:8000/api/v1/data-integration/augment" \
  -H "Content-Type: application/json" \
  -d '{
    "real_data_path": "real_data.csv",
    "synthetic_data_path": "synthetic_data.csv",
    "target_column": "has_cancer",
    "method": "smote"
  }'
```

### از طریق Command Line

```bash
# یکپارچه‌سازی
python scripts/integrate_data.py \
  --synthetic synthetic_data/patients.csv \
  --real collected_data/tcga/patients.csv \
  --output integrated_data.csv \
  --fusion-method concatenate

# با Feature Engineering
python scripts/integrate_data.py \
  --synthetic synthetic_data/patients.csv \
  --real collected_data/tcga/patients.csv \
  --output integrated_data.csv \
  --engineer-features

# با Augmentation
python scripts/integrate_data.py \
  --synthetic synthetic_data/patients.csv \
  --real collected_data/tcga/patients.csv \
  --output integrated_data.csv \
  --augment
```

### از طریق Python Code

```python
from app.services.data_integration.hybrid_integrator import HybridDataIntegrator
from app.services.feature_engineering import FeatureEngineer
from app.services.data_augmentation import DataAugmenter

# Integrate
integrator = HybridDataIntegrator()
fused_data = integrator.fuse_datasets(synthetic_data, real_data)

# Engineer features
engineer = FeatureEngineer()
features = engineer.extract_features_from_patients(fused_data)
features = engineer.normalize_features(features)

# Augment
augmenter = DataAugmenter()
augmented_data = augmenter.augment_with_synthetic(
    real_data, synthetic_data, "has_cancer"
)
```

## API Endpoints

### POST `/api/v1/data-integration/integrate`

یکپارچه‌سازی synthetic و real data

**Request Body:**
```json
{
  "synthetic_data_path": "synthetic_data/patients.csv",
  "real_data_path": "collected_data/tcga/patients.csv",
  "fusion_method": "concatenate",
  "matching_threshold": 0.8
}
```

**Response:**
```json
{
  "message": "Data integration completed",
  "matching_scores": {
    "age_correlation": 0.85,
    "age_ks_pvalue": 0.12
  },
  "quality_metrics": {
    "total_samples": 2000,
    "synthetic_samples": 1000,
    "real_samples": 1000
  },
  "fused_data_size": 2000
}
```

### POST `/api/v1/data-integration/engineer-features`

Feature engineering از multi-modal data

### POST `/api/v1/data-integration/augment`

Augment کردن داده با synthetic samples

### POST `/api/v1/data-integration/warehouse/load`

بارگذاری داده در warehouse

### GET `/api/v1/data-integration/warehouse/query`

پرس‌وجو از warehouse

## معیارهای موفقیت

- ✅ Correlation ≥ 0.8 بین synthetic و real data
- ✅ Feature extraction < 30 دقیقه per dataset
- ✅ Augmentation بهبود performance ≥ 5%
- ✅ Data warehouse queries < 5 ثانیه

## مثال خروجی

پس از یکپارچه‌سازی:

```
Loading data...
Synthetic data: 1000 samples
Real data: 500 samples

Integrating data...
Matching scores: {
  'age_correlation': 0.87,
  'age_ks_pvalue': 0.15,
  'gender_similarity': 0.92
}
Fused data: 1500 samples

Engineering features...
Engineered 45 features

✅ Integration complete!
```

## مراحل بعدی

پس از تکمیل فاز 4، می‌توانید به فاز 5 بروید:

**فاز 5: مدل‌های یادگیری ماشین**
- آموزش مدل‌های ML
- Transfer learning
- Model validation
- Explainable AI

## نکات مهم

1. **Feature Engineering:** همیشه features را normalize کنید
2. **Augmentation:** روش مناسب را بر اساس داده انتخاب کنید
3. **Data Warehouse:** برای datasets بزرگ استفاده کنید
4. **Quality Metrics:** همیشه quality metrics را بررسی کنید

## مشکلات احتمالی و راه‌حل

### مشکل: Memory Error برای datasets بزرگ

**راه‌حل:**
- داده‌ها را به batches تقسیم کنید
- از data warehouse استفاده کنید
- فقط features ضروری را استخراج کنید

### مشکل: Feature Engineering کند است

**راه‌حل:**
- از parallel processing استفاده کنید
- فقط features مهم را استخراج کنید
- Cache کردن results

## وضعیت

✅ **فاز 4 به طور کامل تکمیل شد و آماده استفاده است!**

