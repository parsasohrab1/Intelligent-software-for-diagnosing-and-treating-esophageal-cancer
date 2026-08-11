# ⚡ راه‌اندازی سریع Staging

## 🚀 در 3 مرحله

### مرحله 1: تنظیم Environment Variables

```powershell
# Windows
Copy-Item .env.staging .env.staging.local
# سپس .env.staging.local را ویرایش کنید و passwords را تغییر دهید
```

```bash
# Linux/Mac
cp .env.staging .env.staging.local
# سپس .env.staging.local را ویرایش کنید
```

### مرحله 2: Deploy

**Windows:**
```powershell
.\scripts\deploy_staging.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/deploy_staging.sh
./scripts/deploy_staging.sh
```

### مرحله 3: بررسی

باز کردن در browser:
- **API:** http://localhost:8001/api/v1/health
- **API Docs:** http://localhost:8001/docs
- **Grafana:** http://localhost:3002
- **Prometheus:** http://localhost:9091

## ✅ بررسی سریع

```bash
# Check services
docker-compose -f docker-compose.staging.yml ps

# Check logs
docker-compose -f docker-compose.staging.yml logs -f app

# Health check
curl http://localhost:8001/api/v1/health
```

## 🔧 دستورات مفید

```bash
# Start
docker-compose -f docker-compose.staging.yml up -d

# Stop
docker-compose -f docker-compose.staging.yml down

# Restart
docker-compose -f docker-compose.staging.yml restart

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

## ⚠️ نکات مهم

1. **Passwords را تغییر دهید!**
2. **Secret keys را تغییر دهید!**
3. **Ports را بررسی کنید** (8001, 9091, 3002)
4. **Docker Desktop باید در حال اجرا باشد**

---

**برای اطلاعات بیشتر:** [STAGING_SETUP.md](STAGING_SETUP.md)

