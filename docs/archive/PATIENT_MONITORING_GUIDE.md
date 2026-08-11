# راهنمای Patient Monitoring Dashboard

## 📊 معرفی

Patient Monitoring Dashboard یک سیستم جامع برای رصد و کنترل تمام پارامترهای مهم بیماران است که شامل:
- **Vital Signs** (علائم حیاتی)
- **Lab Results** (نتایج آزمایش)
- **Clinical Parameters** (پارامترهای بالینی)
- **Imaging Results** (نتایج تصویربرداری)

## 🎯 ویژگی‌ها

### 1. Vital Signs (علائم حیاتی)

| Parameter | Normal Range | Unit |
|-----------|--------------|------|
| Blood Pressure (Systolic) | 90 - 140 | mmHg |
| Blood Pressure (Diastolic) | 60 - 90 | mmHg |
| Heart Rate | 60 - 100 | bpm |
| Respiratory Rate | 12 - 20 | breaths/min |
| Temperature | 36.1 - 37.2 | °C |
| Oxygen Saturation | 95 - 100 | % |

### 2. Lab Results (نتایج آزمایش)

| Parameter | Normal Range (Male) | Normal Range (Female) | Unit |
|-----------|---------------------|----------------------|------|
| Hemoglobin | 13.5 - 17.5 | 12.0 - 15.5 | g/dL |
| White Blood Cell Count | 4.0 - 11.0 | 4.0 - 11.0 | ×10³/μL |
| Platelet Count | 150 - 450 | 150 - 450 | ×10³/μL |
| Creatinine | 0.6 - 1.2 | 0.6 - 1.2 | mg/dL |
| Albumin | 3.5 - 5.0 | 3.5 - 5.0 | g/dL |
| AST | 10 - 40 | 10 - 40 | U/L |
| ALT | 7 - 56 | 7 - 56 | U/L |
| C-Reactive Protein | 0 - 3.0 | 0 - 3.0 | mg/L |
| CEA (Tumor Marker) | 0 - 3.0 | 0 - 3.0 | ng/mL |
| CA19-9 (Tumor Marker) | 0 - 37 | 0 - 37 | U/mL |

### 3. Clinical Parameters (پارامترهای بالینی)

| Parameter | Normal Range | Unit |
|-----------|--------------|------|
| BMI | 18.5 - 24.9 | kg/m² |
| Weight Loss | 0 - 5% | % |
| ECOG Performance Status | 0 - 1 | score |
| Pain Score | 0 - 3 | 0-10 scale |

### 4. Imaging Results (نتایج تصویربرداری)

| Parameter | Normal Range | Unit |
|-----------|--------------|------|
| Tumor Length | 0 (no tumor) | cm |
| Wall Thickness | 0.3 - 0.5 | cm |
| Lymph Nodes Positive | 0 (no positive nodes) | count |

## 🚀 دسترسی

### Frontend
- **URL:** http://localhost:3000/monitoring
- **Menu:** "Patient Monitoring" در sidebar

### API Endpoints

1. **Get Patient Monitoring Data:**
   ```
   GET /api/v1/monitoring/patients/{patient_id}/monitoring
   ```

2. **Get All Patients Monitoring:**
   ```
   GET /api/v1/monitoring/patients/monitoring/all?skip=0&limit=100
   ```

3. **Get Normal Ranges:**
   ```
   GET /api/v1/monitoring/normal-ranges
   ```

## 📋 Status Indicators

### Status Types:
- **Normal** (سبز): مقدار در محدوده نرمال
- **Abnormal** (زرد): مقدار خارج از محدوده نرمال
- **Critical** (قرمز): مقدار به شدت خارج از محدوده (30% بیشتر/کمتر)
- **Missing** (خاکستری): داده موجود نیست

## ⚠️ Alerts

Dashboard به صورت خودکار alerts ایجاد می‌کند برای:
- مقادیر Critical
- مقادیر Abnormal
- مقادیر Missing برای پارامترهای مهم

## 🎨 Interface Features

1. **Patient Selection:** Dropdown برای انتخاب بیمار
2. **Tabbed View:** 
   - Tab 1: Vital Signs
   - Tab 2: Lab Results
   - Tab 3: Clinical Parameters
   - Tab 4: Imaging Results
3. **Status Cards:** نمایش Overall Status بیمار
4. **Alerts Panel:** نمایش تمام alerts
5. **Parameter Table:** جدول کامل با:
   - نام پارامتر
   - مقدار فعلی
   - محدوده نرمال
   - وضعیت (normal/abnormal/critical)
   - تاریخ آخرین بروزرسانی

## 📊 مثال Response

```json
{
  "patient_id": "P001",
  "patient_name": "John Doe",
  "age": 65,
  "gender": "Male",
  "has_cancer": true,
  "monitoring_date": "2024-12-02",
  "vital_signs": [
    {
      "name": "Blood Pressure (Systolic)",
      "value": 130.0,
      "unit": "mmHg",
      "normal_range": {"min": 90, "max": 140, "unit": "mmHg"},
      "status": "normal",
      "last_updated": "2024-12-01"
    }
  ],
  "lab_results": [...],
  "clinical_parameters": [...],
  "imaging_results": [...],
  "overall_status": "monitoring_required",
  "alerts": [
    "⚠️ Hemoglobin requires attention"
  ]
}
```

## 🔧 استفاده

### 1. انتخاب بیمار
از dropdown در بالای صفحه، بیمار مورد نظر را انتخاب کنید.

### 2. مشاهده داده‌ها
- داده‌ها به صورت خودکار بارگذاری می‌شوند
- از tabs برای مشاهده دسته‌های مختلف استفاده کنید

### 3. بررسی Alerts
- Alerts در بالای صفحه نمایش داده می‌شوند
- رنگ alert نشان‌دهنده سطح اهمیت است

### 4. بررسی Normal Ranges
- برای هر پارامتر، محدوده نرمال در جدول نمایش داده می‌شود
- Status indicator نشان می‌دهد که آیا مقدار در محدوده نرمال است یا خیر

## 📝 نکات مهم

1. **Gender-Specific Ranges:** Hemoglobin برای مردان و زنان محدوده‌های متفاوتی دارد
2. **Critical Threshold:** مقادیر 30% بیشتر یا کمتر از محدوده نرمال به عنوان Critical در نظر گرفته می‌شوند
3. **Missing Data:** اگر داده‌ای موجود نباشد، status به صورت "missing" نمایش داده می‌شود
4. **Overall Status:** بر اساس تعداد پارامترهای abnormal/critical تعیین می‌شود:
   - **Stable:** همه پارامترها نرمال
   - **Monitoring Required:** 1-2 پارامتر abnormal
   - **Intervention Needed:** بیش از 2 پارامتر abnormal
   - **Critical:** حداقل یک پارامتر critical

## 🔄 به‌روزرسانی داده‌ها

داده‌ها از منابع زیر جمع‌آوری می‌شوند:
- **Clinical Data:** از جدول `clinical_data`
- **Lab Results:** از جدول `lab_results`
- **Imaging Data:** از جدول `imaging_data`
- **Patient Info:** از جدول `patients`

## 🎯 استفاده در Clinical Practice

این dashboard برای:
- **Monitoring روزانه** بیماران
- **تشخیص زودهنگام** مشکلات
- **Tracking پیشرفت** درمان
- **Alert generation** برای موارد نیازمند توجه
- **Documentation** برای گزارش‌های بالینی

