# Coverage Dashboard - راهنمای رفع مشکل

## ✅ وضعیت فعلی

- **Coverage Report:** تولید شده ✅
- **Total Coverage:** 46%
- **Files:** 86 فایل HTML
- **Data Files:** همه موجود هستند

## 📊 فایل‌های موجود

1. **htmlcov/index.html** - صفحه اصلی dashboard
2. **htmlcov/status.json** - داده‌های coverage
3. **htmlcov/coverage_html_cb_497bf287.js** - JavaScript برای نمایش
4. **htmlcov/style_cb_dca529e9.css** - استایل‌ها

## 🔧 راه‌حل‌های رفع مشکل

### اگر داده‌ها نمایش داده نمی‌شوند:

1. **Hard Refresh مرورگر:**
   - Windows: `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

2. **بررسی Console مرورگر:**
   - باز کردن Developer Tools (F12)
   - بررسی Console برای خطاها
   - بررسی Network tab برای فایل‌های missing

3. **باز کردن مستقیم فایل:**
   ```bash
   # Windows
   start htmlcov/index.html
   
   # یا از File Explorer
   # Navigate to htmlcov folder
   # Double-click index.html
   ```

4. **استفاده از HTTP Server:**
   ```bash
   # Server در حال اجرا است
   http://localhost:8000
   
   # یا اجرای مجدد:
   python scripts/view_coverage.py
   ```

5. **تولید مجدد Report:**
   ```bash
   # پاک کردن report قدیمی
   Remove-Item -Recurse -Force htmlcov
   
   # تولید مجدد
   pytest --cov=app --cov-report=html:htmlcov --cov-report=json:coverage.json
   
   # باز کردن
   start htmlcov/index.html
   ```

## 📈 بررسی داده‌ها

### بررسی status.json:
```python
import json
with open('htmlcov/status.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Files: {len(data['files'])}")
    # داده‌ها باید موجود باشند
```

### بررسی Coverage:
- Coverage کلی: 46%
- فایل‌های با coverage بالا: `synthetic_data_generator.py` (90%)
- فایل‌های با coverage پایین: `cds/` services (11-24%)

## 🚀 دستورات سریع

```bash
# تولید و باز کردن dashboard
python scripts/view_coverage.py

# یا دستی:
pytest --cov=app --cov-report=html:htmlcov
start htmlcov/index.html
```

## ✅ چک‌لیست

- [x] Coverage report تولید شده
- [x] فایل‌های HTML موجود هستند
- [x] status.json حاوی داده است
- [x] JavaScript و CSS موجود هستند
- [x] HTTP server در حال اجرا است

## 💡 نکات

1. **CORS Issues:** اگر از file:// استفاده می‌کنید، ممکن است JavaScript کار نکند. از HTTP server استفاده کنید.

2. **Browser Cache:** مرورگر ممکن است فایل‌های قدیمی را cache کرده باشد. Hard refresh کنید.

3. **File Paths:** اطمینان حاصل کنید که همه فایل‌ها در همان directory هستند.

4. **JavaScript Errors:** اگر JavaScript خطا می‌دهد، ممکن است فایل‌ها corrupt شده باشند. دوباره generate کنید.

## 📞 اگر مشکل حل نشد

1. بررسی کنید که همه فایل‌ها در `htmlcov/` موجود هستند
2. بررسی کنید که JavaScript در Console خطا نمی‌دهد
3. سعی کنید از مرورگر دیگری استفاده کنید
4. دوباره coverage report را generate کنید

