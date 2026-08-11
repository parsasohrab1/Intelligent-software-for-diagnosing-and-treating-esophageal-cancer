# INEsCape - Intelligent Nanosystem for Esophageal Cancer

**پلتفرم یکپارچه نانوترانوستیک برای تشخیص و درمان سرطان مری**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 فهرست مطالب

- [معرفی](#معرفی)
- [ویژگی‌های کلیدی](#ویژگی‌های-کلیدی)
- [معماری](#معماری)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [استفاده سریع](#استفاده-سریع)
- [مستندات](#مستندات)
- [API Documentation](#api-documentation)
- [تست](#تست)
- [استقرار](#استقرار)
- [مشارکت](#مشارکت)

## 🎯 معرفی

INEsCape یک پلتفرم جامع برای مدیریت سرطان مری است که شامل:

- **تولید داده سنتتیک** برای توسعه و تست
- **جمع‌آوری داده واقعی** از منابع عمومی
- **مدل‌های یادگیری ماشین** برای پیش‌بینی و تشخیص
- **سیستم پشتیبانی تصمیم‌گیری بالینی (CDS)** برای کمک به پزشکان
- **رابط کاربری وب** برای دسترسی آسان
- **امنیت و اخلاقیات** برای حفاظت از داده‌ها

## ✨ ویژگی‌های کلیدی

### 🔬 تولید و مدیریت داده
- تولید داده سنتتیک با کیفیت بالا
- جمع‌آوری داده از TCGA, GEO, Kaggle
- De-identification و quality control
- یکپارچه‌سازی داده‌های سنتتیک و واقعی

### 🤖 یادگیری ماشین
- مدل‌های مختلف: Logistic Regression, Random Forest, XGBoost, LightGBM, Neural Networks
- Training pipeline با experiment tracking
- Explainable AI با SHAP
- Model registry و versioning
- **MLOps Features:**
  - Model Monitoring (Data Drift & Model Decay detection)
  - A/B Testing Framework
  - Real-time Messaging (Kafka/RabbitMQ)
  - Multi-Modality Data Processing (DICOM, NIfTI, Text Reports)

### 🏥 پشتیبانی تصمیم‌گیری بالینی
- پیش‌بینی ریسک سرطان
- پیشنهادات درمانی بر اساس NCCN guidelines
- امتیازدهی پیش‌آگهی
- تطبیق با کارآزمایی‌های بالینی
- نظارت بلادرنگ و هشدارها

### 🔒 امنیت
- Authentication با JWT
- Role-Based Access Control (RBAC)
- Encryption برای داده‌های حساس
- Audit logging کامل
- Ethical guidelines

### 📊 رابط کاربری
- Dashboard تعاملی
- Visualization tools
- مدیریت patients
- Interface برای تمام user types

## 🏗️ معماری

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API Gateway (FastAPI)                       │
├──────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │  Auth    │  │  Data    │  │   ML     │  │   CDS    ││
│  │  Service │  │  Service │  │  Service │  │  Service ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└────────────────────┬────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐      ┌─────▼─────┐    ┌────▼────┐
│PostgreSQL│    │  MongoDB  │    │  Redis  │
└─────────┘    └───────────┘    └─────────┘
```

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (برای frontend)
- PostgreSQL 14+ (یا استفاده از Docker)
- MongoDB 6+ (یا استفاده از Docker)
- Redis 7+ (یا استفاده از Docker)

### نصب سریع

```bash
# Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# Install Python dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services with Docker Compose
docker-compose up -d

# Initialize database
python scripts/init_database.py

# Create admin user
python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password secure_password

# Start backend server
python scripts/run_server.py
```

### نصب Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🎮 استفاده سریع

### 1. تولید داده سنتتیک

```python
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData

generator = EsophagealCancerSyntheticData()
data = generator.generate_complete_dataset(n_patients=1000, cancer_ratio=0.3)
```

### 2. آموزش مدل ML

```python
from app.services.ml_training import MLTrainingPipeline

pipeline = MLTrainingPipeline()
X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(data, "has_cancer")
pipeline.train_model("RandomForest", X_train, y_train, X_val, y_val)
```

### 3. استفاده از CDS

```python
from app.services.cds.risk_predictor import RiskPredictor

predictor = RiskPredictor()
risk = predictor.calculate_risk_score({
    "age": 65,
    "gender": "Male",
    "smoking": True,
    "gerd": True
})
```

### 4. API Usage

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure_password"

# Generate synthetic data
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"n_patients": 100, "cancer_ratio": 0.3}'

# Risk prediction
curl -X POST "http://localhost:8000/api/v1/cds/risk-prediction" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"patient_data": {"age": 65, "gender": "Male", "smoking": true}}'
```

## 📚 مستندات

- [Quick Start Guide](QUICK_START.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [User Manual](docs/USER_MANUAL.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Training Materials](docs/TRAINING_MATERIALS.md)
- **[MLOps Features Guide](docs/MLOPS_FEATURES.md)** - راهنمای کامل ویژگی‌های MLOps
- **[MLOps Setup Guide](MLOPS_SETUP_GUIDE.md)** - راهنمای راه‌اندازی MLOps

### فازهای تکمیل شده

- ✅ [فاز 1: زیرساخت و پایه‌گذاری](PHASE1_COMPLETION.md)
- ✅ [فاز 2: تولید داده سنتتیک](PHASE2_COMPLETION.md)
- ✅ [فاز 3: جمع‌آوری داده واقعی](PHASE3_COMPLETION.md)
- ✅ [فاز 4: یکپارچه‌سازی و پردازش](PHASE4_COMPLETION.md)
- ✅ [فاز 5: مدل‌های یادگیری ماشین](PHASE5_COMPLETION.md)
- ✅ [فاز 6: سیستم پشتیبانی تصمیم‌گیری بالینی](PHASE6_COMPLETION.md)
- ✅ [فاز 7: رابط کاربری و داشبورد](PHASE7_COMPLETION.md)
- ✅ [فاز 8: امنیت و اخلاقیات](PHASE8_COMPLETION.md)
- ✅ [فاز 9: استقرار و بهینه‌سازی](PHASE9_COMPLETION.md)
- ✅ [فاز 10: تست و پذیرش نهایی](PHASE10_COMPLETION.md)
- ✅ [فاز 11: نگهداری و بهبود مستمر](PHASE11_COMPLETION.md)

## 📖 API Documentation

API documentation در دسترس است:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

## 🧪 تست

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m performance
pytest -m security
```

## 🚢 استقرار

### Development

```bash
docker-compose up -d
```

### Production

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

برای جزئیات بیشتر، [Deployment Guide](DEPLOYMENT.md) را ببینید.

## 📊 Monitoring

- **Grafana:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090
- **System Health:** http://localhost:8000/api/v1/health

## 🔐 امنیت

- JWT authentication
- Role-based access control
- Data encryption
- Audit logging
- Ethical guidelines compliance

## 👥 نقش‌های کاربری

- **Data Scientist:** تولید داده، آموزش مدل
- **Clinical Researcher:** جمع‌آوری داده، آنالیز
- **Medical Oncologist:** استفاده از CDS
- **System Administrator:** مدیریت سیستم

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. Branch ایجاد کنید (`git checkout -b feature/AmazingFeature`)
3. Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request باز کنید

## ⚠️ وضعیت واقعی و محدودیت‌های شناخته‌شده

- پوشش تست‌های خودکار در حال حاضر حدود ۳۵٪ است، نه سطحی که ادعای «Production Ready» را به‌طور کامل توجیه کند.
- مشکل ایزوله‌سازی تست‌های rate limiter به‌تازگی برطرف شده است.
- رمزنگاری داده در حالت سکون (encryption-at-rest) فقط در سطح برخی فیلدهای حساس پیاده‌سازی شده و هنوز به همه فیلدهای حساس تعمیم نیافته است.
- خروجی مدل به فرمت ONNX/TensorRT صرفاً در مستندات به‌عنوان گام آینده ذکر شده و هنوز پیاده‌سازی نشده است.
- ممیزی کامل دسترس‌پذیری مطابق استاندارد WCAG انجام نشده؛ فقط یک بررسی هدفمند روی چند صفحه محدود صورت گرفته است.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 تماس

- **Email:** support@inescape.com
- **Documentation:** https://docs.inescape.com
- **Issues:** https://github.com/inescape/issues

## 🙏 تشکر

از تمام کسانی که در توسعه این پروژه مشارکت کرده‌اند، تشکر می‌کنیم.

---

**نسخه:** 1.0.0  
**وضعیت:** در حال توسعه فعال - نیازمند تکمیل پوشش تست و بررسی‌های امنیتی پیش از استقرار Production  
**آخرین به‌روزرسانی:** 2024-12-19
