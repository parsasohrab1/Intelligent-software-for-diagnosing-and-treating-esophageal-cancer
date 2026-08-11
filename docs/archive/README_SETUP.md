# راهنمای راه‌اندازی پروژه INEsCape

این راهنما برای راه‌اندازی محیط توسعه پروژه INEsCape است.

## پیش‌نیازها

- Python 3.9 یا بالاتر
- Docker و Docker Compose
- Git
- (اختیاری) Node.js 18+ برای frontend

## نصب و راه‌اندازی

### 1. کلون کردن پروژه

```bash
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
```

### 2. ایجاد محیط مجازی Python

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. نصب وابستگی‌ها

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. تنظیم متغیرهای محیطی

```bash
cp .env.example .env
# فایل .env را ویرایش کنید و مقادیر مناسب را تنظیم کنید
```

### 5. راه‌اندازی سرویس‌های پایگاه داده با Docker

```bash
docker-compose up -d
```

این دستور سرویس‌های زیر را راه‌اندازی می‌کند:
- PostgreSQL (پورت 5432)
- MongoDB (پورت 27017)
- Redis (پورت 6379)
- MinIO (پورت 9000, 9001)
- Prometheus (پورت 9090)
- Grafana (پورت 3000)

### 6. بررسی وضعیت سرویس‌ها

```bash
docker-compose ps
```

### 7. راه‌اندازی پایگاه داده

```bash
# اجرای migrations
alembic upgrade head

# یا استفاده از اسکریپت
python scripts/init_database.py
```

### 8. راه‌اندازی سرویس API

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# یا با استفاده از script
python scripts/run_server.py
```

### 9. دسترسی به سرویس‌ها

- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health
- **Grafana:** http://localhost:3000 (admin/admin)
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)
- **Prometheus:** http://localhost:9090

## ساختار پروژه

```
.
├── app/                    # کد اصلی اپلیکیشن
│   ├── api/               # API endpoints
│   ├── core/              # تنظیمات و utilities
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── main.py            # FastAPI app
├── scripts/               # اسکریپت‌های کمکی
├── tests/                 # تست‌ها
├── monitoring/            # تنظیمات monitoring
├── alembic/               # Database migrations
├── docker-compose.yml     # Docker services
├── requirements.txt       # Python dependencies
└── README_SETUP.md        # این فایل
```

## دستورات مفید

### Database Migrations

```bash
# ایجاد migration جدید
alembic revision --autogenerate -m "description"

# اعمال migrations
alembic upgrade head

# بازگشت به migration قبلی
alembic downgrade -1
```

### Testing

```bash
# اجرای تمام تست‌ها
pytest

# با coverage
pytest --cov=app --cov-report=html

# تست‌های خاص
pytest tests/test_specific.py
```

### Code Quality

```bash
# Format code
black app/

# Check linting
flake8 app/

# Type checking
mypy app/

# Sort imports
isort app/
```

### Docker Commands

```bash
# مشاهده لاگ‌ها
docker-compose logs -f

# توقف سرویس‌ها
docker-compose down

# توقف و حذف volumes
docker-compose down -v

# بازسازی containers
docker-compose up -d --build
```

## عیب‌یابی

### مشکل اتصال به پایگاه داده

1. بررسی کنید که Docker containers در حال اجرا هستند:
   ```bash
   docker-compose ps
   ```

2. بررسی لاگ‌های PostgreSQL:
   ```bash
   docker-compose logs postgres
   ```

3. تست اتصال:
   ```bash
   python scripts/test_db_connection.py
   ```

### مشکل پورت در حال استفاده

اگر پورتی در حال استفاده است، می‌توانید در `docker-compose.yml` پورت را تغییر دهید.

### مشکل نصب وابستگی‌ها

```bash
# به‌روزرسانی pip
pip install --upgrade pip setuptools wheel

# نصب مجدد
pip install -r requirements.txt --no-cache-dir
```

## مراحل بعدی

پس از راه‌اندازی موفق:

1. بررسی کنید که تمام سرویس‌ها در حال اجرا هستند
2. API documentation را در http://localhost:8000/docs بررسی کنید
3. تست‌های اولیه را اجرا کنید
4. به فاز 2 (تولید داده سنتتیک) بروید

## پشتیبانی

در صورت بروز مشکل، لطفاً issue در repository ایجاد کنید.

