# ⚡ راه‌اندازی سریع Development

## 🎯 شروع در 3 مرحله

### مرحله 1: راه‌اندازی Docker Desktop

**⚠️ مهم:** Docker Desktop باید در حال اجرا باشد!

1. Docker Desktop را باز کنید
2. منتظر بمانید تا Docker engine شروع شود (آیکون Docker در system tray سبز شود)
3. بررسی کنید:

```bash
docker ps
```

اگر خطا داد، Docker Desktop را restart کنید.

### مرحله 2: راه‌اندازی Services

```bash
# Start all services
docker-compose up -d

# Wait 30 seconds for services to start
timeout /t 30

# Check services status
python scripts/check_services.py
```

### مرحله 3: Initialize و Start

```bash
# Initialize database
python scripts/init_database.py

# Create admin user
python scripts/create_admin_user.py --username admin --email admin@example.com --password admin123

# Start development server
python scripts/run_server.py
```

## ✅ بررسی

باز کردن در browser:
- **API:** http://localhost:8000/api/v1/health
- **API Docs:** http://localhost:8000/docs

## 🚀 یا استفاده از Script

### Windows PowerShell:

```powershell
.\scripts\start_dev.ps1
```

### Linux/Mac:

```bash
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh
```

## 🐛 مشکلات رایج

### Docker Desktop not running

```
Error: Cannot connect to Docker daemon
```

**راه‌حل:** Docker Desktop را باز کنید و منتظر بمانید تا شروع شود.

### Port already in use

```
Error: Address already in use
```

**راه‌حل:**
```bash
# Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in .env
API_PORT=8001
```

### Database connection failed

```
Error: connection refused
```

**راه‌حل:**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait and retry
python scripts/check_services.py
```

## 📝 Development Tips

### Hot Reload

Server با `--reload` flag به صورت خودکار reload می‌شود.

### API Testing

از Swagger UI استفاده کنید: http://localhost:8000/docs

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f app
```

---

**برای اطلاعات بیشتر:** [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)

