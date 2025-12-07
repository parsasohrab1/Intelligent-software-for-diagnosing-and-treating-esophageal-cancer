# امنیت داده (Data Security) - HIPAA/GDPR Compliance

این سند راهنمای پیاده‌سازی امنیت داده برای سیستم تشخیص و درمان سرطان مری است که با استانداردهای HIPAA (آمریکا) و GDPR (اروپا) سازگار است.

## ویژگی‌های امنیتی پیاده‌سازی شده

### 1. رمزگذاری (Encryption)

#### رمزگذاری در حالت استراحت (Encryption at Rest)
- **AES-256**: استفاده از الگوریتم AES-256-CBC برای رمزگذاری داده‌های حساس
- **رمزگذاری در سطح فیلد**: فیلدهای PHI (Protected Health Information) به صورت جداگانه رمزگذاری می‌شوند
- **مدیریت کلید**: کلیدهای رمزگذاری از طریق متغیرهای محیطی مدیریت می‌شوند

#### فیلدهای حساس (PHI Fields)
فیلدهای زیر به صورت خودکار رمزگذاری می‌شوند:
- `patient_id`
- `name`, `first_name`, `last_name`
- `email`
- `phone`, `phone_number`
- `address`, `street_address`, `city`, `zip_code`, `postal_code`
- `ssn`, `social_security_number`
- `medical_record_number`, `mrn`
- `date_of_birth`, `dob`
- `insurance_number`
- `national_id`
- `passport_number`

### 2. کنترل دسترسی (Access Control)

#### Role-Based Access Control (RBAC)
سیستم از کنترل دسترسی مبتنی بر نقش استفاده می‌کند:

**نقش‌های کاربری:**
- `DATA_SCIENTIST`: دسترسی به داده‌های سنتتیک و غیرشناسایی شده
- `CLINICAL_RESEARCHER`: دسترسی به داده‌های غیرشناسایی شده و سنتتیک
- `MEDICAL_ONCOLOGIST`: دسترسی کامل به داده‌های بیمار (با رضایت)
- `DATA_ENGINEER`: دسترسی کامل به داده‌ها
- `SYSTEM_ADMINISTRATOR`: دسترسی کامل + مدیریت کاربران
- `ETHICS_COMMITTEE`: دسترسی به لاگ‌های حسابرسی و متادیتا

#### Permission-Based Access
هر endpoint نیاز به permission خاص دارد:
- `READ_DEIDENTIFIED`: خواندن داده‌های غیرشناسایی شده
- `READ_ALL`: خواندن تمام داده‌ها
- `WRITE_ALL`: نوشتن/ویرایش داده‌ها
- `READ_AUDIT_LOGS`: خواندن لاگ‌های حسابرسی

### 3. Data Masking و Anonymization

#### سطوح Masking
- **NONE**: بدون masking (دسترسی کامل)
- **PARTIAL**: masking جزئی (نمایش 4 کاراکتر آخر)
- **FULL**: masking کامل
- **AGGREGATE**: فقط آمارهای تجمیعی

#### Masking بر اساس نقش
- `DATA_SCIENTIST`: Partial masking برای patient_id، Full masking برای اطلاعات شخصی
- `CLINICAL_RESEARCHER`: Partial masking برای patient_id و name
- `MEDICAL_ONCOLOGIST`: بدون masking (با رضایت)
- `SYSTEM_ADMINISTRATOR`: بدون masking

### 4. مدیریت رضایت (Consent Management)

#### انواع رضایت
- `DATA_PROCESSING`: پردازش داده
- `DATA_SHARING`: اشتراک‌گذاری داده
- `RESEARCH`: استفاده در تحقیقات
- `MARKETING`: استفاده در بازاریابی
- `THIRD_PARTY`: اشتراک با طرف‌های سوم

#### وضعیت‌های رضایت
- `GRANTED`: اعطا شده
- `DENIED`: رد شده
- `WITHDRAWN`: پس گرفته شده
- `EXPIRED`: منقضی شده
- `PENDING`: در انتظار

### 5. لاگ‌های حسابرسی (Audit Logging)

تمام دسترسی‌ها به داده‌های PHI لاگ می‌شوند:
- **Data Access Logging**: تمام دسترسی‌ها به داده‌های بیمار
- **User Action Logging**: تمام اقدامات کاربران
- **Security Event Logging**: رویدادهای امنیتی
- **Suspicious Activity Detection**: تشخیص فعالیت‌های مشکوک

### 6. سیاست‌های نگهداری و حذف داده (Data Retention & Deletion)

#### HIPAA Compliance
- **دوره نگهداری**: 7 سال (2555 روز)
- **حذف خودکار**: داده‌های منقضی شده به صورت خودکار حذف می‌شوند

#### GDPR Compliance
- **Right to be Forgotten**: بیماران می‌توانند درخواست حذف کامل داده‌های خود را بدهند
- **حذف فوری**: حذف داده‌ها بلافاصله انجام می‌شود
- **گزینه Anonymization**: به جای حذف، می‌توان داده‌ها را anonymize کرد

## API Endpoints

### Consent Management
- `POST /api/v1/consent/grant`: اعطای رضایت
- `POST /api/v1/consent/withdraw`: پس‌گیری رضایت
- `GET /api/v1/consent/check/{patient_id}`: بررسی رضایت
- `GET /api/v1/consent/patient/{patient_id}`: دریافت تمام رضایت‌های یک بیمار

### Data Privacy
- `POST /api/v1/data-privacy/delete-patient-data`: حذف داده‌های بیمار (GDPR)
- `POST /api/v1/data-privacy/cleanup-expired-data`: پاکسازی داده‌های منقضی شده
- `GET /api/v1/data-privacy/retention-policy`: دریافت سیاست نگهداری داده

### Patient Data (Protected)
- `GET /api/v1/patients/`: لیست بیماران (با masking)
- `GET /api/v1/patients/{patient_id}`: اطلاعات بیمار (با masking و کنترل دسترسی)
- `POST /api/v1/patients/`: ایجاد بیمار جدید (نیاز به WRITE_ALL permission)

## تنظیمات (Configuration)

### متغیرهای محیطی
```bash
# Encryption
ENCRYPTION_KEY=<32-byte-key-for-AES-256>
HASH_SALT=<salt-for-hashing>

# Security
SECRET_KEY=<jwt-secret-key>
```

### تنظیمات در config.py
```python
USE_AES256_ENCRYPTION: bool = True
DATA_RETENTION_DAYS: int = 2555  # 7 years
ENABLE_DATA_MASKING: bool = True
REQUIRE_CONSENT_FOR_ACCESS: bool = True
```

## استفاده در کد

### مثال: استفاده از Data Masking
```python
from app.core.security.dependencies import get_masked_patient_data
from app.core.security.dependencies import check_patient_access

# در endpoint
patient = check_patient_access(patient_id, current_user, db)
masked_data = get_masked_patient_data(patient, current_user, db)
return masked_data
```

### مثال: بررسی رضایت
```python
from app.core.security.consent_manager import ConsentManager, ConsentType

consent_manager = ConsentManager(db)
has_consent = consent_manager.check_consent(
    patient_id,
    ConsentType.DATA_PROCESSING
)
```

### مثال: رمزگذاری داده
```python
from app.core.security.encryption import DataEncryption

encryption = DataEncryption(use_aes256=True)
encrypted_data = encryption.encrypt_dict(patient_data)
```

## بهترین روش‌ها (Best Practices)

1. **همیشه از dependencies استفاده کنید**: از `require_permission` و `check_patient_access` استفاده کنید
2. **لاگ تمام دسترسی‌ها**: تمام دسترسی‌ها به صورت خودکار لاگ می‌شوند
3. **بررسی رضایت**: قبل از دسترسی به داده، رضایت را بررسی کنید
4. **استفاده از masking**: داده‌ها را بر اساس نقش کاربر mask کنید
5. **مدیریت کلید**: کلیدهای رمزگذاری را در متغیرهای محیطی نگهداری کنید

## انطباق با استانداردها

### HIPAA (Health Insurance Portability and Accountability Act)
- ✅ رمزگذاری داده‌های PHI
- ✅ کنترل دسترسی
- ✅ لاگ‌های حسابرسی
- ✅ نگهداری داده به مدت 7 سال
- ✅ مدیریت رضایت

### GDPR (General Data Protection Regulation)
- ✅ Right to be Forgotten
- ✅ Data Minimization
- ✅ Consent Management
- ✅ Data Portability
- ✅ Privacy by Design

## امنیت در Production

1. **کلیدهای رمزگذاری**: از یک Key Management Service (KMS) استفاده کنید
2. **TLS/SSL**: تمام ارتباطات باید از HTTPS استفاده کنند
3. **Rate Limiting**: محدودیت نرخ درخواست برای جلوگیری از حملات
4. **Monitoring**: نظارت مداوم بر دسترسی‌ها و رویدادهای امنیتی
5. **Backup Encryption**: بکاپ‌ها نیز باید رمزگذاری شوند

