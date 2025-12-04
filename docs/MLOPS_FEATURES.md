# راهنمای ویژگی‌های MLOps و پردازش چندوجهی

این سند راهنمای استفاده از ویژگی‌های جدید MLOps و پردازش چندوجهی است که به سیستم اضافه شده‌اند.

## فهرست مطالب

1. [Model Monitoring (نظارت بر مدل)](#model-monitoring)
2. [Real-time Messaging (پیام‌رسانی بلادرنگ)](#real-time-messaging)
3. [A/B Testing Framework](#ab-testing-framework)
4. [Multi-Modality Data Processing](#multi-modality-data-processing)

---

## Model Monitoring (نظارت بر مدل)

### بررسی Data Drift و Model Decay

سیستم نظارت بر مدل به صورت خودکار تغییرات در توزیع داده‌ها (Data Drift) و کاهش عملکرد مدل (Model Decay) را ردیابی می‌کند.

### تنظیمات

در فایل `app/core/config.py`:

```python
MODEL_MONITORING_ENABLED: bool = True
DATA_DRIFT_THRESHOLD: float = 0.1  # آستانه برای تشخیص drift
MODEL_DECAY_THRESHOLD: float = 0.05  # آستانه برای تشخیص کاهش عملکرد
MONITORING_WINDOW_SIZE: int = 1000  # تعداد پیش‌بینی‌ها برای نظارت
```

### API Endpoints

#### دریافت وضعیت نظارت برای یک مدل

```http
GET /api/v1/mlops/monitoring/{model_id}
```

**Response:**
```json
{
  "model_id": "RandomForest_20240101_120000",
  "drift_status": {
    "drift_detected": false,
    "timestamp": "2024-01-01T12:00:00",
    "feature_drifts": {}
  },
  "decay_status": {
    "decay_detected": false,
    "current_accuracy": 0.95,
    "baseline_accuracy": 0.96,
    "accuracy_decay": 0.01
  },
  "recent_alerts": []
}
```

#### دریافت وضعیت نظارت برای همه مدل‌ها

```http
GET /api/v1/mlops/monitoring
```

#### ثبت پیش‌بینی برای نظارت

```http
POST /api/v1/mlops/monitoring/{model_id}/record
Content-Type: application/json

{
  "features": {
    "age": 65,
    "bmi": 25.5,
    "smoking_years": 20
  },
  "prediction": 1,
  "probability": [0.2, 0.8],
  "ground_truth": 1
}
```

### استفاده خودکار

هنگامی که از endpoint `/api/v1/ml-models/predict` استفاده می‌کنید، پیش‌بینی‌ها به صورت خودکار برای نظارت ثبت می‌شوند (اگر `MODEL_MONITORING_ENABLED=True` باشد).

---

## Real-time Messaging (پیام‌رسانی بلادرنگ)

### پشتیبانی از Kafka و RabbitMQ

سیستم از هر دو پلتفرم پیام‌رسانی Kafka و RabbitMQ پشتیبانی می‌کند.

### تنظیمات

در فایل `app/core/config.py`:

```python
MESSAGE_QUEUE_TYPE: str = "rabbitmq"  # یا "kafka"

# تنظیمات RabbitMQ
RABBITMQ_HOST: str = "localhost"
RABBITMQ_PORT: int = 5672
RABBITMQ_USER: str = "guest"
RABBITMQ_PASSWORD: str = "guest"

# تنظیمات Kafka
KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
KAFKA_TOPIC_PATIENT_DATA: str = "patient-data"
KAFKA_TOPIC_IMAGING_DATA: str = "imaging-data"
KAFKA_TOPIC_ALERTS: str = "alerts"
```

### API Endpoints

#### ارسال پیام

```http
POST /api/v1/mlops/messaging/publish
Content-Type: application/json

{
  "topic": "patient_data",
  "message": {
    "patient_id": "P001",
    "event_type": "new_imaging",
    "data": {
      "modality": "CT",
      "timestamp": "2024-01-01T12:00:00"
    }
  }
}
```

#### دریافت وضعیت پیام‌رسانی

```http
GET /api/v1/mlops/messaging/status
```

**Response:**
```json
{
  "queue_type": "rabbitmq",
  "connected": true
}
```

### استفاده در کد

```python
from app.services.messaging.message_queue import get_message_queue

queue = get_message_queue()

# ارسال پیام
queue.publish("patient_data", {
    "patient_id": "P001",
    "event": "new_data"
})

# دریافت پیام (در background worker)
def process_message(message):
    print(f"Received: {message}")

queue.subscribe("patient_data", process_message)
```

---

## A/B Testing Framework

### ایجاد و مدیریت تست‌های A/B

این فریمورک امکان استقرار و تست نسخه‌های جدید مدل در کنار مدل فعلی را فراهم می‌کند.

### API Endpoints

#### ایجاد تست A/B

```http
POST /api/v1/mlops/ab-testing/create
Content-Type: application/json

{
  "test_name": "New RandomForest Model Test",
  "control_model_id": "RandomForest_20240101_120000",
  "treatment_model_id": "RandomForest_20240102_120000",
  "traffic_split": 0.5,
  "metric": "accuracy"
}
```

**Response:**
```json
{
  "test_id": "ab_test_20240102_120000",
  "message": "A/B test created successfully"
}
```

#### لیست تست‌های فعال

```http
GET /api/v1/mlops/ab-testing
```

#### انتخاب مدل برای تست A/B

```http
POST /api/v1/mlops/ab-testing/{test_id}/select-model?user_id=user123
```

**Response:**
```json
{
  "model_id": "RandomForest_20240102_120000",
  "variant": "treatment",
  "test_id": "ab_test_20240102_120000"
}
```

#### ثبت نتیجه تست

```http
POST /api/v1/mlops/ab-testing/{test_id}/record
Content-Type: application/json

{
  "variant": "treatment",
  "prediction": 1,
  "ground_truth": 1,
  "metrics": {
    "confidence": 0.95
  }
}
```

#### دریافت نتایج تست

```http
GET /api/v1/mlops/ab-testing/{test_id}
```

**Response:**
```json
{
  "test_id": "ab_test_20240102_120000",
  "test_name": "New RandomForest Model Test",
  "status": "active",
  "control": {
    "model_id": "RandomForest_20240101_120000",
    "predictions": 1000,
    "accuracy": 0.92
  },
  "treatment": {
    "model_id": "RandomForest_20240102_120000",
    "predictions": 1000,
    "accuracy": 0.95
  },
  "improvement": 0.03,
  "statistical_significance": {
    "chi2": 8.5,
    "p_value": 0.003,
    "significant": true
  }
}
```

#### توقف تست A/B

```http
POST /api/v1/mlops/ab-testing/{test_id}/stop?winner=treatment
```

### جریان کار

1. ایجاد تست A/B با مدل کنترل و مدل جدید
2. استفاده از endpoint `select-model` برای انتخاب مدل در هر درخواست
3. ثبت نتایج پیش‌بینی‌ها
4. بررسی نتایج و تحلیل آماری
5. توقف تست و انتخاب برنده

---

## Multi-Modality Data Processing

### پردازش تصاویر پزشکی و گزارش‌های متنی

این سیستم امکان پردازش همزمان تصاویر پزشکی (CT, MRI, DICOM, NIfTI) و گزارش‌های متنی غیرساختاریافته را فراهم می‌کند.

### فرمت‌های پشتیبانی شده

- **تصاویر:** DICOM (.dcm), NIfTI (.nii, .nii.gz), PNG, JPG, TIFF
- **گزارش‌ها:** متن خام، گزارش‌های رادیولوژی، گزارش‌های بالینی

### تنظیمات

```python
MULTI_MODALITY_ENABLED: bool = True
IMAGE_PROCESSING_BACKEND: str = "opencv"  # یا "pillow"
TEXT_PROCESSING_BACKEND: str = "spacy"  # یا "nltk"
MAX_IMAGE_SIZE_MB: int = 50
SUPPORTED_IMAGE_FORMATS: List[str] = ["dicom", "nifti", "png", "jpg", "jpeg", "tiff"]
```

### API Endpoints

#### پردازش تصویر

```http
POST /api/v1/multi-modality/process-image
Content-Type: multipart/form-data

file: [image file]
modality: CT
text_report: "Findings: Mass in esophagus..."
```

**Response:**
```json
{
  "modality": "CT",
  "processed_at": "2024-01-01T12:00:00",
  "image": {
    "file_path": "/tmp/image.dcm",
    "format": "dicom",
    "file_size_mb": 2.5,
    "dicom_metadata": {
      "patient_id": "P001",
      "study_date": "20240101",
      "modality": "CT"
    },
    "image_statistics": {
      "shape": [512, 512, 100],
      "mean_value": 125.5,
      "std_value": 45.2
    }
  },
  "text_report": {
    "text_length": 500,
    "word_count": 80,
    "extracted_entities": {
      "pathologies": ["tumor", "mass"],
      "anatomical_structures": ["esophagus"]
    },
    "findings": [
      "Mass in esophagus",
      "Wall thickness increased"
    ],
    "measurements": [
      {"value": 2.5, "unit": "cm", "text": "2.5 cm"}
    ]
  }
}
```

#### پردازش متن

```http
POST /api/v1/multi-modality/process-text
Content-Type: application/json

{
  "text": "CT scan shows mass in esophagus...",
  "report_type": "radiology"
}
```

#### پردازش چندوجهی (تصویر + متن)

```http
POST /api/v1/multi-modality/process-multi-modality
Content-Type: multipart/form-data

file: [image file]
modality: MRI
text_report: "MRI findings: ..."
```

### استفاده در کد

```python
from app.services.data_processing.multi_modality import MultiModalityProcessor

processor = MultiModalityProcessor()

# پردازش تصویر
result = processor.process_imaging_data(
    image_path="path/to/image.dcm",
    modality="CT",
    text_report="Findings: ..."
)

# پردازش متن
text_result = processor.process_text_only(
    text="Clinical report...",
    report_type="clinical"
)
```

---

## نصب و راه‌اندازی

### 1. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### 2. راه‌اندازی Message Queue

#### RabbitMQ

```bash
# با Docker
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# یا با docker-compose
docker-compose up -d rabbitmq
```

#### Kafka

```bash
# با Docker
docker-compose up -d kafka zookeeper
```

### 3. تنظیم متغیرهای محیطی

ایجاد فایل `.env`:

```env
MESSAGE_QUEUE_TYPE=rabbitmq
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
MODEL_MONITORING_ENABLED=true
MULTI_MODALITY_ENABLED=true
```

### 4. راه‌اندازی MongoDB (برای Model Registry و Monitoring)

```bash
docker-compose up -d mongodb
```

---

## مثال‌های استفاده

### مثال 1: نظارت بر مدل

```python
from app.services.mlops.model_monitoring import ModelMonitoring

monitoring = ModelMonitoring()

# ثبت پیش‌بینی
monitoring.record_prediction(
    model_id="model_123",
    features={"age": 65, "bmi": 25},
    prediction=1,
    ground_truth=1
)

# بررسی وضعیت
status = monitoring.get_monitoring_status("model_123")
print(status)
```

### مثال 2: تست A/B

```python
from app.services.mlops.ab_testing import ABTestManager

ab_manager = ABTestManager()

# ایجاد تست
test_id = ab_manager.create_ab_test(
    test_name="New Model Test",
    control_model_id="model_v1",
    treatment_model_id="model_v2",
    traffic_split=0.5
)

# انتخاب مدل
model_id, variant = ab_manager.select_model(test_id, user_id="user123")

# ثبت نتیجه
ab_manager.record_prediction_result(
    test_id=test_id,
    variant=variant,
    prediction=1,
    ground_truth=1
)

# دریافت نتایج
results = ab_manager.get_test_results(test_id)
print(results)
```

### مثال 3: پردازش چندوجهی

```python
from app.services.data_processing.multi_modality import MultiModalityProcessor

processor = MultiModalityProcessor()

# پردازش تصویر DICOM با گزارش
result = processor.process_imaging_data(
    image_path="patient_scan.dcm",
    modality="CT",
    text_report="CT scan shows esophageal mass..."
)

print(result["image"]["dicom_metadata"])
print(result["text_report"]["extracted_entities"])
```

---

## نکات مهم

1. **Model Monitoring**: برای عملکرد بهتر، حداقل 100 پیش‌بینی برای بررسی drift و decay لازم است.

2. **A/B Testing**: برای نتایج آماری معتبر، حداقل 1000 پیش‌بینی برای هر variant توصیه می‌شود.

3. **Message Queue**: در محیط production، از persistent queues استفاده کنید تا پیام‌ها در صورت restart از دست نروند.

4. **Multi-Modality**: فایل‌های DICOM و NIfTI ممکن است بزرگ باشند. حداکثر اندازه را در تنظیمات تنظیم کنید.

---

## عیب‌یابی

### مشکل: Model Monitoring کار نمی‌کند

- بررسی کنید که MongoDB در دسترس باشد
- بررسی کنید که `MODEL_MONITORING_ENABLED=True` باشد
- لاگ‌ها را برای خطاها بررسی کنید

### مشکل: Message Queue متصل نمی‌شود

- بررسی کنید که RabbitMQ یا Kafka در حال اجرا باشد
- بررسی تنظیمات اتصال در `.env`
- بررسی لاگ‌های اتصال

### مشکل: پردازش تصویر خطا می‌دهد

- بررسی کنید که کتابخانه‌های لازم نصب شده باشند (pydicom, nibabel, opencv-python)
- بررسی اندازه فایل (نباید از `MAX_IMAGE_SIZE_MB` بیشتر باشد)
- بررسی فرمت فایل (باید در `SUPPORTED_IMAGE_FORMATS` باشد)

---

## پشتیبانی

برای سوالات و مشکلات، لطفاً issue در repository ایجاد کنید.

