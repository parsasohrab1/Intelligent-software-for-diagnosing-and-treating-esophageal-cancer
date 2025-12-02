# ✅ چک‌لیست MVP

## پیش از شروع

- [ ] Docker نصب شده
- [ ] Python 3.11+ نصب شده
- [ ] Git repository clone شده
- [ ] Dependencies نصب شده (`pip install -r requirements.txt`)

## راه‌اندازی

- [ ] Docker services شروع شده (`docker-compose up -d`)
- [ ] Services healthy هستند (`python scripts/check_services.py`)
- [ ] Database initialized شده (`python scripts/init_database.py`)
- [ ] Admin user ایجاد شده (`python scripts/create_admin_user.py`)
- [ ] Server در حال اجرا است (`python scripts/run_server.py`)

## تست قابلیت‌ها

### تولید داده
- [ ] Health check passing (`curl http://localhost:8000/api/v1/health`)
- [ ] Synthetic data generation کار می‌کند
- [ ] Data validation موفق است

### ML Models
- [ ] Model training کار می‌کند
- [ ] Model evaluation موفق است
- [ ] Model registry کار می‌کند

### CDS
- [ ] Risk prediction کار می‌کند
- [ ] Treatment recommendations تولید می‌شود
- [ ] Prognostic scoring محاسبه می‌شود

### امنیت
- [ ] Authentication کار می‌کند
- [ ] RBAC اعمال می‌شود
- [ ] Audit logging فعال است

### Frontend (اختیاری)
- [ ] Frontend نصب شده
- [ ] Frontend در حال اجرا است
- [ ] Dashboard قابل دسترسی است

## تست‌ها

- [ ] Unit tests passing (`pytest tests/ -m unit`)
- [ ] Integration tests passing (`pytest tests/ -m integration`)
- [ ] Health checks passing

## مستندات

- [ ] README.md خوانده شده
- [ ] API documentation بررسی شده
- [ ] User manual بررسی شده

## آماده برای استفاده

- [ ] تمام چک‌لیست‌ها کامل شده
- [ ] System healthy است
- [ ] Documentation بررسی شده

---

**وضعیت:** ⬜ در حال انجام | ✅ تکمیل شده | ❌ مشکل دارد
