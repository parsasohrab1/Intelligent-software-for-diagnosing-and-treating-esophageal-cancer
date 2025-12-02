# راهنمای اتصال به Backend

## ⚠️ مشکل: خطای SSL

اگر خطای زیر را می‌بینید:
```
Bad Request: You're speaking plain HTTP to an SSL-enabled server port
```

این به این معنی است که:
- پورت 8000 توسط یک service دیگر (احتمالاً Apache/httpd) استفاده می‌شود
- آن service انتظار HTTPS دارد

## ✅ راه‌حل

### راه‌حل 1: استفاده از پورت 8001 (پیشنهادی)

Backend روی پورت **8001** راه‌اندازی شده است:

```powershell
# راه‌اندازی server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**دسترسی:**
- API Docs: http://127.0.0.1:8001/docs
- Health: http://127.0.0.1:8001/api/v1/health
- Monitoring: http://127.0.0.1:8001/api/v1/monitoring/normal-ranges

### راه‌حل 2: توقف Apache/httpd (نیاز به Admin)

اگر می‌خواهید از پورت 8000 استفاده کنید:

```powershell
# توقف Apache (نیاز به Admin rights)
# در PowerShell با Run as Administrator:
Stop-Service -Name "Apache2.4" -ErrorAction SilentlyContinue
# یا
net stop Apache2.4
```

سپس:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### راه‌حل 3: استفاده از Script

```powershell
.\scripts\start_backend.ps1
```

این script به صورت خودکار پورت مناسب را انتخاب می‌کند.

## 🔧 تنظیمات Frontend

اگر از پورت 8001 استفاده می‌کنید، فایل `frontend/.env` را ایجاد کنید:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

یا در `frontend/src/services/api.ts` تغییر دهید:

```typescript
const api = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  // ...
})
```

## 📝 نکات مهم

1. **همیشه از http:// استفاده کنید** (نه https://)
   - ✅ صحیح: `http://127.0.0.1:8001/docs`
   - ❌ اشتباه: `https://127.0.0.1:8001/docs`

2. **Browser Cache را پاک کنید:**
   - Ctrl + Shift + Delete
   - یا Hard Refresh: Ctrl + F5

3. **Proxy Settings:**
   - اگر از proxy استفاده می‌کنید، آن را غیرفعال کنید
   - یا proxy را برای localhost bypass کنید

4. **Firewall:**
   - مطمئن شوید که firewall پورت 8001 را block نمی‌کند

## 🧪 تست اتصال

```powershell
# تست Health endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health"

# یا با curl
curl http://127.0.0.1:8001/api/v1/health
```

## 🌐 URL های مهم

بعد از راه‌اندازی:

- **API Documentation:** http://127.0.0.1:8001/docs
- **ReDoc:** http://127.0.0.1:8001/redoc
- **Health Check:** http://127.0.0.1:8001/api/v1/health
- **Normal Ranges:** http://127.0.0.1:8001/api/v1/monitoring/normal-ranges
- **MRI API:** http://127.0.0.1:8001/api/v1/imaging/mri
- **Patient Monitoring:** http://127.0.0.1:8001/api/v1/monitoring/patients/{id}/monitoring

## 🔍 Troubleshooting

### مشکل: هنوز خطای SSL می‌بینم

1. مطمئن شوید از `http://` استفاده می‌کنید
2. Browser cache را پاک کنید
3. از Incognito/Private mode استفاده کنید
4. URL را مستقیماً در address bar تایپ کنید

### مشکل: Connection Refused

1. بررسی کنید server در حال اجرا است:
   ```powershell
   netstat -ano | findstr :8001
   ```

2. Server را دوباره راه‌اندازی کنید:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
   ```

### مشکل: Port در حال استفاده است

```powershell
# پیدا کردن process
netstat -ano | findstr :8001

# توقف process (با Admin rights)
taskkill /PID <PID> /F
```

