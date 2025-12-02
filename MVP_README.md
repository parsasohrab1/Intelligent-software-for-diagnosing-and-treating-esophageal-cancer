# 🚀 INEsCape MVP - راهنمای کامل

## 🎯 MVP چیست؟

**Minimum Viable Product (MVP)** نسخه حداقلی و قابل استفاده از INEsCape است که شامل تمام قابلیت‌های اصلی برای شروع کار می‌باشد.

## ✨ قابلیت‌های MVP

### ✅ شامل شده در MVP

1. **🔬 تولید داده سنتتیک**
   - تولید 100-1000 نمونه داده واقع‌گرا
   - Validation خودکار
   - Export به CSV/JSON

2. **🤖 مدل‌های یادگیری ماشین**
   - Random Forest
   - Logistic Regression
   - Training و evaluation
   - Model registry

3. **🏥 پشتیبانی تصمیم‌گیری بالینی (CDS)**
   - پیش‌بینی ریسک سرطان
   - پیشنهادات درمانی
   - امتیازدهی پیش‌آگهی

4. **🎨 رابط کاربری وب**
   - Dashboard تعاملی
   - Interface برای تولید داده
   - Interface برای CDS

5. **🔒 امنیت پایه**
   - Authentication با JWT
   - Role-based access control
   - Audit logging

## 🚀 نصب و راه‌اندازی سریع

### پیش‌نیازها

```bash
# بررسی نسخه‌ها
python --version  # باید 3.11+ باشد
docker --version
docker-compose --version
```

### نصب در 5 دقیقه

```bash
# 1. Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up -d

# 4. Wait for services (30 seconds)
sleep 30

# 5. Initialize
python scripts/init_database.py
python scripts/create_admin_user.py --username admin --email admin@example.com --password admin123

# 6. Start server
python scripts/run_server.py
```

### دسترسی

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (اگر نصب شده)

## 🎮 استفاده از MVP

### مثال 1: تولید داده سنتتیک

```python
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData

generator = EsophagealCancerSyntheticData()
data = generator.generate_complete_dataset(n_patients=100, cancer_ratio=0.3)
data.to_csv("data.csv", index=False)
print(f"Generated {len(data)} patients")
```

### مثال 2: آموزش مدل

```python
from app.services.ml_training import MLTrainingPipeline
import pandas as pd

# Load data
data = pd.read_csv("data.csv")

# Train model
pipeline = MLTrainingPipeline()
X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(data, "has_cancer")
pipeline.train_model("RandomForest", X_train, y_train, X_val, y_val)

# Evaluate
metrics = pipeline.evaluate_model("RandomForest", X_test, y_test)
print(f"Accuracy: {metrics['accuracy']:.3f}")
```

### مثال 3: استفاده از CDS

```python
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender

# Risk prediction
predictor = RiskPredictor()
risk = predictor.calculate_risk_score({
    "age": 65,
    "gender": "Male",
    "smoking": True,
    "gerd": True
})
print(f"Risk Score: {risk['risk_score']:.3f}")

# Treatment recommendation
recommender = TreatmentRecommender()
treatments = recommender.recommend_treatment(
    {"age": 65, "gender": "Male"},
    {"t_stage": "T3", "n_stage": "N1", "m_stage": "M0"}
)
print(f"Found {len(treatments['recommendations'])} recommendations")
```

### مثال 4: استفاده از API

```bash
# 1. Login
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Generate data
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"n_patients": 100, "cancer_ratio": 0.3}'

# 3. Risk prediction
curl -X POST "http://localhost:8000/api/v1/cds/risk-prediction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_data": {"age": 65, "gender": "Male", "smoking": true}}'
```

## 📊 Demo Workflow کامل

```python
# Complete MVP workflow
import pandas as pd
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.ml_training import MLTrainingPipeline
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender

print("=== INEsCape MVP Demo ===\n")

# Step 1: Generate synthetic data
print("1. Generating synthetic data...")
generator = EsophagealCancerSyntheticData()
data = generator.generate_complete_dataset(n_patients=500, cancer_ratio=0.3)
print(f"   ✅ Generated {len(data)} patients")
print(f"   ✅ Cancer patients: {data['has_cancer'].sum()}")
print(f"   ✅ Normal patients: {(~data['has_cancer']).sum()}\n")

# Step 2: Train ML model
print("2. Training ML model...")
pipeline = MLTrainingPipeline(experiment_name="mvp_demo")
X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(
    data, "has_cancer"
)
pipeline.train_model("RandomForest", X_train, y_train, X_val, y_val)
metrics = pipeline.evaluate_model("RandomForest", X_test, y_test)
print(f"   ✅ Model trained")
print(f"   ✅ Accuracy: {metrics['accuracy']:.3f}")
print(f"   ✅ ROC AUC: {metrics.get('roc_auc', 0):.3f}\n")

# Step 3: Risk prediction
print("3. Risk prediction...")
predictor = RiskPredictor()
risk = predictor.calculate_risk_score({
    "age": 65,
    "gender": "Male",
    "smoking": True,
    "gerd": True,
    "barretts_esophagus": True
})
print(f"   ✅ Risk Score: {risk['risk_score']:.3f}")
print(f"   ✅ Risk Category: {risk['risk_category']}")
print(f"   ✅ Recommendation: {risk['recommendation']}\n")

# Step 4: Treatment recommendation
print("4. Treatment recommendation...")
recommender = TreatmentRecommender()
treatments = recommender.recommend_treatment(
    {"age": 65, "gender": "Male"},
    {
        "cancer_type": "adenocarcinoma",
        "t_stage": "T3",
        "n_stage": "N1",
        "m_stage": "M0",
        "pdl1_status": "Positive"
    }
)
print(f"   ✅ Found {len(treatments['recommendations'])} recommendations")
for i, rec in enumerate(treatments['recommendations'][:3], 1):
    print(f"   {i}. {rec['type']}: {rec['regimen']}")

print("\n=== Demo Complete ===")
```

## 🧪 تست MVP

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Run tests
pytest tests/ -v

# Load test
python scripts/load_test.py --url http://localhost:8000 --endpoint /api/v1/health
```

## 📈 معیارهای موفقیت MVP

- ✅ System health check passing
- ✅ Synthetic data generation working
- ✅ ML model training successful (Accuracy > 0.8)
- ✅ CDS predictions accurate
- ✅ API response time < 2s
- ✅ Frontend accessible (if installed)
- ✅ Authentication working

## 🔧 Troubleshooting

### مشکل: Services شروع نمی‌شوند

```bash
# Check Docker
docker ps

# Restart
docker-compose restart

# Check logs
docker-compose logs
```

### مشکل: Database connection failed

```bash
# Check services
python scripts/check_services.py

# Reinitialize
python scripts/init_database.py
```

### مشکل: Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 مستندات بیشتر

- [Quick Start Guide](QUICK_START_MVP.md) - راهنمای 5 دقیقه‌ای
- [Full README](README.md) - مستندات کامل
- [API Documentation](docs/API_DOCUMENTATION.md) - مستندات API
- [User Manual](docs/USER_MANUAL.md) - راهنمای کاربر
- [Deployment Guide](DEPLOYMENT.md) - راهنمای استقرار

## 🎯 Next Steps

بعد از MVP، می‌توانید:

1. **جمع‌آوری داده واقعی** از TCGA/GEO
2. **مدل‌های پیشرفته** (Neural Networks)
3. **Advanced CDS** (Clinical trial matching)
4. **Analytics** پیشرفته
5. **Mobile app**

## 🎉 خلاصه

MVP شامل:
- ✅ تولید داده سنتتیک
- ✅ مدل‌های ML پایه
- ✅ CDS پایه
- ✅ رابط کاربری
- ✅ امنیت

**MVP آماده استفاده است!** 🚀

---

**نسخه MVP:** 1.0.0  
**وضعیت:** ✅ Production Ready  
**تاریخ:** 2024-12-19
