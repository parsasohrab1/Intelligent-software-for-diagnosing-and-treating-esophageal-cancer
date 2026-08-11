# راهنمای تست Staging Environment

## 🧪 تست Staging Environment

### پیش‌نیازها

1. ✅ Docker Desktop در حال اجرا باشد
2. ✅ فایل `.env.staging` موجود باشد
3. ✅ Ports آزاد باشند (8001, 9091, 3002, 9002, 9003)

## 🚀 روش‌های تست

### روش 1: استفاده از Test Script (توصیه می‌شود)

#### Windows PowerShell:

```powershell
.\scripts\test_staging.ps1
```

#### Linux/Mac:

```bash
chmod +x scripts/test_staging.sh
./scripts/test_staging.sh
```

### روش 2: تست دستی

#### 1. راه‌اندازی Services

```bash
# Start services
docker-compose -f docker-compose.staging.yml up -d

# Wait for services
timeout /t 30  # Windows
# یا
sleep 30  # Linux/Mac
```

#### 2. بررسی وضعیت Services

```bash
# Check service status
docker-compose -f docker-compose.staging.yml ps

# Check logs
docker-compose -f docker-compose.staging.yml logs -f
```

#### 3. تست Health Endpoint

```bash
# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8001/api/v1/health" -UseBasicParsing

# Linux/Mac
curl http://localhost:8001/api/v1/health
```

#### 4. تست API Documentation

```bash
# Open in browser
start http://localhost:8001/docs  # Windows
# یا
open http://localhost:8001/docs  # Mac
```

#### 5. تست Database Connections

```bash
# PostgreSQL
docker-compose -f docker-compose.staging.yml exec postgres pg_isready -U inescape_staging_user

# MongoDB
docker-compose -f docker-compose.staging.yml exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker-compose -f docker-compose.staging.yml exec redis redis-cli ping
```

## ✅ Checklist تست

### Services
- [ ] تمام services start شده‌اند
- [ ] تمام services healthy هستند
- [ ] هیچ service ای failed نشده

### API
- [ ] Health endpoint پاسخ می‌دهد (200 OK)
- [ ] API docs accessible است
- [ ] OpenAPI schema accessible است
- [ ] Root endpoint کار می‌کند

### Databases
- [ ] PostgreSQL ready است
- [ ] MongoDB ready است
- [ ] Redis ready است

### Monitoring
- [ ] Grafana accessible است (http://localhost:3002)
- [ ] Prometheus accessible است (http://localhost:9091)
- [ ] Metrics جمع‌آوری می‌شوند

### Storage
- [ ] MinIO accessible است (http://localhost:9003)

## 🔍 Troubleshooting

### Services شروع نمی‌شوند

```bash
# Check Docker
docker ps

# Check logs
docker-compose -f docker-compose.staging.yml logs

# Restart services
docker-compose -f docker-compose.staging.yml restart
```

### Port conflicts

```bash
# Find process using port
netstat -ano | findstr :8001  # Windows
# یا
lsof -i :8001  # Linux/Mac

# Kill process
taskkill /PID <PID> /F  # Windows
# یا
kill -9 <PID>  # Linux/Mac
```

### Database connection errors

```bash
# Check database logs
docker-compose -f docker-compose.staging.yml logs postgres
docker-compose -f docker-compose.staging.yml logs mongodb

# Restart database
docker-compose -f docker-compose.staging.yml restart postgres
```

### API not responding

```bash
# Check app logs
docker-compose -f docker-compose.staging.yml logs app

# Check app health
docker-compose -f docker-compose.staging.yml exec app curl http://localhost:8000/api/v1/health

# Restart app
docker-compose -f docker-compose.staging.yml restart app
```

## 📊 Expected Results

### Health Endpoint Response

```json
{
  "status": "ok"
}
```

### Service Status

```
NAME                          STATUS
inescape-app-staging          Up (healthy)
inescape-postgres-staging     Up (healthy)
inescape-mongodb-staging      Up (healthy)
inescape-redis-staging        Up (healthy)
inescape-minio-staging        Up
inescape-prometheus-staging   Up
inescape-grafana-staging      Up
```

## 🎯 Next Steps

بعد از تست موفق:

1. ✅ بررسی logs برای errors
2. ✅ تست API endpoints مختلف
3. ✅ بررسی monitoring dashboards
4. ✅ تست database operations
5. ✅ تست authentication

---

**برای تست سریع:** `.\scripts\test_staging.ps1` (Windows) یا `./scripts/test_staging.sh` (Linux/Mac)

