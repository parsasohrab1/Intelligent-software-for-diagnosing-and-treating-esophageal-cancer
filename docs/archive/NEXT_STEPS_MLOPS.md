# مراحل بعدی - راه‌اندازی MLOps Features

## ✅ کارهای انجام شده

1. ✅ پیاده‌سازی Model Monitoring
2. ✅ پیاده‌سازی Real-time Messaging (Kafka/RabbitMQ)
3. ✅ پیاده‌سازی A/B Testing Framework
4. ✅ پیاده‌سازی Multi-Modality Data Processing
5. ✅ ایجاد API Endpoints
6. ✅ به‌روزرسانی docker-compose.yml
7. ✅ ایجاد اسکریپت‌های راه‌اندازی و تست
8. ✅ ایجاد مستندات کامل

## 🚀 مراحل بعدی (برای شما)

### مرحله 1: نصب وابستگی‌ها

```bash
# روش 1: استفاده از اسکریپت خودکار
python scripts/setup_mlops.py

# روش 2: نصب دستی
pip install -r requirements.txt
```

### مرحله 2: تنظیم فایل .env

اگر فایل `.env` وجود ندارد، از `.env.example` کپی کنید:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# یا دستی ایجاد کنید و تنظیمات زیر را اضافه کنید:
```

محتوای پیشنهادی برای `.env`:

```env
# Message Queue
MESSAGE_QUEUE_TYPE=rabbitmq
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Model Monitoring
MODEL_MONITORING_ENABLED=True
DATA_DRIFT_THRESHOLD=0.1
MODEL_DECAY_THRESHOLD=0.05

# A/B Testing
AB_TESTING_ENABLED=True

# Multi-Modality
MULTI_MODALITY_ENABLED=True
```

### مرحله 3: راه‌اندازی سرویس‌ها

```bash
# راه‌اندازی همه سرویس‌ها (توصیه می‌شود)
docker-compose up -d

# یا فقط سرویس‌های MLOps
docker-compose up -d rabbitmq mongodb

# بررسی وضعیت
docker-compose ps
```

**⏱️ صبر کنید:** 30-60 ثانیه تا سرویس‌ها کاملاً آماده شوند.

### مرحله 4: بررسی اتصال

#### RabbitMQ Management UI

باز کردن در مرورگر:
```
http://localhost:15672
```

ورود:
- Username: `guest`
- Password: `guest`

#### MongoDB

```bash
docker exec -it inescape_mongodb mongosh -u inescape_user -p inescape_password
```

### مرحله 5: راه‌اندازی Application

```bash
# روش 1: استفاده از اسکریپت
python scripts/run_server.py

# روش 2: مستقیم
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### مرحله 6: تست کردن

```bash
# تست کامل با اسکریپت
python scripts/test_mlops.py

# یا تست دستی
curl http://localhost:8001/api/v1/mlops/messaging/status
curl http://localhost:8001/api/v1/mlops/monitoring
curl http://localhost:8001/api/v1/mlops/ab-testing
```

## 📋 چک‌لیست

- [ ] وابستگی‌ها نصب شده (`pip install -r requirements.txt`)
- [ ] فایل `.env` ایجاد و تنظیم شده
- [ ] Docker Desktop در حال اجرا است
- [ ] سرویس‌های Docker راه‌اندازی شده‌اند (`docker-compose up -d`)
- [ ] MongoDB در حال اجرا است
- [ ] RabbitMQ در حال اجرا است (یا Kafka)
- [ ] Application راه‌اندازی شده است
- [ ] تست‌ها با موفقیت اجرا شده‌اند

## 📚 مستندات

برای اطلاعات بیشتر:

- **[MLOPS_FEATURES.md](docs/MLOPS_FEATURES.md)** - راهنمای کامل استفاده از ویژگی‌ها
- **[MLOPS_SETUP_GUIDE.md](MLOPS_SETUP_GUIDE.md)** - راهنمای تفصیلی راه‌اندازی
- **[MLOPS_IMPLEMENTATION_SUMMARY.md](MLOPS_IMPLEMENTATION_SUMMARY.md)** - خلاصه پیاده‌سازی

## 🔍 API Endpoints جدید

### Model Monitoring
- `GET /api/v1/mlops/monitoring` - وضعیت نظارت برای همه مدل‌ها
- `GET /api/v1/mlops/monitoring/{model_id}` - وضعیت نظارت برای یک مدل
- `POST /api/v1/mlops/monitoring/{model_id}/record` - ثبت پیش‌بینی

### A/B Testing
- `POST /api/v1/mlops/ab-testing/create` - ایجاد تست A/B
- `GET /api/v1/mlops/ab-testing` - لیست تست‌های فعال
- `GET /api/v1/mlops/ab-testing/{test_id}` - نتایج تست
- `POST /api/v1/mlops/ab-testing/{test_id}/select-model` - انتخاب مدل
- `POST /api/v1/mlops/ab-testing/{test_id}/record` - ثبت نتیجه
- `POST /api/v1/mlops/ab-testing/{test_id}/stop` - توقف تست

### Messaging
- `POST /api/v1/mlops/messaging/publish` - ارسال پیام
- `GET /api/v1/mlops/messaging/status` - وضعیت اتصال

### Multi-Modality
- `POST /api/v1/multi-modality/process-image` - پردازش تصویر
- `POST /api/v1/multi-modality/process-text` - پردازش متن
- `POST /api/v1/multi-modality/process-multi-modality` - پردازش همزمان

## 🎯 مثال‌های استفاده

### مثال 1: ثبت پیش‌بینی برای Monitoring

```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/mlops/monitoring/model_123/record",
    json={
        "features": {"age": 65, "bmi": 25},
        "prediction": 1,
        "probability": [0.2, 0.8],
        "ground_truth": 1
    }
)
```

### مثال 2: ایجاد تست A/B

```python
response = requests.post(
    "http://localhost:8001/api/v1/mlops/ab-testing/create",
    json={
        "test_name": "New Model Test",
        "control_model_id": "model_v1",
        "treatment_model_id": "model_v2",
        "traffic_split": 0.5
    }
)
test_id = response.json()["test_id"]
```

### مثال 3: پردازش متن

```python
response = requests.post(
    "http://localhost:8001/api/v1/multi-modality/process-text",
    json={
        "text": "CT scan shows mass in esophagus. Tumor size: 2.5 cm.",
        "report_type": "radiology"
    }
)
entities = response.json()["extracted_entities"]
```

## 🆘 عیب‌یابی

اگر مشکلی پیش آمد:

1. **بررسی لاگ‌های Docker:**
   ```bash
   docker-compose logs rabbitmq
   docker-compose logs mongodb
   ```

2. **بررسی لاگ‌های Application:**
   - لاگ‌ها در console نمایش داده می‌شوند

3. **اجرای تست‌ها:**
   ```bash
   python scripts/test_mlops.py
   ```

4. **بررسی مستندات:**
   - [MLOPS_SETUP_GUIDE.md](MLOPS_SETUP_GUIDE.md) - بخش عیب‌یابی

## ✨ نکات مهم

1. **Model Monitoring**: برای عملکرد بهتر، حداقل 100 پیش‌بینی لازم است
2. **A/B Testing**: برای نتایج آماری معتبر، حداقل 1000 پیش‌بینی برای هر variant توصیه می‌شود
3. **Message Queue**: در محیط production، از persistent queues استفاده کنید
4. **Multi-Modality**: فایل‌های DICOM و NIfTI ممکن است بزرگ باشند

---

**موفق باشید! 🎉**

