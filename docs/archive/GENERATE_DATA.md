# راهنمای تولید داده بیماران

## مشکل: هیچ بیماری یافت نشد

اگر در صفحه Patients پیام "هیچ بیماری یافت نشد" را می‌بینید، باید داده تولید کنید.

## مراحل راه‌اندازی

### مرحله 1: Docker Desktop را باز کنید
- Docker Desktop را از Start Menu اجرا کنید
- منتظر بمانید تا کاملاً راه‌اندازی شود (آیکون Docker در system tray سبز شود)

### مرحله 2: PostgreSQL را راه‌اندازی کنید
```powershell
docker-compose up -d postgres
```

**نکته:** 30 ثانیه صبر کنید تا PostgreSQL کاملاً آماده شود.

### مرحله 3: دیتابیس را Initialize کنید
```powershell
python scripts/init_database.py
```

این دستور جداول دیتابیس را ایجاد می‌کند.

### مرحله 4: داده تولید کنید

**روش 1 (پیشنهادی):**
```powershell
python scripts/generate_and_display_mri_data.py
```

این اسکریپت:
- 50 بیمار تولید می‌کند
- 40% از بیماران سرطان دارند
- شامل داده‌های MRI می‌شود
- داده‌ها را در دیتابیس ذخیره می‌کند

**روش 2 (از API):**
```powershell
# با استفاده از PowerShell
$body = @{
    n_patients = 50
    cancer_ratio = 0.4
    save_to_db = $true
    seed = 42
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/v1/synthetic-data/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**روش 3 (از Frontend):**
- به صفحه "Data Generation" بروید
- تعداد بیماران را وارد کنید
- روی "Generate Data" کلیک کنید

## بررسی داده‌ها

پس از تولید داده، می‌توانید بررسی کنید:

```powershell
# بررسی تعداد بیماران
python -c "import requests; r = requests.get('http://localhost:8001/api/v1/patients/'); print(f'Patients: {len(r.json())}')"
```

یا مستقیماً در Frontend:
- به صفحه "Patients" بروید
- لیست بیماران باید نمایش داده شود

## مشکلات رایج

### خطا: "Docker Desktop is not running"
**راه‌حل:** Docker Desktop را باز کنید و منتظر بمانید تا راه‌اندازی شود.

### خطا: "Connection refused" در PostgreSQL
**راه‌حل:** 
1. بررسی کنید Docker Desktop در حال اجرا است
2. `docker-compose up -d postgres` را دوباره اجرا کنید
3. 30 ثانیه صبر کنید

### خطا: "Table does not exist"
**راه‌حل:** 
```powershell
python scripts/init_database.py
```

### داده تولید شد اما نمایش داده نمی‌شود
**راه‌حل:**
1. Backend را restart کنید
2. Frontend را refresh کنید (Ctrl+F5)
3. بررسی کنید که Backend به PostgreSQL متصل است

## دستورات سریع

```powershell
# راه‌اندازی کامل (اگر همه چیز آماده است)
docker-compose up -d postgres
Start-Sleep -Seconds 30
python scripts/init_database.py
python scripts/generate_and_display_mri_data.py
```

## نتیجه

پس از انجام این مراحل:
- ✅ 50 بیمار در دیتابیس ذخیره می‌شود
- ✅ صفحه Patients لیست بیماران را نمایش می‌دهد
- ✅ Dashboard آمار بیماران را نمایش می‌دهد

