# پیش‌بینی پاسخ به درمان نئوادجوانت

این سند راهنمای سیستم پیش‌بینی پاسخ بیمار به شیمی‌درمانی یا رادیوتراپی نئوادجوانت است.

## نیازمندی

سیستم باید بر اساس:
- **ویژگی‌های بیومارکر**: PD-L1, MSI, HER2, mutations, CNV, gene expression
- **رادیومیکس**: ویژگی‌های استخراج شده از تصاویر پزشکی

قبل از شروع درمان (نئوادجوانت)، میزان احتمال پاسخ موفقیت‌آمیز بیمار را با دقت بالا پیش‌بینی کند.

## سیستم‌های پیاده‌سازی شده

### 1. Radiomics Feature Extraction ✅

استخراج ویژگی‌های رادیومیکس از تصاویر پزشکی

**دسته‌های ویژگی:**
- **First-Order Features**: Mean, Std, Variance, Skewness, Kurtosis, Entropy
- **Shape Features**: Area, Perimeter, Compactness, Sphericity, Eccentricity
- **Texture Features**: GLCM-based (Contrast, Homogeneity, Energy, Correlation)
- **Wavelet Features**: Multi-resolution analysis
- **Gradient Features**: Edge and gradient-based features

**فایل‌ها:**
- `app/services/radiomics/radiomics_extractor.py`

### 2. Treatment Response Predictor ✅

پیش‌بینی پاسخ به درمان نئوادجوانت

**ویژگی‌ها:**
- ترکیب بیومارکرها و رادیومیکس
- پیش‌بینی با مدل ML یا rule-based
- محاسبه سهم هر عامل
- شناسایی عوامل کلیدی
- تولید توصیه‌های بالینی

**فایل‌ها:**
- `app/services/treatment_response/treatment_response_predictor.py`

## API Endpoints

### پیش‌بینی پاسخ درمانی
```
POST /api/v1/treatment-response/predict
```

**Request Body:**
```json
{
  "patient_id": "CAN001",
  "treatment_type": "Chemotherapy",
  "model_id": "optional_model_id",
  "use_imaging": true
}
```

**Response:**
```json
{
  "patient_id": "CAN001",
  "treatment_type": "Chemotherapy",
  "response_probability": 0.75,
  "response_category": "High",
  "confidence": 0.85,
  "biomarkers_contribution": {
    "PD-L1": 0.8,
    "MSI-H": 0.0,
    "HER2": 0.0,
    "Mutation_Burden": 0.3
  },
  "radiomics_contribution": {
    "Texture_Homogeneity": 0.7,
    "First_Order_Entropy": 0.6,
    "Shape_Compactness": 0.5
  },
  "key_factors": [
    "PD-L1 (contribution: 0.80)",
    "Texture_Homogeneity (contribution: 0.70)"
  ],
  "recommendation": "High probability (75.0%) of successful response to Chemotherapy. Neoadjuvant Chemotherapy is strongly recommended. Key predictive factors: PD-L1 (contribution: 0.80), Texture_Homogeneity (contribution: 0.70).",
  "timestamp": "2024-12-19T10:30:00"
}
```

### پیش‌بینی با تصویر
```
POST /api/v1/treatment-response/predict-with-image
```

**Parameters:**
- `patient_id`: شناسه بیمار
- `treatment_type`: نوع درمان (Chemotherapy یا Radiotherapy)
- `file`: تصویر برای استخراج رادیومیکس
- `model_id`: شناسه مدل (اختیاری)

### تاریخچه پیش‌بینی‌ها
```
GET /api/v1/treatment-response/patient/{patient_id}/history
```

## استفاده

### مثال: پیش‌بینی پاسخ درمانی
```python
from app.services.treatment_response.treatment_response_predictor import TreatmentResponsePredictor

predictor = TreatmentResponsePredictor()

# Prepare biomarkers
biomarkers = {
    "pdl1_status": "positive",
    "pdl1_percentage": 60.0,
    "msi_status": "MSS",
    "her2_status": "negative",
    "mutations": {
        "TP53": True,
        "PIK3CA": False
    },
    "copy_number_variations": {},
    "gene_expression": {}
}

# Predict
prediction = predictor.predict_response(
    patient_id="CAN001",
    biomarkers=biomarkers,
    treatment_type="Chemotherapy"
)

print(f"Response probability: {prediction.response_probability:.1%}")
print(f"Category: {prediction.response_category}")
print(f"Recommendation: {prediction.recommendation}")
```

### مثال: استخراج رادیومیکس
```python
from app.services.radiomics.radiomics_extractor import RadiomicsExtractor
import cv2

extractor = RadiomicsExtractor()

# Load image
image = cv2.imread("ct_scan.jpg")

# Extract features
features = extractor.extract_features(
    image=image,
    modality="CT"
)

print(f"First-order features: {features['first_order']}")
print(f"Texture features: {features['texture']}")
```

## عوامل پیش‌بینی

### بیومارکرها

1. **PD-L1**
   - Positive: افزایش احتمال پاسخ
   - Percentage: هرچه بیشتر، بهتر

2. **MSI-H**
   - MSI-H: افزایش قابل توجه احتمال پاسخ
   - MSS: احتمال متوسط

3. **HER2**
   - Positive: برای targeted therapy

4. **Mutation Burden**
   - High (>5 mutations): افزایش احتمال پاسخ

### رادیومیکس

1. **Texture Homogeneity**
   - بالاتر: احتمال پاسخ بهتر

2. **First-Order Entropy**
   - متوسط (2-6): احتمال پاسخ بهتر

3. **Shape Compactness**
   - بالاتر: احتمال پاسخ بهتر

## دسته‌بندی پاسخ

- **High** (≥70%): پاسخ بالا - درمان نئوادجوانت قویاً توصیه می‌شود
- **Moderate** (40-70%): پاسخ متوسط - درمان با نظارت نزدیک
- **Low** (<40%): پاسخ پایین - در نظر گرفتن استراتژی‌های جایگزین

## یکپارچه‌سازی با CDS

سیستم پیش‌بینی پاسخ درمانی با سیستم CDS موجود یکپارچه است و می‌تواند در توصیه‌های درمانی استفاده شود.

## بهترین روش‌ها

1. **داده کامل**: استفاده از هر دو بیومارکر و رادیومیکس برای دقت بهتر
2. **مدل ML**: استفاده از مدل‌های آموزش دیده برای دقت بالاتر
3. **Validation**: همیشه پیش‌بینی را با پزشک بررسی کنید
4. **Monitoring**: نظارت بر نتایج واقعی برای بهبود مدل

## تنظیمات

### در config.py
```python
# Treatment Response Prediction
TREATMENT_RESPONSE_ENABLED: bool = True
TREATMENT_RESPONSE_DEFAULT_MODEL: str = "treatment_response_v1"
TREATMENT_RESPONSE_HIGH_THRESHOLD: float = 0.7
TREATMENT_RESPONSE_MODERATE_THRESHOLD: float = 0.4
```

## وضعیت

تمام سیستم‌های پیش‌بینی پاسخ درمانی با موفقیت پیاده‌سازی شدند و آماده استفاده برای پیش‌بینی پاسخ بیماران به درمان نئوادجوانت هستند.

**Radiomics Extraction**: ✅  
**Biomarker Integration**: ✅  
**Treatment Response Prediction**: ✅  
**ML Model Support**: ✅  
**Clinical Recommendations**: ✅

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

