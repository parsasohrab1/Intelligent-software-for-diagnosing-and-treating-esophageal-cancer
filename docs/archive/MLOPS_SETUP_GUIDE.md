# راهنمای راه‌اندازی MLOps Features

این راهنما مراحل نصب و راه‌اندازی ویژگی‌های MLOps را به صورت گام‌به‌گام توضیح می‌دهد.

## 📋 پیش‌نیازها

- Python 3.8+
- Docker Desktop (برای RabbitMQ, Kafka, MongoDB)
- pip (Python package manager)

## 🚀 مراحل راه‌اندازی

### مرحله 1: نصب وابستگی‌ها

#### روش 1: استفاده از اسکریپت خودکار

```bash
python scripts/setup_mlops.py
```

این اسکریپت به صورت خودکار:
- وابستگی‌های لازم را نصب می‌کند
- فایل `.env` را ایجاد می‌کند
- وضعیت سرویس‌ها را بررسی می‌کند

#### روش 2: نصب دستی

```bash
pip install -r requirements.txt
```

### مرحله 2: تنظیم فایل .env

اگر فایل `.env` وجود ندارد، از `.env.example` کپی کنید:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید و تنظیمات زیر را بررسی کنید:

```env
# Message Queue
MESSAGE_QUEUE_TYPE=rabbitmq  # یا "kafka"

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Model Monitoring
MODEL_MONITORING_ENABLED=True
DATA_DRIFT_THRESHOLD=0.1
MODEL_DECAY_THRESHOLD=0.05

# A/B Testing
AB_TESTING_ENABLED=True

# Multi-Modality
MULTI_MODALITY_ENABLED=True
```

### مرحله 3: راه‌اندازی سرویس‌ها با Docker

#### راه‌اندازی همه سرویس‌ها (توصیه می‌شود)

```bash
docker-compose up -d
```

این دستور همه سرویس‌ها را راه‌اندازی می‌کند:
- PostgreSQL
- MongoDB
- Redis
- RabbitMQ
- Kafka + Zookeeper
- MinIO
- Prometheus
- Grafana

#### راه‌اندازی فقط سرویس‌های MLOps

```bash
# فقط RabbitMQ
docker-compose up -d rabbitmq mongodb

# یا فقط Kafka
docker-compose up -d kafka zookeeper mongodb

# یا هر دو
docker-compose up -d rabbitmq kafka zookeeper mongodb
```

#### بررسی وضعیت سرویس‌ها

```bash
docker-compose ps
```

صبر کنید تا همه سرویس‌ها `healthy` شوند (30-60 ثانیه).

### مرحله 4: بررسی اتصال سرویس‌ها

#### RabbitMQ Management UI

باز کردن در مرورگر:
```
http://localhost:15672
```

ورود با:
- Username: `guest`
- Password: `guest`

#### Kafka

بررسی با:
```bash
docker exec -it inescape_kafka kafka-topics --list --bootstrap-server localhost:9092
```

#### MongoDB

بررسی با:
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

#### تست با اسکریپت

```bash
python scripts/test_mlops.py
```

#### تست دستی

```bash
# تست API health
curl http://localhost:8001/api/v1/health

# تست messaging status
curl http://localhost:8001/api/v1/mlops/messaging/status

# تست monitoring
curl http://localhost:8001/api/v1/mlops/monitoring

# تست A/B testing
curl http://localhost:8001/api/v1/mlops/ab-testing

# تست multi-modality (text)
curl -X POST http://localhost:8001/api/v1/multi-modality/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "CT scan shows mass.", "report_type": "radiology"}'
```

## 🔍 عیب‌یابی

### مشکل: Docker services شروع نمی‌شوند

```bash
# بررسی لاگ‌ها
docker-compose logs rabbitmq
docker-compose logs kafka
docker-compose logs mongodb

# Restart سرویس
docker-compose restart rabbitmq
```

### مشکل: Port در حال استفاده است

```bash
# Windows: پیدا کردن process
netstat -ano | findstr :5672
netstat -ano | findstr :9092

# Linux/Mac: پیدا کردن process
lsof -i :5672
lsof -i :9092

# تغییر port در docker-compose.yml یا .env
```

### مشکل: وابستگی‌ها نصب نمی‌شوند

```bash
# به‌روزرسانی pip
python -m pip install --upgrade pip

# نصب جداگانه
pip install pika==1.3.2
pip install kafka-python==2.0.2
pip install pydicom==2.4.4
pip install nibabel==5.2.1
pip install opencv-python==4.8.1.78
pip install Pillow==10.1.0
```

### مشکل: MongoDB connection failed

```bash
# بررسی MongoDB
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb

# بررسی لاگ
docker-compose logs mongodb
```

### مشکل: Message Queue متصل نمی‌شود

1. بررسی کنید که سرویس در حال اجرا باشد:
   ```bash
   docker-compose ps rabbitmq
   # یا
   docker-compose ps kafka
   ```

2. بررسی تنظیمات در `.env`:
   ```env
   MESSAGE_QUEUE_TYPE=rabbitmq  # یا kafka
   RABBITMQ_HOST=localhost
   RABBITMQ_PORT=5672
   ```

3. تست اتصال:
   ```python
   # برای RabbitMQ
   import pika
   connection = pika.BlockingConnection(
       pika.ConnectionParameters('localhost', 5672)
   )
   
   # برای Kafka
   from kafka import KafkaProducer
   producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
   ```

## ✅ چک‌لیست راه‌اندازی

- [ ] Python 3.8+ نصب شده
- [ ] Docker Desktop در حال اجرا است
- [ ] وابستگی‌ها نصب شده‌اند (`pip install -r requirements.txt`)
- [ ] فایل `.env` ایجاد و تنظیم شده
- [ ] سرویس‌های Docker راه‌اندازی شده‌اند
- [ ] MongoDB در حال اجرا است
- [ ] RabbitMQ یا Kafka در حال اجرا است
- [ ] Application راه‌اندازی شده است
- [ ] تست‌ها با موفقیت اجرا شده‌اند

## 📚 منابع بیشتر

- [مستندات کامل MLOps Features](docs/MLOPS_FEATURES.md)
- [خلاصه پیاده‌سازی](MLOPS_IMPLEMENTATION_SUMMARY.md)
- [API Documentation](http://localhost:8001/docs)

## 🆘 پشتیبانی

اگر مشکلی پیش آمد:
1. لاگ‌های Docker را بررسی کنید
2. لاگ‌های Application را بررسی کنید
3. اسکریپت `test_mlops.py` را اجرا کنید
4. Issue در repository ایجاد کنید

