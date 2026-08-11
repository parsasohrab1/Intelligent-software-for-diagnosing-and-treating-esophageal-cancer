# راهنمای رفع خطای Startup

## خطا: Application startup failed

این خطا معمولاً به دلیل مشکل در اتصال به Database (PostgreSQL) رخ می‌دهد.

## علل احتمالی

1. **Docker services در حال اجرا نیستند**
2. **PostgreSQL container در حال اجرا نیست**
3. **PostgreSQL هنوز آماده نیست (در حال راه‌اندازی)**
4. **DATABASE_URL اشتباه است**
5. **فایل .env موجود نیست یا نادرست است**

## راه‌حل گام به گام

### Step 1: بررسی Docker

```powershell
# بررسی Docker Desktop
# باید Docker Desktop در حال اجرا باشد

# بررسی containers
docker ps

# باید PostgreSQL container را ببینید
```

### Step 2: راه‌اندازی Docker Services

```powershell
# راه‌اندازی تمام services
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# باید همه services "Up" باشند
```

### Step 3: منتظر بمانید

PostgreSQL نیاز به 10-15 ثانیه زمان دارد تا کاملاً راه‌اندازی شود.

```powershell
# بررسی logs
docker-compose logs postgres

# باید ببینید: "database system is ready to accept connections"
```

### Step 4: بررسی Database Connection

```powershell
# تست اتصال
python -c "from app.core.database import engine; conn = engine.connect(); print('OK'); conn.close()"
```

### Step 5: بررسی .env File

```powershell
# بررسی وجود .env
Get-Content .env

# باید DATABASE_URL داشته باشد:
# DATABASE_URL=postgresql://inescape_user:inescape_password@localhost:5432/inescape
```

### Step 6: راه‌اندازی Backend

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## استفاده از Script

```powershell
.\scripts\fix_startup_error.ps1
```

این script به صورت خودکار:
- Docker services را بررسی می‌کند
- .env file را بررسی می‌کند
- Database connection را تست می‌کند

## مشکلات رایج

### مشکل 1: "Connection refused"

**علت:** PostgreSQL در حال اجرا نیست

**راه‌حل:**
```powershell
docker-compose up -d
# منتظر بمانید 10-15 ثانیه
```

### مشکل 2: "Connection timeout"

**علت:** PostgreSQL هنوز آماده نیست

**راه‌حل:**
```powershell
# بررسی logs
docker-compose logs postgres

# منتظر بمانید تا ببینید:
# "database system is ready to accept connections"
```

### مشکل 3: "Authentication failed"

**علت:** Username/Password اشتباه است

**راه‌حل:**
```powershell
# بررسی .env file
Get-Content .env | Select-String DATABASE_URL

# باید با docker-compose.yml مطابقت داشته باشد
```

### مشکل 4: "Database does not exist"

**علت:** Database ایجاد نشده است

**راه‌حل:**
```powershell
# Database به صورت خودکار ایجاد می‌شود
# اما می‌توانید دستی ایجاد کنید:
docker-compose exec postgres psql -U inescape_user -c "CREATE DATABASE inescape;"
```

## Checklist

- [ ] Docker Desktop در حال اجرا است
- [ ] `docker-compose up -d` اجرا شده است
- [ ] PostgreSQL container در حال اجرا است (`docker ps`)
- [ ] PostgreSQL آماده است (logs را بررسی کنید)
- [ ] فایل `.env` موجود است
- [ ] `DATABASE_URL` در `.env` صحیح است
- [ ] 10-15 ثانیه صبر کرده‌اید

## دستورات مفید

```powershell
# بررسی وضعیت containers
docker-compose ps

# بررسی logs
docker-compose logs postgres

# Restart services
docker-compose restart

# Stop و Start مجدد
docker-compose down
docker-compose up -d

# بررسی connection
python -c "from app.core.database import engine; engine.connect()"
```

## اگر هنوز کار نمی‌کند

1. **Docker Desktop را restart کنید**
2. **تمام containers را stop و start کنید:**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```
3. **Logs را بررسی کنید:**
   ```powershell
   docker-compose logs
   ```
4. **Port را بررسی کنید:**
   ```powershell
   netstat -ano | findstr :5432
   ```

## نکات مهم

1. **همیشه ابتدا Docker را راه‌اندازی کنید**
2. **10-15 ثانیه صبر کنید** تا PostgreSQL آماده شود
3. **Logs را بررسی کنید** برای اطمینان از آماده بودن
4. **Backend را بعد از Docker راه‌اندازی کنید**

