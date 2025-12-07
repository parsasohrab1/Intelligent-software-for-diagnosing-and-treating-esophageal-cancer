# Explainable AI - Saliency Maps و Heatmaps

این سند راهنمای سیستم توضیح‌پذیری برای مدل‌های ML است که مناطقی از تصویر که مدل بر اساس آن‌ها تصمیم گرفته را برجسته می‌کند.

## نیازمندی

سیستم باید نه تنها تشخیص (مثلاً "سرطان مثبت") را ارائه دهد، بلکه باید مناطقی از تصویر (آندوسکوپی یا رادیولوژی) که مدل بر اساس آن‌ها تصمیم گرفته است را با استفاده از نقشه‌های برجستگی (Heatmaps یا Saliency Maps) برجسته کند.

## روش‌های پشتیبانی شده

### 1. Grad-CAM ✅
**Gradient-weighted Class Activation Mapping**

- استفاده از gradients برای شناسایی مناطق مهم
- مناسب برای مدل‌های CNN
- پشتیبانی از TensorFlow/Keras و PyTorch

### 2. Grad-CAM++ ✅
**Improved Grad-CAM**

- نسخه بهبود یافته Grad-CAM
- دقت بهتر در localization

### 3. LIME ✅
**Local Interpretable Model-agnostic Explanations**

- توضیح‌پذیری برای هر پیش‌بینی
- مستقل از نوع مدل
- نیاز به نصب: `pip install lime`

### 4. SHAP ✅
**SHapley Additive exPlanations**

- بر اساس نظریه بازی
- اهمیت ویژگی‌ها
- نیاز به نصب: `pip install shap`

### 5. Integrated Gradients
**در حال توسعه**

### 6. Occlusion Sensitivity
**در حال توسعه**

## API Endpoints

### توضیح یک تصویر
```
POST /api/v1/xai/explain-image
```

**Parameters:**
- `file`: تصویر (multipart/form-data)
- `model_id`: شناسه مدل
- `method`: روش توضیح‌پذیری (grad_cam, lime, shap, etc.)
- `target_class`: کلاس هدف (اختیاری)
- `layer_name`: نام لایه برای Grad-CAM (اختیاری)

**Response:**
```json
{
  "success": true,
  "model_id": "model_123",
  "prediction": {
    "predicted_class": 1,
    "confidence": 0.95,
    "probabilities": [0.05, 0.95]
  },
  "saliency_map": {
    "method": "grad_cam",
    "map": [...],
    "heatmap_colored": [...],
    "overlay": [...],
    "target_class": 1,
    "layer_name": "conv5_block3_out"
  },
  "explanation": {
    "regions_of_interest": [
      {
        "bbox": [100, 150, 50, 50],
        "area": 2500,
        "center": [125, 175]
      }
    ],
    "confidence_regions": [
      {
        "threshold": 0.5,
        "pixel_count": 5000,
        "percentage": 25.5
      }
    ]
  }
}
```

### توضیح چند تصویر
```
POST /api/v1/xai/explain-batch
```

### مقایسه روش‌ها
```
POST /api/v1/xai/compare-methods
```

**Parameters:**
- `file`: تصویر
- `model_id`: شناسه مدل
- `methods`: لیست روش‌ها (comma-separated): `grad_cam,lime,shap`

### دریافت روش‌های موجود
```
GET /api/v1/xai/methods
```

## استفاده

### مثال: تولید Saliency Map
```python
from app.services.xai.explainable_ai import ExplainableAIService
from app.services.xai.saliency_maps import SaliencyMethod
import cv2

# Load image
image = cv2.imread("endoscopy_image.jpg")

# Create service
xai_service = ExplainableAIService()

# Generate explanation
result = xai_service.explain_image_prediction(
    model_id="model_123",
    image=image,
    method=SaliencyMethod.GRAD_CAM,
    target_class=1  # Cancer class
)

# Get overlay (image with heatmap)
overlay = result["saliency_map"]["overlay"]
cv2.imwrite("explanation.jpg", overlay)
```

### مثال: مقایسه روش‌ها
```python
result = xai_service.compare_explanations(
    model_id="model_123",
    image=image,
    methods=[
        SaliencyMethod.GRAD_CAM,
        SaliencyMethod.LIME,
        SaliencyMethod.SHAP
    ]
)

# Compare similarity
similarity = result["comparison"]["similarity"]
print(f"Grad-CAM vs LIME: {similarity['grad_cam_vs_lime']}")
```

### مثال: استفاده در Real-Time Processing
```python
from app.services.realtime.video_processor import VideoFrameProcessor

processor = VideoFrameProcessor()

# Process frame with saliency map
result = processor.process_frame(
    frame=frame,
    model=model,
    frame_id=0,
    include_saliency=True  # Enable saliency map generation
)

# Access saliency map
if "saliency_map" in result.prediction:
    overlay = result.prediction["saliency_map"]
```

## یکپارچه‌سازی با سیستم‌های کلینیک

### ارسال Heatmap به سیستم آندوسکوپی
```python
from app.services.integration.endoscopy_integration import EndoscopyIntegration

# Generate explanation
result = xai_service.explain_image_prediction(...)
overlay = result["saliency_map"]["overlay"]

# Send to endoscopy system
endoscopy = EndoscopyIntegration(...)
endoscopy.send_analysis_result(
    procedure_id="PROC001",
    analysis_result={
        "diagnosis": "esophageal_cancer",
        "confidence": 0.95
    },
    annotations=[{
        "type": "heatmap",
        "image": overlay,
        "regions": result["explanation"]["regions_of_interest"]
    }]
)
```

### ذخیره در PACS با Annotations
```python
from app.services.integration.pacs_integration import PACSIntegration

# Generate explanation
result = xai_service.explain_image_prediction(...)

# Create DICOM with annotations
# (Implementation would create DICOM SR with overlay)
pacs = PACSIntegration(...)
pacs.store_image("annotated_image.dcm")
```

## نمایش در UI

### Overlay Heatmap
```javascript
// دریافت overlay از API
const response = await fetch('/api/v1/xai/explain-image', {
  method: 'POST',
  body: formData
});

const result = await response.json();
const overlay = result.saliency_map.overlay;

// نمایش در canvas
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const img = new Image();
img.src = 'data:image/jpeg;base64,' + overlay;
img.onload = () => {
  ctx.drawImage(img, 0, 0);
};
```

### نمایش Regions of Interest
```javascript
// نمایش bounding boxes
result.explanation.regions_of_interest.forEach(region => {
  const [x, y, w, h] = region.bbox;
  ctx.strokeStyle = 'red';
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, w, h);
  
  // نمایش confidence
  ctx.fillStyle = 'white';
  ctx.fillText(
    `Confidence: ${region.confidence}`,
    x, y - 5
  );
});
```

## بهترین روش‌ها

1. **انتخاب روش**: 
   - Grad-CAM برای CNN models
   - LIME برای model-agnostic explanations
   - SHAP برای feature importance

2. **Performance**: 
   - Grad-CAM سریع‌تر است
   - LIME و SHAP کندتر اما دقیق‌تر

3. **Real-Time**: 
   - در real-time processing، فقط از Grad-CAM استفاده کنید
   - LIME و SHAP برای post-processing

4. **Validation**: 
   - همیشه heatmap را با پزشک بررسی کنید
   - مقایسه با ground truth annotations

## تنظیمات

### در config.py
```python
# Explainable AI
XAI_ENABLED: bool = True
XAI_DEFAULT_METHOD: str = "grad_cam"
XAI_REALTIME_METHOD: str = "grad_cam"  # Fast method for real-time
XAI_SALIENCY_THRESHOLD: float = 0.5  # Threshold for high-confidence regions
```

## وضعیت

تمام سیستم‌های Explainable AI با موفقیت پیاده‌سازی شدند و آماده استفاده برای توضیح تصمیم‌گیری مدل‌ها هستند.

**Grad-CAM**: ✅  
**LIME**: ✅  
**SHAP**: ✅  
**Real-Time Integration**: ✅  
**Clinical System Integration**: ✅

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده

