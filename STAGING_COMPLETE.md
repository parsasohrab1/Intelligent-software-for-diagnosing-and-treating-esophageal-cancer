# ✅ Staging Environment Setup Complete

## 🎉 خلاصه

محیط Staging برای INEsCape با موفقیت راه‌اندازی شد.

## 📁 فایل‌های ایجاد شده

### Configuration Files
- ✅ `docker-compose.staging.yml` - Docker Compose configuration برای staging
- ✅ `.env.staging` - Environment variables برای staging
- ✅ `monitoring/prometheus.staging.yml` - Prometheus config برای staging

### Deployment Scripts
- ✅ `scripts/deploy_staging.sh` - Deployment script برای Linux/Mac
- ✅ `scripts/deploy_staging.ps1` - Deployment script برای Windows

### Documentation
- ✅ `STAGING_SETUP.md` - راهنمای کامل staging
- ✅ `STAGING_QUICK_START.md` - راهنمای سریع
- ✅ `STAGING_CHECKLIST.md` - Checklist برای deployment
- ✅ `STAGING_COMPLETE.md` - این فایل

## 🚀 ویژگی‌های Staging Environment

### Services
- **API:** Port 8001 (متفاوت از development)
- **PostgreSQL:** Database جداگانه (`inescape_staging`)
- **MongoDB:** Database جداگانه (`inescape_staging_metadata`)
- **Redis:** Instance جداگانه
- **MinIO:** Ports 9002/9003
- **Prometheus:** Port 9091
- **Grafana:** Port 3002

### Isolation
- ✅ Database جداگانه از development و production
- ✅ Ports متفاوت برای جلوگیری از conflict
- ✅ Volumes جداگانه برای data و logs
- ✅ Network جداگانه

## 📋 مراحل Deployment

### 1. تنظیم Environment Variables

```powershell
# ویرایش .env.staging و تغییر passwords
notepad .env.staging
```

**مهم:** این مقادیر را تغییر دهید:
- `STAGING_SECRET_KEY`
- `STAGING_ENCRYPTION_KEY`
- `STAGING_POSTGRES_PASSWORD`
- `STAGING_MONGODB_PASSWORD`
- `STAGING_REDIS_PASSWORD`
- `STAGING_GRAFANA_PASSWORD`

### 2. Deploy

**Windows:**
```powershell
.\scripts\deploy_staging.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/deploy_staging.sh
./scripts/deploy_staging.sh
```

### 3. بررسی

```bash
# Check services
docker-compose -f docker-compose.staging.yml ps

# Health check
curl http://localhost:8001/api/v1/health
```

## 🔗 دسترسی به Services

- **API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Grafana:** http://localhost:3002 (admin / password from .env.staging)
- **Prometheus:** http://localhost:9091
- **MinIO Console:** http://localhost:9003

## 🔧 دستورات مفید

### Start/Stop

```bash
# Start
docker-compose -f docker-compose.staging.yml up -d

# Stop
docker-compose -f docker-compose.staging.yml down

# Restart
docker-compose -f docker-compose.staging.yml restart
```

### Logs

```bash
# All services
docker-compose -f docker-compose.staging.yml logs -f

# Specific service
docker-compose -f docker-compose.staging.yml logs -f app
```

### Database

```bash
# Run migrations
docker-compose -f docker-compose.staging.yml exec app alembic upgrade head

# Create admin user
docker-compose -f docker-compose.staging.yml exec app python scripts/create_admin_user.py \
    --username admin --email admin@staging.example.com --password admin123
```

## ✅ Checklist

قبل از استفاده از staging:

- [ ] `.env.staging` ویرایش شده و passwords تغییر کرده‌اند
- [ ] Docker Desktop در حال اجرا است
- [ ] Ports آزاد هستند (8001, 9091, 3002, 9002, 9003)
- [ ] Services start شده‌اند
- [ ] Health check پاس شده
- [ ] Database initialized شده
- [ ] Admin user ایجاد شده

## 📚 مستندات

- [STAGING_SETUP.md](STAGING_SETUP.md) - راهنمای کامل
- [STAGING_QUICK_START.md](STAGING_QUICK_START.md) - راهنمای سریع
- [STAGING_CHECKLIST.md](STAGING_CHECKLIST.md) - Deployment checklist

## 🎯 Next Steps

1. **ویرایش `.env.staging`** و تغییر passwords
2. **اجرای deployment script**
3. **بررسی health check**
4. **تست API endpoints**
5. **بررسی monitoring dashboards**

---

**✅ Staging environment آماده است!**

برای شروع: `.\scripts\deploy_staging.ps1` (Windows) یا `./scripts/deploy_staging.sh` (Linux/Mac)

