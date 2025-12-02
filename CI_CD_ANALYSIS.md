# بررسی CI/CD Pipeline

## 📋 خلاصه

**وضعیت:** ✅ CI/CD Pipeline فعال است  
**فایل:** `.github/workflows/ci.yml`  
**Trigger:** Push به `main` یا `develop` branches

## 🔍 جزئیات Pipeline

### Workflow Name
`CI Pipeline`

### Triggers
- ✅ **Push** به branches: `main`, `develop`
- ✅ **Pull Request** به branches: `main`, `develop`

### Jobs

#### 1. Test Job
**Runner:** `ubuntu-latest`

**Services:**
- PostgreSQL 14 (برای تست‌ها)

**Steps:**
1. ✅ Checkout code
2. ✅ Set up Python 3.9
3. ✅ Install dependencies (`requirements.txt` و `requirements-dev.txt`)
4. ✅ Lint with flake8
5. ✅ Format check with black
6. ✅ Type check with mypy
7. ✅ Run tests with pytest + coverage
8. ✅ Upload coverage to codecov

**Environment Variables:**
- `DATABASE_URL`: `postgresql://test_user:test_password@localhost:5432/test_db`

#### 2. Build Job
**Runner:** `ubuntu-latest`  
**Depends on:** Test job (باید پاس شود)

**Steps:**
1. ✅ Checkout code
2. ✅ Set up Docker Buildx
3. ✅ Build Docker image (`inescape-api:latest`)

## ⚙️ Configuration Details

### Linting
```yaml
flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### Formatting
```yaml
black --check app/
```

### Type Checking
```yaml
mypy app/ --ignore-missing-imports
```

### Testing
```yaml
pytest tests/ --cov=app --cov-report=xml
```

### Coverage Upload
- Service: Codecov
- File: `./coverage.xml`
- Flags: `unittests`

## 🔗 لینک‌های مفید

- **GitHub Actions:** https://github.com/parsasohrab1/Intelligent-software-for-diagnosing-and-treating-esophageal-cancer/actions
- **Workflow File:** `.github/workflows/ci.yml`

## ⚠️ نکات مهم

### 1. Python Version
Pipeline از Python 3.9 استفاده می‌کند، اما پروژه ممکن است به Python 3.10 نیاز داشته باشد.

**توصیه:** به‌روزرسانی به Python 3.10:
```yaml
python-version: '3.10'
```

### 2. Dependencies
Pipeline نیاز به:
- `flake8` (برای linting)
- `black` (برای formatting)
- `mypy` (برای type checking)
- `pytest` و `pytest-cov` (برای testing)
- `codecov` (برای coverage upload)

**بررسی:** این dependencies در `requirements-dev.txt` موجود هستند؟

### 3. Database Services
Pipeline فقط PostgreSQL را setup می‌کند. اگر به MongoDB یا Redis نیاز دارید، باید اضافه شوند.

### 4. Coverage Upload
Codecov نیاز به token دارد. باید در repository secrets تنظیم شود.

## 🚀 بهبودهای پیشنهادی

### 1. اضافه کردن MongoDB و Redis Services
```yaml
services:
  mongodb:
    image: mongo:6
    ports:
      - 27017:27017
  
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
```

### 2. اضافه کردن Security Scanning
```yaml
- name: Security scan
  uses: github/super-linter@v4
```

### 3. اضافه کردن Build Artifacts
```yaml
- name: Upload build artifacts
  uses: actions/upload-artifact@v3
  with:
    name: docker-image
    path: inescape-api:latest
```

### 4. اضافه کردن Deployment Job (Optional)
```yaml
deploy:
  runs-on: ubuntu-latest
  needs: build
  if: github.ref == 'refs/heads/main'
  steps:
    - name: Deploy to staging
      run: |
        # Deployment commands
```

## 📊 وضعیت فعلی

### ✅ فعال
- CI Pipeline تعریف شده
- Trigger برای push و PR تنظیم شده
- Test و Build jobs تعریف شده

### ⚠️ نیاز به بررسی
- آیا workflow اجرا شده است؟
- آیا tests پاس شده‌اند؟
- آیا build موفق بوده است؟
- آیا coverage upload کار می‌کند؟

## 🔍 بررسی در GitHub

برای بررسی وضعیت pipeline:
1. برو به: https://github.com/parsasohrab1/Intelligent-software-for-diagnosing-and-treating-esophageal-cancer/actions
2. آخرین workflow run را بررسی کن
3. Logs را برای هر job بررسی کن

---

**تاریخ بررسی:** 2024-12-02  
**وضعیت:** Pipeline فعال است و باید بعد از push اجرا شود

