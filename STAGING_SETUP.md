# راه‌اندازی محیط Staging - INEsCape

## 🎯 هدف

محیط Staging برای تست نهایی قبل از deployment به production استفاده می‌شود.

## 📋 پیش‌نیازها

- Docker Desktop
- Docker Compose
- Python 3.10+
- دسترسی به اینترنت (برای دانلود images)

## 🚀 راه‌اندازی سریع

### Windows PowerShell:

```powershell
# 1. کپی .env.staging
Copy-Item .env.staging .env.staging.local

# 2. ویرایش .env.staging.local و تغییر passwords

# 3. Deploy
.\scripts\deploy_staging.ps1
```

### Linux/Mac:

```bash
# 1. کپی .env.staging
cp .env.staging .env.staging.local

# 2. ویرایش .env.staging.local و تغییر passwords

# 3. Deploy
chmod +x scripts/deploy_staging.sh
./scripts/deploy_staging.sh
```

## ⚙️ تنظیمات

### فایل .env.staging

فایل `.env.staging` را ویرایش کنید و مقادیر زیر را تغییر دهید:

```env
# Security - مهم: این مقادیر را تغییر دهید!
STAGING_SECRET_KEY=your-strong-secret-key-here
STAGING_ENCRYPTION_KEY=your-encryption-key-here

# Database passwords
STAGING_POSTGRES_PASSWORD=strong-password-here
STAGING_MONGODB_PASSWORD=strong-password-here
STAGING_REDIS_PASSWORD=strong-password-here

# Grafana
STAGING_GRAFANA_PASSWORD=admin-password-here
```

## 🔧 دستورات

### Start Staging

```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Stop Staging

```bash
docker-compose -f docker-compose.staging.yml down
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.staging.yml logs -f

# Specific service
docker-compose -f docker-compose.staging.yml logs -f app
```

### Restart Service

```bash
docker-compose -f docker-compose.staging.yml restart app
```

### Access Services

- **API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Grafana:** http://localhost:3002
- **Prometheus:** http://localhost:9091
- **MinIO Console:** http://localhost:9003

## 🗄️ Database Management

### Backup Database

```bash
# PostgreSQL
docker-compose -f docker-compose.staging.yml exec postgres pg_dump -U inescape_staging_user inescape_staging > backup.sql

# MongoDB
docker-compose -f docker-compose.staging.yml exec mongodb mongodump --out /backup
```

### Restore Database

```bash
# PostgreSQL
docker-compose -f docker-compose.staging.yml exec -T postgres psql -U inescape_staging_user inescape_staging < backup.sql

# MongoDB
docker-compose -f docker-compose.staging.yml exec mongodb mongorestore /backup
```

## 🔄 Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.staging.yml exec app alembic upgrade head

# Create new migration
docker-compose -f docker-compose.staging.yml exec app alembic revision --autogenerate -m "description"

# Rollback
docker-compose -f docker-compose.staging.yml exec app alembic downgrade -1
```

## 🧪 Testing in Staging

### Run Tests

```bash
docker-compose -f docker-compose.staging.yml exec app pytest -v
```

### Load Testing

```bash
docker-compose -f docker-compose.staging.yml exec app python scripts/load_test.py --url http://localhost:8001
```

## 📊 Monitoring

### Grafana

1. باز کردن http://localhost:3002
2. Login با:
   - Username: `admin`
   - Password: (از .env.staging)

### Prometheus

1. باز کردن http://localhost:9091
2. Query metrics:
   - `up` - Service status
   - `http_requests_total` - Request count

## 🔒 Security Checklist

- [ ] تغییر `STAGING_SECRET_KEY`
- [ ] تغییر `STAGING_ENCRYPTION_KEY`
- [ ] تغییر database passwords
- [ ] تغییر Redis password
- [ ] تغییر Grafana password
- [ ] بررسی CORS settings
- [ ] بررسی firewall rules
- [ ] Enable SSL/TLS (برای production)

## 🐛 Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs

# Check service status
docker-compose -f docker-compose.staging.yml ps

# Restart services
docker-compose -f docker-compose.staging.yml restart
```

### Database connection errors

```bash
# Check database health
docker-compose -f docker-compose.staging.yml exec postgres pg_isready -U inescape_staging_user

# Check MongoDB
docker-compose -f docker-compose.staging.yml exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Port conflicts

اگر port‌ها در حال استفاده هستند، در `.env.staging` تغییر دهید:
- `API_PORT=8002` (و در docker-compose.staging.yml)
- `PROMETHEUS_PORT=9092`
- `GRAFANA_PORT=3003`

## 📝 Notes

- Staging environment از database جداگانه استفاده می‌کند
- Ports متفاوت از development و production
- Logs در `./logs/staging` ذخیره می‌شوند
- Data در `./data/staging` ذخیره می‌شود

## 🔗 Resources

- [Development Setup](DEVELOPMENT_SETUP.md)
- [Production Deployment](DEPLOYMENT.md)
- [Testing Guide](TESTING_GUIDE.md)

---

**برای راه‌اندازی:** `.\scripts\deploy_staging.ps1` (Windows) یا `./scripts/deploy_staging.sh` (Linux/Mac)

