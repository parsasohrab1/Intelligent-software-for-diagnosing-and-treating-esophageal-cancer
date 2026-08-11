# 🚀 شروع کنید - INEsCape MVP

## خوش آمدید!

این فایل راهنمای سریع برای شروع کار با INEsCape MVP است.

## ⚡ شروع سریع (5 دقیقه)

### 1. نصب پیش‌نیازها

```bash
# بررسی نسخه‌ها
python --version  # باید 3.11+ باشد
docker --version
```

### 2. راه‌اندازی

```bash
# Clone و نصب
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
pip install -r requirements.txt

# راه‌اندازی services
docker-compose up -d

# Initialize
python scripts/init_database.py
python scripts/create_admin_user.py --username admin --email admin@example.com --password admin123

# Start server
python scripts/run_server.py
```

### 3. تست

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API Documentation
# باز کردن http://localhost:8000/docs در browser
```

## 📚 مستندات

### برای شروع سریع:
- **[QUICK_START_MVP.md](QUICK_START_MVP.md)** - راهنمای 5 دقیقه‌ای
- **[MVP_GUIDE.md](MVP_GUIDE.md)** - راهنمای کامل MVP

### برای استفاده:
- **[README.md](README.md)** - مستندات اصلی
- **[docs/USER_MANUAL.md](docs/USER_MANUAL.md)** - راهنمای کاربر
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - مستندات API

### برای استقرار:
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - راهنمای استقرار
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - راهنمای کامل

## 🎯 قابلیت‌های MVP

✅ تولید داده سنتتیک  
✅ مدل‌های ML (Random Forest, Logistic Regression)  
✅ پشتیبانی تصمیم‌گیری بالینی  
✅ رابط کاربری وب  
✅ امنیت و authentication  

## 🔑 دسترسی

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (اگر نصب شده)

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 🎮 مثال استفاده

```python
# تولید داده
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
generator = EsophagealCancerSyntheticData()
data = generator.generate_complete_dataset(n_patients=100)

# پیش‌بینی ریسک
from app.services.cds.risk_predictor import RiskPredictor
predictor = RiskPredictor()
risk = predictor.calculate_risk_score({"age": 65, "gender": "Male", "smoking": True})
```

## 📞 کمک

- مستندات: `docs/` directory
- Issues: Create issue in repository
- Email: support@inescape.com

---

**آماده شروع هستید؟** [QUICK_START_MVP.md](QUICK_START_MVP.md) را ببینید! 🚀
