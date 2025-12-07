# یکپارچه‌سازی بومی با سیستم‌های کلینیک

این سند راهنمای یکپارچه‌سازی با سیستم‌های موجود کلینیک است.

## سیستم‌های پشتیبانی شده

### 1. PACS (Picture Archiving and Communication System) ✅

یکپارچه‌سازی با سیستم‌های PACS برای دریافت و ارسال تصاویر DICOM

**ویژگی‌ها:**
- C-STORE: ذخیره تصاویر DICOM
- C-FIND: جستجوی مطالعات
- C-MOVE: انتقال مطالعات
- پشتیبانی از DICOM networking

**API Endpoints:**
- `POST /api/v1/integration/pacs/connect` - اتصال به PACS
- `POST /api/v1/integration/pacs/store-image` - ذخیره تصویر DICOM
- `GET /api/v1/integration/pacs/find-studies` - جستجوی مطالعات

### 2. Endoscopy Software ✅

یکپارچه‌سازی با نرم‌افزارهای آندوسکوپی

**سیستم‌های پشتیبانی شده:**
- Olympus
- Pentax
- Fujifilm
- Karl Storz
- Generic (برای سیستم‌های دیگر)

**ویژگی‌ها:**
- دریافت جریان ویدیو زنده
- دریافت داده‌های پروسیجر
- ارسال نتایج تحلیل
- دریافت لیست پروسیجرهای بیمار

**API Endpoints:**
- `POST /api/v1/integration/endoscopy/connect` - اتصال به سیستم آندوسکوپی
- `GET /api/v1/integration/endoscopy/video-stream` - دریافت جریان ویدیو
- `POST /api/v1/integration/endoscopy/send-analysis` - ارسال نتیجه تحلیل

### 3. EHR (Electronic Health Records) ✅

یکپارچه‌سازی با سیستم‌های EHR با استفاده از HL7 FHIR

**سیستم‌های پشتیبانی شده:**
- Epic
- Cerner
- Allscripts
- Athenahealth
- Generic FHIR
- HL7 v2

**ویژگی‌ها:**
- دریافت اطلاعات بیمار (FHIR Patient)
- ایجاد Observation (FHIR Observation)
- ایجاد Diagnostic Report (FHIR DiagnosticReport)
- جستجوی بیماران
- دریافت Observations بیمار

**API Endpoints:**
- `POST /api/v1/integration/ehr/connect` - اتصال به EHR
- `GET /api/v1/integration/ehr/patient/{patient_id}` - دریافت اطلاعات بیمار
- `POST /api/v1/integration/ehr/create-observation` - ایجاد Observation
- `POST /api/v1/integration/ehr/create-diagnostic-report` - ایجاد Diagnostic Report

## Adapter Pattern

سیستم از الگوی Adapter استفاده می‌کند تا یکپارچه‌سازی با سیستم‌های مختلف را ساده کند.

**مزایا:**
- یکسان‌سازی interface برای سیستم‌های مختلف
- افزودن سیستم‌های جدید بدون تغییر کد موجود
- مدیریت متمرکز اتصالات

## Integration Manager

مدیریت متمرکز تمام یکپارچه‌سازی‌ها

**ویژگی‌ها:**
- ثبت و مدیریت adapters
- اتصال/قطع اتصال همزمان
- دریافت داده از تمام سیستم‌ها
- ارسال نتایج به تمام سیستم‌ها

## API Endpoints یکپارچه

### وضعیت اتصال
```
GET /api/v1/integration/status
```

### اتصال/قطع اتصال
```
POST /api/v1/integration/connect-all
POST /api/v1/integration/disconnect-all
```

### دریافت داده از تمام سیستم‌ها
```
GET /api/v1/integration/patient/{patient_id}/all-systems
```

### ارسال نتایج به تمام سیستم‌ها
```
POST /api/v1/integration/patient/{patient_id}/send-results
```

## استفاده

### مثال: اتصال به PACS
```python
from app.services.integration.pacs_integration import PACSIntegration, PACSConnection

connection = PACSConnection(
    host="pacs.hospital.com",
    port=11112,
    ae_title="INESCAPE"
)

pacs = PACSIntegration(connection)

# Store image
result = pacs.store_image("image.dcm")

# Find studies
studies = pacs.find_studies(patient_id="P12345")
```

### مثال: اتصال به سیستم آندوسکوپی
```python
from app.services.integration.endoscopy_integration import (
    EndoscopyIntegration,
    EndoscopyConnection,
    EndoscopySystemType
)

connection = EndoscopyConnection(
    system_type=EndoscopySystemType.OLYMPUS,
    api_endpoint="http://endoscopy.hospital.com/api"
)

endoscopy = EndoscopyIntegration(connection)

# Get video stream
stream_url = endoscopy.get_live_video_stream()

# Send analysis result
endoscopy.send_analysis_result(
    procedure_id="PROC001",
    analysis_result={"diagnosis": "esophageal_cancer", "confidence": 0.95}
)
```

### مثال: اتصال به EHR
```python
from app.services.integration.ehr_integration import (
    EHRIntegration,
    EHRConnection,
    EHRSystemType
)

connection = EHRConnection(
    system_type=EHRSystemType.EPIC,
    fhir_base_url="https://fhir.epic.com/api/FHIR/R4",
    client_id="client_id",
    client_secret="client_secret",
    use_oauth=True
)

ehr = EHRIntegration(connection)
ehr.authenticate()

# Get patient
patient = ehr.get_patient("P12345")

# Create observation
observation = ehr.create_observation(
    patient_id="P12345",
    observation_data={
        "code": "33747-0",
        "display": "Esophageal cancer risk score",
        "value": 0.85,
        "unit": "score"
    }
)
```

### مثال: استفاده از Integration Manager
```python
from app.services.integration.integration_adapter import (
    IntegrationManager,
    PACSAdapter,
    EndoscopyAdapter,
    EHRAdapter,
    IntegrationType
)

# Create manager
manager = IntegrationManager()

# Register adapters
pacs_adapter = PACSAdapter(pacs_connection)
endoscopy_adapter = EndoscopyAdapter(endoscopy_connection)
ehr_adapter = EHRAdapter(ehr_connection)

manager.register_adapter(IntegrationType.PACS, pacs_adapter)
manager.register_adapter(IntegrationType.ENDOSCOPY, endoscopy_adapter)
manager.register_adapter(IntegrationType.EHR, ehr_adapter)

# Connect all
manager.connect_all()

# Get patient data from all systems
patient_data = manager.get_patient_data_from_all("P12345")

# Send results to all systems
manager.send_results_to_all("P12345", {
    "analysis": {"diagnosis": "esophageal_cancer"},
    "annotations": [...]
})
```

## Workflow یکپارچه

### 1. دریافت داده از سیستم‌ها
```
Patient ID → Integration Manager → PACS + Endoscopy + EHR
    ↓
Combined Patient Data
```

### 2. پردازش و تحلیل
```
Combined Data → ML Model → Analysis Results
```

### 3. ارسال نتایج به سیستم‌ها
```
Analysis Results → Integration Manager → PACS + Endoscopy + EHR
```

## تنظیمات

### در config.py
```python
# PACS
PACS_ENABLED: bool = True
PACS_HOST: str = "localhost"
PACS_PORT: int = 11112
PACS_AE_TITLE: str = "INESCAPE"

# Endoscopy
ENDOSCOPY_ENABLED: bool = True
ENDOSCOPY_SYSTEM_TYPE: str = "generic"

# EHR
EHR_ENABLED: bool = True
EHR_SYSTEM_TYPE: str = "generic_fhir"
EHR_FHIR_BASE_URL: str = ""
EHR_USE_OAUTH: bool = True
```

## بهترین روش‌ها

1. **Authentication**: استفاده از OAuth 2.0 برای EHR
2. **Error Handling**: مدیریت خطاها برای عدم اختلال در workflow
3. **Caching**: Cache کردن اتصالات برای عملکرد بهتر
4. **Monitoring**: نظارت بر وضعیت اتصالات
5. **Fallback**: سیستم fallback در صورت قطع اتصال
6. **Security**: رمزگذاری داده‌ها در انتقال

## امنیت

- **TLS/SSL**: استفاده از TLS برای اتصالات
- **OAuth 2.0**: احراز هویت برای EHR
- **API Keys**: استفاده از API keys برای سیستم‌های مختلف
- **Access Control**: کنترل دسترسی بر اساس نقش کاربر

## وضعیت

تمام سیستم‌های یکپارچه‌سازی با موفقیت پیاده‌سازی شدند و آماده استفاده برای یکپارچه‌سازی با سیستم‌های موجود کلینیک هستند.

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

