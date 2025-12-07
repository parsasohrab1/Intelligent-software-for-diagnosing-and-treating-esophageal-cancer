# پردازش بلادرنگ (Real-Time Processing)

این سند راهنمای سیستم پردازش بلادرنگ برای استفاده در اتاق آندوسکوپی است.

## نیازمندی‌ها

### تأخیر (Latency)
- **حداکثر تأخیر**: زیر 200 میلی‌ثانیه
- **هدف**: پردازش در لحظه برای کمک به تشخیص
- **FPS هدف**: 30 فریم در ثانیه

### سخت‌افزار
- **GPU/TPU**: برای پردازش سریع
- **Edge Computing**: پشتیبانی از دستگاه‌های لبه
- **بهینه‌سازی**: برای کاهش تأخیر

## ویژگی‌های پیاده‌سازی شده

### 1. Video Frame Processing
پردازش فریم‌های ویدیو با تأخیر کم

**ویژگی‌ها:**
- پیش‌پردازش بهینه
- کاهش resolution برای سرعت بیشتر
- Normalization خودکار
- پشتیبانی از GPU/TPU

**کلاس:** `VideoFrameProcessor`

### 2. Video Stream Processing
پردازش جریان ویدیو بلادرنگ

**ویژگی‌ها:**
- پردازش چندنخی (multi-threaded)
- بافر فریم‌ها
- پردازش غیرهمزمان
- مدیریت صف نتایج

**کلاس:** `VideoStreamProcessor`

### 3. Edge Computing Support
پشتیبانی از Edge Computing

**دستگاه‌های پشتیبانی شده:**
- NVIDIA Jetson (TensorRT)
- Google Coral (Edge TPU)
- Raspberry Pi (TensorFlow Lite)
- Apple Silicon (Metal)
- Intel NUC (OpenVINO)

**کلاس:** `EdgeComputingManager`

## API Endpoints

### پردازش فریم واحد
```
POST /api/v1/realtime/video/process-frame
```

**Parameters:**
- `file`: فایل تصویر (فریم)
- `model_id`: شناسه مدل (اختیاری)
- `max_latency_ms`: حداکثر تأخیر (پیش‌فرض: 200ms)

**Response:**
```json
{
  "frame_id": 0,
  "processing_time_ms": 45.2,
  "total_time_ms": 52.1,
  "prediction": {...},
  "confidence": 0.95,
  "annotations": [...],
  "meets_latency_requirement": true
}
```

### WebSocket برای جریان ویدیو
```
WS /api/v1/realtime/video/stream
```

**Usage:**
- Client sends video frames as bytes
- Server returns processing results in real-time

### آمار عملکرد
```
GET /api/v1/realtime/video/stats
```

**Response:**
```json
{
  "total_frames": 1000,
  "avg_latency_ms": 45.2,
  "min_latency_ms": 12.5,
  "max_latency_ms": 198.3,
  "p95_latency_ms": 95.4,
  "p99_latency_ms": 145.2,
  "fps": 22.1,
  "latency_violations": 5,
  "violation_rate": 0.5,
  "device": "gpu"
}
```

### اطلاعات دستگاه Edge
```
GET /api/v1/realtime/edge/device-info
```

### شروع/توقف جریان
```
POST /api/v1/realtime/video/start-stream
POST /api/v1/realtime/video/stop-stream
```

## استفاده

### مثال: پردازش یک فریم
```python
from app.services.realtime.video_processor import VideoFrameProcessor
import cv2

# Load frame
frame = cv2.imread("frame.jpg")

# Create processor
processor = VideoFrameProcessor(
    target_fps=30,
    max_latency_ms=200.0
)

# Process frame
result = processor.process_frame(frame, model=None, frame_id=0)

print(f"Processing time: {result.processing_time_ms}ms")
print(f"Meets requirement: {result.processing_time_ms <= 200}")
```

### مثال: پردازش جریان ویدیو
```python
from app.services.realtime.video_processor import VideoStreamProcessor

# Create stream processor
processor = VideoStreamProcessor(
    model=model,
    target_fps=30,
    max_latency_ms=200.0
)

# Start processing
processor.start_processing()

# Add frames
for frame in video_frames:
    processor.add_frame(frame)
    
    # Get result
    result = processor.get_result(timeout=0.1)
    if result:
        print(f"Frame {result.frame_id}: {result.processing_time_ms}ms")

# Stop processing
processor.stop_processing()

# Get stats
stats = processor.get_performance_stats()
print(f"Average latency: {stats['avg_latency_ms']}ms")
```

### مثال: بهینه‌سازی برای Edge
```python
from app.services.realtime.edge_computing import EdgeComputingManager

# Create edge manager
edge_manager = EdgeComputingManager()

# Get device info
info = edge_manager.get_device_info()
print(f"Device: {info['device_type']}")

# Optimize model
optimized_model = edge_manager.optimize_model_for_edge(
    model=original_model,
    model_format="tensorflow"
)
```

## بهینه‌سازی‌ها

### 1. پیش‌پردازش
- کاهش resolution برای فریم‌های بزرگ
- Normalization سریع
- تبدیل رنگ بهینه

### 2. Inference
- استفاده از GPU/TPU
- Batch processing (حتی برای یک فریم)
- FP16 precision برای سرعت بیشتر

### 3. Threading
- پردازش چندنخی
- بافر برای جلوگیری از blocking
- مدیریت صف‌ها

### 4. Edge Optimization
- TensorRT برای NVIDIA Jetson
- Edge TPU برای Google Coral
- TensorFlow Lite برای Raspberry Pi
- Metal برای Apple Silicon
- OpenVINO برای Intel

## Performance Monitoring

### معیارهای کلیدی
- **Average Latency**: میانگین تأخیر
- **P95/P99 Latency**: تأخیر در صدک 95/99
- **FPS**: فریم‌های پردازش شده در ثانیه
- **Violation Rate**: درصد فریم‌هایی که تأخیر بیش از حد دارند

### هدف‌ها
- Average latency < 100ms
- P95 latency < 150ms
- P99 latency < 200ms
- Violation rate < 1%

## تنظیمات

### در config.py
```python
REALTIME_ENABLED: bool = True
REALTIME_TARGET_FPS: int = 30
REALTIME_MAX_LATENCY_MS: float = 200.0
REALTIME_BUFFER_SIZE: int = 5
REALTIME_USE_GPU: bool = True
REALTIME_USE_TPU: bool = False
REALTIME_OPTIMIZATION_LEVEL: str = "high"
```

## بهترین روش‌ها

1. **مدل بهینه**: استفاده از مدل‌های بهینه شده برای inference سریع
2. **GPU/TPU**: استفاده از سخت‌افزار اختصاصی
3. **Resolution**: کاهش resolution تا حد ممکن
4. **Batch Size**: استفاده از batch size = 1 برای تأخیر کم
5. **Precision**: استفاده از FP16 به جای FP32
6. **Caching**: Cache کردن مدل در حافظه
7. **Monitoring**: نظارت مداوم بر تأخیر

## استفاده در اتاق آندوسکوپی

### معماری پیشنهادی
```
Endoscopy Camera → Edge Device → Real-Time Processing → Display
                                    ↓
                              Results (< 200ms)
```

### الزامات سخت‌افزاری
- **Edge Device**: NVIDIA Jetson Nano/Xavier یا Google Coral
- **GPU**: برای پردازش سریع
- **Network**: Latency کم برای streaming

### Workflow
1. دریافت فریم از دوربین آندوسکوپی
2. پیش‌پردازش سریع
3. Inference با مدل بهینه شده
4. نمایش نتایج در کمتر از 200ms

## وضعیت

سیستم پردازش بلادرنگ با موفقیت پیاده‌سازی شد و آماده استفاده در اتاق آندوسکوپی است.

**تأخیر هدف**: < 200ms  
**FPS هدف**: 30 fps  
**پشتیبانی Edge**: ✅  
**بهینه‌سازی GPU/TPU**: ✅

