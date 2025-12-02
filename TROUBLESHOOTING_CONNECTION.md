# Troubleshooting: ERR_CONNECTION_REFUSED

## مشکل: ERR_CONNECTION_REFUSED

اگر خطای `ERR_CONNECTION_REFUSED` می‌بینید، این به معنی است که:
- Server در حال اجرا نیست
- یا پورت در دسترس نیست

## راه‌حل‌های سریع

### 1. بررسی وضعیت Servers

```powershell
# بررسی پورت‌ها
Get-NetTCPConnection -LocalPort 8001  # Backend
Get-NetTCPConnection -LocalPort 3000  # Frontend

# بررسی processes
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" }
Get-Process node
```

### 2. راه‌اندازی Servers

#### Backend:
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

#### Frontend:
```powershell
cd frontend
npm run dev
```

یا از script استفاده کنید:
```powershell
.\scripts\start_all.ps1
```

### 3. بررسی Docker Services

Backend نیاز به Docker services دارد:

```powershell
# بررسی Docker services
docker ps

# راه‌اندازی Docker services
docker-compose up -d
```

### 4. بررسی Browser

1. **Hard Refresh:** `Ctrl + F5`
2. **Clear Cache:** `Ctrl + Shift + Delete`
3. **Incognito Mode:** `Ctrl + Shift + N`
4. **URL را دوباره تایپ کنید:** `http://localhost:3000`

### 5. بررسی Firewall

```powershell
# بررسی firewall rules
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Python*" -or $_.DisplayName -like "*Node*" }
```

## مشکلات رایج

### مشکل 1: Backend شروع نمی‌شود

**علل احتمالی:**
- Docker services در حال اجرا نیستند
- پورت 8001 توسط process دیگری استفاده می‌شود
- Dependencies نصب نشده‌اند

**راه‌حل:**
```powershell
# 1. بررسی Docker
docker ps

# 2. راه‌اندازی Docker
docker-compose up -d

# 3. بررسی پورت
netstat -ano | findstr :8001

# 4. توقف process (اگر لازم باشد)
taskkill /PID <PID> /F
```

### مشکل 2: Frontend شروع نمی‌شود

**علل احتمالی:**
- `node_modules` نصب نشده
- پورت 3000 در حال استفاده است
- خطا در `package.json`

**راه‌حل:**
```powershell
# 1. نصب dependencies
cd frontend
npm install

# 2. بررسی پورت
netstat -ano | findstr :3000

# 3. راه‌اندازی
npm run dev
```

### مشکل 3: Backend کار می‌کند اما Frontend نمی‌تواند به آن متصل شود

**علل احتمالی:**
- CORS issue
- API URL اشتباه است
- Backend روی پورت دیگری است

**راه‌حل:**
```powershell
# 1. بررسی API URL در frontend/.env
cat frontend/.env

# باید باشد:
# VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1

# 2. تست Backend
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"
```

## بررسی کامل

### Step 1: بررسی Services

```powershell
# Docker
docker ps

# Python/Uvicorn
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" }

# Node
Get-Process node
```

### Step 2: تست اتصال

```powershell
# Backend
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# Frontend
Invoke-WebRequest -Uri "http://localhost:3000"
```

### Step 3: بررسی Logs

```powershell
# Backend logs (در پنجره PowerShell)
# باید ببینید:
# INFO:     Uvicorn running on http://127.0.0.1:8001

# Frontend logs (در پنجره PowerShell)
# باید ببینید:
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:3000/
```

## راه‌اندازی کامل

### Option 1: استفاده از Script

```powershell
.\scripts\start_all.ps1
```

### Option 2: راه‌اندازی دستی

**Terminal 1 (Backend):**
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```

## URLs

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://127.0.0.1:8001/docs
- **Backend Health:** http://127.0.0.1:8001/api/v1/health

## نکات مهم

1. **همیشه از `http://` استفاده کنید** (نه `https://`)
2. **Backend روی `127.0.0.1` است** (نه `localhost`)
3. **Frontend روی `localhost` است**
4. **Docker services باید در حال اجرا باشند** برای Backend

## اگر هنوز کار نمی‌کند

1. تمام processes را توقف کنید
2. Docker services را restart کنید
3. Dependencies را دوباره نصب کنید
4. Logs را بررسی کنید
5. از script استفاده کنید: `.\scripts\start_all.ps1`

