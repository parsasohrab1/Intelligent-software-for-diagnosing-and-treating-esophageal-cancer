# راهنمای جراحی Real-Time

این سند راهنمای سیستم راهنمای جراحی Real-Time برای آندوسکوپی است.

## نیازمندی

ابزار باید در حین عمل:
- مرزهای تومور را به صورت Real-Time در تصاویر آندوسکوپی (NBI/WLI) مشخص کند
- عمق نفوذ احتمالی را تخمین بزند
- حاشیه امن برداشت را تعیین کند
- به جراح یا متخصص آندوسکوپی در تعیین حاشیه امن برداشت کمک کند

## سیستم‌های پیاده‌سازی شده

### 1. Tumor Segmentation ✅

تشخیص مرزهای تومور به صورت Real-Time

**ویژگی‌ها:**
- پشتیبانی از NBI (Narrow Band Imaging)
- پشتیبانی از WLI (White Light Imaging)
- تشخیص خودکار حالت آندوسکوپی
- Segmentation با مدل ML یا rule-based
- استخراج مرزهای تومور (contours)
- محاسبه مساحت و محیط
- Bounding boxes

**فایل‌ها:**
- `app/services/surgical_guidance/tumor_segmentation.py`

### 2. Depth Estimation ✅

تخمین عمق نفوذ احتمالی تومور

**ویژگی‌ها:**
- تخمین عمق بر اساس intensity و texture
- نقشه عمق (depth map)
- دسته‌بندی سطح نفوذ:
  - **Superficial**: < 1mm (mucosa)
  - **Moderate**: 1-3mm (submucosa)
  - **Deep**: > 3mm (muscularis propria or beyond)
- محاسبه اطمینان از تخمین

**فایل‌ها:**
- `app/services/surgical_guidance/depth_estimation.py`

### 3. Safe Margin Calculator ✅

محاسبه حاشیه امن برداشت

**ویژگی‌ها:**
- محاسبه حاشیه امن بر اساس عمق نفوذ
- استانداردهای حاشیه:
  - Superficial: 2mm
  - Moderate: 5mm
  - Deep: 10mm
- محاسبه مساحت برداشت
- امتیاز ایمنی (Safety Score)
- تولید توصیه‌های بالینی

**فایل‌ها:**
- `app/services/surgical_guidance/safe_margin_calculator.py`

### 4. Surgical Guidance System ✅

سیستم جامع راهنمای جراحی

**ویژگی‌ها:**
- یکپارچه‌سازی تمام سیستم‌ها
- پردازش Real-Time (< 200ms)
- ایجاد overlay جامع
- حاشیه‌نویسی متنی

**فایل‌ها:**
- `app/services/surgical_guidance/surgical_guidance_system.py`

## API Endpoints

### پردازش یک فریم
```
POST /api/v1/surgical-guidance/process-frame
```

**Parameters:**
- `file`: تصویر آندوسکوپی
- `endoscopy_mode`: حالت آندوسکوپی (nbi, wli, auto)
- `custom_margin_mm`: حاشیه سفارشی (میلی‌متر)

**Response:**
```json
{
  "frame_id": 0,
  "processing_time_ms": 150.5,
  "tumor_count": 1,
  "tumor_boundaries": [
    {
      "area": 1250.5,
      "perimeter": 150.2,
      "centroid": [320, 240],
      "bbox": [200, 150, 240, 180],
      "confidence": 0.85
    }
  ],
  "depth_estimation": {
    "mean_depth_mm": 2.5,
    "max_depth_mm": 4.0,
    "min_depth_mm": 1.0,
    "invasion_level": "moderate",
    "confidence": 0.75
  },
  "safe_margin": {
    "margin_distance_mm": 5.0,
    "resection_area_mm2": 2500.0,
    "safety_score": 0.82,
    "recommendations": [
      "Recommended safe margin: 5.0mm (moderate invasion)",
      "Estimated invasion depth: 2.5mm (range: 1.0-4.0mm)",
      "High safety score: Resection margin appears adequate"
    ]
  },
  "overlay_image_base64": "...",
  "segmentation_confidence": 0.85
}
```

### Real-Time WebSocket Stream
```
WS /api/v1/surgical-guidance/real-time-stream
```

**Usage:**
- Client sends video frames as bytes
- Server returns surgical guidance results in JSON
- Latency: < 200ms per frame

### دریافت استانداردهای حاشیه
```
GET /api/v1/surgical-guidance/margin-standards
```

## استفاده

### مثال: پردازش یک فریم
```python
from app.services.surgical_guidance.surgical_guidance_system import (
    SurgicalGuidanceSystem,
    EndoscopyMode
)
import cv2

# Load image
frame = cv2.imread("endoscopy_frame.jpg")

# Create system
guidance_system = SurgicalGuidanceSystem(endoscopy_mode=EndoscopyMode.NBI)

# Process
result = guidance_system.process_frame(
    frame=frame,
    frame_id=0
)

# Access results
print(f"Tumor count: {len(result.segmentation.tumor_boundaries)}")
print(f"Mean depth: {result.depth_estimation.mean_depth_mm}mm")
print(f"Safe margin: {result.safe_margin.margin_distance_mm}mm")
print(f"Safety score: {result.safe_margin.safety_score:.1%}")

# Save overlay
cv2.imwrite("guidance_overlay.jpg", result.overlay_image)
```

### مثال: Real-Time Processing
```python
from app.services.realtime.video_processor import VideoFrameProcessor

processor = VideoFrameProcessor(target_fps=30, max_latency_ms=200.0)

# Process frame with surgical guidance
result = processor.process_frame(
    frame=frame,
    model=model,
    frame_id=0,
    include_surgical_guidance=True
)

# Access surgical guidance
if result.surgical_guidance:
    guidance = result.surgical_guidance
    print(f"Tumor count: {guidance['tumor_count']}")
    print(f"Depth: {guidance['mean_depth_mm']}mm")
    print(f"Margin: {guidance['margin_distance_mm']}mm")
```

## Overlay Visualization

### رنگ‌ها
- **قرمز**: مرزهای تومور
- **زرد**: حاشیه امن برداشت
- **سبز**: کانتور برداشت پیشنهادی
- **آبی-قرمز**: نقشه عمق (آبی = سطحی، قرمز = عمیق)

### حاشیه‌نویسی
- تعداد تومورها
- عمق نفوذ
- حاشیه امن
- مساحت برداشت

## استانداردهای حاشیه امن

### Superficial Invasion (< 1mm)
- **حاشیه**: 2mm
- **توضیح**: نفوذ سطحی - فقط mucosa

### Moderate Invasion (1-3mm)
- **حاشیه**: 5mm
- **توضیح**: نفوذ متوسط - submucosa

### Deep Invasion (> 3mm)
- **حاشیه**: 10mm
- **توضیح**: نفوذ عمیق - muscularis propria یا بیشتر

## یکپارچه‌سازی با Real-Time Processing

سیستم راهنمای جراحی با سیستم Real-Time processing یکپارچه است و می‌تواند در حین عمل استفاده شود.

## بهترین روش‌ها

1. **Real-Time**: استفاده از GPU برای پردازش سریع‌تر
2. **Calibration**: کالیبراسیون pixels_per_mm بر اساس endoscope
3. **Validation**: همیشه نتایج را با پزشک بررسی کنید
4. **Safety**: همیشه از حاشیه امن استفاده کنید
5. **Monitoring**: نظارت بر latency در حین عمل

## تنظیمات

### در config.py
```python
# Surgical Guidance
SURGICAL_GUIDANCE_ENABLED: bool = True
SURGICAL_GUIDANCE_PIXELS_PER_MM: float = 10.0  # Calibration factor
SURGICAL_GUIDANCE_MARGIN_SUPERFICIAL: float = 2.0  # mm
SURGICAL_GUIDANCE_MARGIN_MODERATE: float = 5.0  # mm
SURGICAL_GUIDANCE_MARGIN_DEEP: float = 10.0  # mm
```

## وضعیت

تمام سیستم‌های راهنمای جراحی با موفقیت پیاده‌سازی شدند و آماده استفاده برای کمک به جراح در حین عمل هستند.

**Tumor Segmentation**: ✅  
**Depth Estimation**: ✅  
**Safe Margin Calculation**: ✅  
**Real-Time Processing**: ✅  
**WebSocket Support**: ✅

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

