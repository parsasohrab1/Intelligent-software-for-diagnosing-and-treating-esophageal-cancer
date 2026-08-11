# راهنمای MVP - INEsCape

## 🎯 MVP چیست؟

MVP (Minimum Viable Product) نسخه حداقلی از INEsCape است که شامل قابلیت‌های اصلی برای استفاده اولیه می‌باشد.

## ✨ قابلیت‌های MVP

### ✅ شامل شده

1. **تولید داده سنتتیک**
   - تولید 100-1000 نمونه داده
   - Validation اولیه
   - Export به CSV

2. **مدل‌های ML پایه**
   - Random Forest
   - Logistic Regression
   - Training و evaluation

3. **CDS پایه**
   - Risk prediction
   - Treatment recommendations
   - Prognostic scoring

4. **رابط کاربری**
   - Dashboard
   - Data generation interface
   - CDS interface

5. **امنیت پایه**
   - Authentication
   - RBAC
   - Audit logging

### ⏳ خارج از MVP (برای نسخه‌های بعدی)

- جمع‌آوری داده واقعی از TCGA/GEO
- مدل‌های پیشرفته (Neural Networks)
- Clinical trial matching
- Advanced analytics
- Mobile app

## 🚀 راه‌اندازی سریع MVP

### گام 1: نصب پیش‌نیازها

```bash
# Python 3.11+
python --version

# Docker & Docker Compose
docker --version
docker-compose --version
```

### گام 2: Clone و Setup

```bash
# Clone repository
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer

# Install dependencies
pip install -r requirements.txt
```

### گام 3: راه‌اندازی Services

```bash
# Start Docker services
docker-compose up -d

# Wait for services to be ready
python scripts/check_services.py

# Initialize database
python scripts/init_database.py
```

### گام 4: ایجاد Admin User

```bash
python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password admin123
```

### گام 5: راه‌اندازی Backend

```bash
# Start FastAPI server
python scripts/run_server.py

# یا با uvicorn مستقیم
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### گام 6: راه‌اندازی Frontend (اختیاری)

```bash
cd frontend
npm install
npm run dev
```

## 🎮 استفاده از MVP

### سناریو 1: تولید داده سنتتیک

```bash
# از طریق API
curl -X POST "http://localhost:8000/api/v1/synthetic-data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "n_patients": 100,
    "cancer_ratio": 0.3,
    "seed": 42,
    "save_to_db": false
  }'

# یا از طریق Python
python scripts/generate_synthetic_data.py \
  --n-patients 100 \
  --cancer-ratio 0.3 \
  --output synthetic_data.csv
```

### سناریو 2: آموزش مدل

```bash
# از طریق API
curl -X POST "http://localhost:8000/api/v1/ml-models/train" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "synthetic_data.csv",
    "target_column": "has_cancer",
    "model_type": "RandomForest"
  }'

# یا از طریق Python
python scripts/train_model.py \
  --data synthetic_data.csv \
  --target has_cancer \
  --model RandomForest
```

### سناریو 3: استفاده از CDS

```bash
# Risk Prediction
curl -X POST "http://localhost:8000/api/v1/cds/risk-prediction" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_data": {
      "age": 65,
      "gender": "Male",
      "smoking": true,
      "gerd": true
    }
  }'

# Treatment Recommendation
curl -X POST "http://localhost:8000/api/v1/cds/treatment-recommendation" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_data": {"age": 65, "gender": "Male"},
    "cancer_data": {"t_stage": "T3", "n_stage": "N1", "m_stage": "M0"}
  }'
```

### سناریو 4: استفاده از Frontend

1. باز کردن http://localhost:3000
2. Login با credentials
3. استفاده از Dashboard
4. تولید داده از Data Generation page
5. استفاده از CDS از CDS page

## 📊 Demo Workflow

### کامل Workflow برای MVP

```python
# 1. Import libraries
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.ml_training import MLTrainingPipeline
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender

# 2. Generate synthetic data
generator = EsophagealCancerSyntheticData()
data = generator.generate_complete_dataset(n_patients=500, cancer_ratio=0.3)
data.to_csv("mvp_data.csv", index=False)

# 3. Train ML model
pipeline = MLTrainingPipeline(experiment_name="mvp_experiment")
X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(
    data, "has_cancer"
)
pipeline.train_model("RandomForest", X_train, y_train, X_val, y_val)

# 4. Evaluate model
metrics = pipeline.evaluate_model("RandomForest", X_test, y_test)
print(f"Accuracy: {metrics['accuracy']:.3f}")
print(f"ROC AUC: {metrics.get('roc_auc', 0):.3f}")

# 5. Use CDS
predictor = RiskPredictor()
risk = predictor.calculate_risk_score({
    "age": 65,
    "gender": "Male",
    "smoking": True,
    "gerd": True
})
print(f"Risk Score: {risk['risk_score']:.3f}")
print(f"Risk Category: {risk['risk_category']}")

recommender = TreatmentRecommender()
treatments = recommender.recommend_treatment(
    {"age": 65, "gender": "Male"},
    {"t_stage": "T3", "n_stage": "N1", "m_stage": "M0"}
)
print(f"Found {len(treatments['recommendations'])} treatment recommendations")
```

## 🧪 تست MVP

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Run tests
pytest tests/ -v

# Load test
python scripts/load_test.py \
  --url http://localhost:8000 \
  --endpoint /api/v1/health \
  --requests 100 \
  --concurrency 10
```

## 📈 معیارهای موفقیت MVP

- ✅ System health check passing
- ✅ Synthetic data generation working
- ✅ ML model training successful
- ✅ CDS predictions accurate
- ✅ API response time < 2s
- ✅ Frontend accessible
- ✅ Authentication working

## 🔧 Troubleshooting MVP

### مشکل: Services شروع نمی‌شوند

```bash
# Check Docker
docker ps

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### مشکل: Database connection failed

```bash
# Check PostgreSQL
python scripts/check_services.py

# Reinitialize
python scripts/init_database.py
```

### مشکل: API errors

```bash
# Check server logs
tail -f logs/app.log

# Test health endpoint
curl http://localhost:8000/api/v1/health
```

## 📝 Next Steps بعد از MVP

1. **جمع‌آوری داده واقعی:** اتصال به TCGA/GEO
2. **مدل‌های پیشرفته:** Neural Networks, Transfer Learning
3. **Advanced CDS:** Clinical trial matching, Nanosystem design
4. **Analytics:** Advanced visualizations, Reports
5. **Mobile App:** iOS/Android applications

## 🎉 خلاصه MVP

MVP شامل:
- ✅ تولید داده سنتتیک
- ✅ مدل‌های ML پایه
- ✅ CDS پایه
- ✅ رابط کاربری
- ✅ امنیت

**MVP آماده استفاده است!** 🚀

