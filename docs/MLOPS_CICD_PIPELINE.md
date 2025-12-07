# خط لوله CI/CD/MLOps برای مدل‌های ML

این سند راهنمای کامل سیستم CI/CD/MLOps برای به‌روزرسانی منظم مدل‌ها و نظارت بر عملکرد در محیط تولید است.

## نیازمندی‌ها

### نظارت مداوم
- **Data Drift Detection**: تشخیص تغییرات در توزیع داده‌ها
- **Model Decay Detection**: تشخیص کاهش عملکرد مدل
- **Equipment Changes**: تشخیص تغییرات در تجهیزات تصویربرداری
- **Population Changes**: تشخیص تغییرات در جمعیت بیماران

### به‌روزرسانی منظم
- **Automated Retraining**: آموزش مجدد خودکار
- **CI/CD Pipeline**: خط لوله کامل برای deployment
- **A/B Testing**: تست مدل‌های جدید قبل از production
- **Versioning & Rollback**: مدیریت نسخه‌ها و قابلیت rollback

## سیستم‌های پیاده‌سازی شده

### 1. CI/CD Pipeline ✅

خط لوله کامل برای آموزش، اعتبارسنجی، تست و استقرار مدل‌ها

**مراحل:**
1. **Data Collection**: جمع‌آوری داده برای آموزش
2. **Data Validation**: اعتبارسنجی داده
3. **Model Training**: آموزش مدل
4. **Model Validation**: اعتبارسنجی مدل
5. **Model Testing**: تست مدل
6. **A/B Testing**: راه‌اندازی A/B test
7. **Model Deployment**: استقرار مدل
8. **Production Monitoring**: راه‌اندازی نظارت

**API Endpoints:**
- `POST /api/v1/mlops/cicd/run-pipeline` - اجرای خط لوله
- `GET /api/v1/mlops/cicd/pipeline-history` - تاریخچه خط لوله
- `GET /api/v1/mlops/cicd/check-retrain/{model_id}` - بررسی نیاز به retraining

### 2. Automated Retraining ✅

سیستم آموزش مجدد خودکار بر اساس شرایط

**محرک‌های Retraining:**
- **Scheduled**: زمان‌بندی شده (مثلاً هر 30 روز)
- **Drift Detected**: تشخیص data drift
- **Decay Detected**: تشخیص model decay
- **Manual**: دستی
- **Data Accumulation**: تجمع داده جدید

**API Endpoints:**
- `POST /api/v1/mlops/retraining/start` - شروع retraining خودکار
- `POST /api/v1/mlops/retraining/stop` - توقف retraining خودکار
- `POST /api/v1/mlops/retraining/trigger` - راه‌اندازی دستی retraining
- `GET /api/v1/mlops/retraining/history` - تاریخچه retraining
- `GET /api/v1/mlops/retraining/stats` - آمار retraining

### 3. Production Model Monitoring ✅

نظارت پیشرفته بر مدل‌ها در محیط تولید

**بررسی‌ها:**
- **Data Drift**: بررسی پیشرفته drift در ویژگی‌ها
- **Model Performance**: بررسی عملکرد مدل
- **Prediction Distribution**: بررسی توزیع پیش‌بینی‌ها
- **Feature Importance Drift**: تغییر در اهمیت ویژگی‌ها
- **Equipment Changes**: تغییرات در تجهیزات
- **Population Changes**: تغییرات در جمعیت بیماران

**API Endpoints:**
- `GET /api/v1/mlops/production-monitoring` - نظارت تمام مدل‌ها
- `GET /api/v1/mlops/production-monitoring/{model_id}` - نظارت یک مدل
- `GET /api/v1/mlops/production-monitoring/alerts` - دریافت هشدارها

### 4. Advanced Alerting System ✅

سیستم هشدار پیشرفته برای رویدادهای مهم

**سطح‌های هشدار:**
- **INFO**: اطلاعاتی
- **WARNING**: هشدار
- **CRITICAL**: بحرانی

**انواع هشدار:**
- Data drift detected
- Model decay detected
- Equipment changes
- Population changes

### 5. Model Versioning & Rollback ✅

مدیریت نسخه‌های مدل و قابلیت rollback

**ویژگی‌ها:**
- Semantic versioning (major.minor.patch)
- Version history
- Rollback to previous version
- Promotion workflow (Development → Staging → Production)

**API Endpoints:**
- `POST /api/v1/mlops/versioning/create-version` - ایجاد نسخه جدید
- `GET /api/v1/mlops/versioning/{model_id}/versions` - دریافت نسخه‌ها
- `POST /api/v1/mlops/versioning/{version_id}/promote-to-production` - ارتقا به production
- `POST /api/v1/mlops/versioning/{model_id}/rollback` - Rollback

### 6. A/B Testing ✅

تست مدل‌های جدید قبل از production

**ویژگی‌ها:**
- Traffic splitting
- Performance comparison
- Statistical significance testing
- Automatic winner selection

## استفاده

### مثال: اجرای CI/CD Pipeline
```python
from app.services.mlops.cicd_pipeline import MLModelCICDPipeline

pipeline = MLModelCICDPipeline()
result = pipeline.run_pipeline(
    model_type="RandomForest",
    trigger_reason="drift_detected"
)

print(f"Pipeline status: {result.status}")
print(f"New model ID: {result.model_id}")
```

### مثال: شروع Automated Retraining
```python
from app.services.mlops.automated_retraining import AutomatedRetraining

retraining = AutomatedRetraining()
retraining.start_automated_retraining()

# System will automatically:
# - Check for drift every hour
# - Check for decay every hour
# - Run daily retraining check at 2 AM
```

### مثال: نظارت Production
```python
from app.services.mlops.production_monitoring import ProductionModelMonitoring

monitoring = ProductionModelMonitoring()
results = monitoring.monitor_production_models()

for model_id, result in results.items():
    print(f"Model {model_id}:")
    print(f"  Health Score: {result['overall_health']}")
    print(f"  Alerts: {len(result['alerts'])}")
```

### مثال: Rollback
```python
from app.services.mlops.model_versioning import ModelVersioning

versioning = ModelVersioning()
previous_version = versioning.rollback_to_previous("RandomForest_20240101")

print(f"Rolled back to version {previous_version.version_number}")
```

## Workflow پیشنهادی

### 1. نظارت مداوم
```
Production Model → Monitoring → Detect Issues → Trigger Retraining
```

### 2. Retraining خودکار
```
Drift/Decay Detected → Check Conditions → Run CI/CD Pipeline → A/B Test → Deploy
```

### 3. A/B Testing
```
New Model → A/B Test (10% traffic) → Monitor Performance → Increase Traffic → Full Deployment
```

### 4. Rollback
```
Issue Detected → Rollback to Previous Version → Investigate → Fix → Retrain
```

## تنظیمات

### در config.py
```python
# Model Monitoring
MODEL_MONITORING_ENABLED: bool = True
DATA_DRIFT_THRESHOLD: float = 0.1
MODEL_DECAY_THRESHOLD: float = 0.05
MONITORING_WINDOW_SIZE: int = 1000
MONITORING_CHECK_INTERVAL: int = 3600  # 1 hour

# A/B Testing
AB_TESTING_ENABLED: bool = True
AB_TEST_DEFAULT_TRAFFIC_SPLIT: float = 0.5
```

## بهترین روش‌ها

1. **نظارت مداوم**: نظارت بر تمام مدل‌های production
2. **Retraining منظم**: retraining بر اساس شرایط یا زمان‌بندی
3. **A/B Testing**: همیشه مدل‌های جدید را با A/B test تست کنید
4. **Versioning**: تمام نسخه‌ها را نگه دارید
5. **Rollback Plan**: همیشه یک plan برای rollback داشته باشید
6. **Documentation**: تمام تغییرات را مستند کنید
7. **Alerting**: هشدارهای مناسب تنظیم کنید

## معیارهای کلیدی

### Data Drift
- **Threshold**: 0.1 (Kolmogorov-Smirnov statistic)
- **Check Frequency**: هر 100 پیش‌بینی یا هر ساعت
- **Action**: Retrain if drift detected

### Model Decay
- **Threshold**: 0.05 (5% accuracy drop)
- **Check Frequency**: هر 100 پیش‌بینی با ground truth
- **Action**: Retrain if decay detected

### Health Score
- **Range**: 0.0 - 1.0
- **Good**: > 0.8
- **Warning**: 0.6 - 0.8
- **Critical**: < 0.6

## وضعیت

تمام سیستم‌های CI/CD/MLOps با موفقیت پیاده‌سازی شدند و آماده استفاده برای نظارت و به‌روزرسانی مدل‌ها در محیط تولید هستند.

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

