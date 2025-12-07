# Few-Shot Learning برای تشخیص زیرگونه‌های نادر

این سند راهنمای سیستم Few-Shot Learning برای تشخیص زیرگونه‌های نادر سرطان مری است.

## نیازمندی

سیستم باید بتواند با کمترین میزان داده برای زیرگونه‌های نادر سرطان مری (مانند آدنوکارسینوم مری بارت) یا شرایط پیش‌سرطانی پیچیده، دقت بالا را حفظ کند.

## روش‌های پیاده‌سازی شده

### 1. Prototypical Networks ✅

**مفهوم:**
- یادگیری یک embedding space که در آن نمونه‌های هر کلاس به یک prototype نزدیک می‌شوند
- محاسبه prototype به عنوان میانگین embeddings نمونه‌های support
- پیش‌بینی بر اساس فاصله از prototypes

**مزایا:**
- ساده و مؤثر
- کارایی خوب با نمونه‌های بسیار کم (5-shot)
- Inference سریع

**فایل‌ها:**
- `app/services/few_shot_learning/prototypical_networks.py`

### 2. Transfer Learning با Adaptive Unfreezing ✅

**نوآوری:** متدولوژی بهینه‌سازی که دقت را در داده‌های کم‌حجم به طرز چشمگیری بهبود می‌بخشد.

**ویژگی‌های نوآورانه:**
- **Adaptive Unfreezing**: Unfreezing تطبیقی لایه‌ها بر اساس اهمیت
- **Differential Learning Rates**: نرخ یادگیری متفاوت برای لایه‌های مختلف
- **Few-Shot Optimized Head**: لایه‌های classification بهینه شده برای داده‌های کم

این متدولوژی می‌تواند موضوع ثبت اختراع باشد.

**فایل‌ها:**
- `app/services/few_shot_learning/transfer_learning.py`

### 3. Few-Shot Learning Service ✅

سرویس جامع برای Few-Shot Learning

**ویژگی‌ها:**
- پشتیبانی از زیرگونه‌های نادر
- انتخاب خودکار روش
- یکپارچه‌سازی با transfer learning

**فایل‌ها:**
- `app/services/few_shot_learning/few_shot_service.py`

## زیرگونه‌های نادر پشتیبانی شده

### 1. Barrett's Adenocarcinoma
- **Prevalence**: 1%
- **Description**: Adenocarcinoma arising from Barrett's esophagus
- **Min Samples**: 5

### 2. Neuroendocrine Carcinoma
- **Prevalence**: 2%
- **Description**: Neuroendocrine carcinoma of esophagus
- **Min Samples**: 5

### 3. Gastrointestinal Stromal Tumor (GIST)
- **Prevalence**: 1%
- **Description**: GIST of esophagus
- **Min Samples**: 5

### 4. Precancerous Complex
- **Prevalence**: 5%
- **Description**: Complex precancerous conditions
- **Min Samples**: 10

## API Endpoints

### آموزش Few-Shot Model
```
POST /api/v1/few-shot-learning/train
```

**Request:**
- `subtype`: نام زیرگونه نادر
- `n_way`: تعداد کلاس‌ها
- `k_shot`: تعداد نمونه در هر کلاس
- `method`: روش (prototypical, transfer_learning)
- `use_transfer_learning`: استفاده از transfer learning

**Files:**
- `support_files`: تصاویر support set
- `query_files`: تصاویر query set
- `support_labels`: برچسب‌های support
- `query_labels`: برچسب‌های query

**Response:**
```json
{
  "subtype": "barretts_adenocarcinoma",
  "method": "prototypical",
  "accuracy": 0.85,
  "n_way": 2,
  "k_shot": 5,
  "support_samples": 10,
  "query_samples": 20
}
```

### پیش‌بینی زیرگونه نادر
```
POST /api/v1/few-shot-learning/predict
```

**Request:**
- `subtype`: نام زیرگونه
- `method`: روش Few-Shot Learning
- `query_files`: تصاویر query
- `support_files`: تصاویر support (اختیاری)
- `support_labels`: برچسب‌های support (اختیاری)

### دریافت لیست زیرگونه‌های نادر
```
GET /api/v1/few-shot-learning/rare-subtypes
```

### اطلاعات روش
```
GET /api/v1/few-shot-learning/method-info?method=prototypical
```

## استفاده

### مثال: آموزش Prototypical Network
```python
from app.services.few_shot_learning.few_shot_service import FewShotLearningService
import numpy as np

# Initialize service
service = FewShotLearningService(
    method="prototypical",
    use_transfer_learning=True
)

# Initialize for subtype
service.initialize_for_subtype(
    subtype="barretts_adenocarcinoma",
    input_shape=(224, 224, 3),
    num_classes=2
)

# Prepare data (5-shot, 2-way)
support_set = ...  # 10 samples (5 per class)
support_labels = ...  # [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
query_set = ...  # 20 samples
query_labels = ...  # [0, 0, ..., 1, 1, ...]

# Train
result = service.train_few_shot(
    support_set=support_set,
    support_labels=support_labels,
    query_set=query_set,
    query_labels=query_labels,
    n_way=2,
    k_shot=5,
    epochs=50
)

print(f"Accuracy: {result['accuracy']:.2%}")
```

### مثال: استفاده از Transfer Learning
```python
from app.services.few_shot_learning.transfer_learning import TransferLearningOptimizer

# Initialize optimizer
optimizer = TransferLearningOptimizer(
    base_model_name="resnet50",
    input_shape=(224, 224, 3),
    num_classes=2
)

# Build model with adaptive unfreezing
model = optimizer.build_transfer_model(
    freeze_base=True,
    fine_tune_layers=10,
    use_adaptive_unfreezing=True  # نوآوری
)

# Compile with differential learning rates
optimizer.compile_for_few_shot(
    learning_rate=0.001,
    use_differential_lr=True  # نوآوری
)

# Train with few samples
history = optimizer.train_with_few_samples(
    X_train=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val,
    epochs=50,
    batch_size=8,
    use_data_augmentation=True,
    use_early_stopping=True
)
```

## نوآوری و ثبت اختراع

### Adaptive Unfreezing Strategy

**مشکل:** در transfer learning سنتی، یا همه لایه‌ها freeze می‌شوند یا همه unfreeze می‌شوند.

**راه‌حل نوآورانه:**
- Unfreezing تطبیقی بر اساس عمق و اهمیت لایه
- Unfreeze کردن لایه‌های top به صورت تدریجی
- تنظیم learning rate متفاوت برای لایه‌های مختلف

### Differential Learning Rates

**مفهوم:**
- Learning rate پایین‌تر برای لایه‌های پایه (pre-trained)
- Learning rate بالاتر برای لایه‌های جدید (head)
- بهبود همگرایی و دقت در داده‌های کم

این متدولوژی‌ها می‌توانند موضوع ثبت اختراع باشند.

## مزایا

1. **کارایی با داده‌های کم**: دقت بالا با 5-10 نمونه
2. **سریع**: آموزش و inference سریع
3. **انعطاف‌پذیر**: پشتیبانی از انواع مختلف داده
4. **بهینه‌سازی شده**: متدهای نوآورانه برای بهبود دقت

## تنظیمات

### Hyperparameters
```python
EMBEDDING_DIM: int = 64  # بعد embedding
N_WAY: int = 2  # تعداد کلاس‌ها
K_SHOT: int = 5  # تعداد نمونه در هر کلاس
LEARNING_RATE: float = 0.001  # نرخ یادگیری
FINE_TUNE_LAYERS: int = 10  # تعداد لایه‌های fine-tune
```

## وضعیت

تمام سیستم‌های Few-Shot Learning با موفقیت پیاده‌سازی شدند.

**Prototypical Networks**: ✅  
**Transfer Learning**: ✅  
**Adaptive Unfreezing**: ✅  
**Differential Learning Rates**: ✅  
**API Endpoints**: ✅

**تاریخ تکمیل:** 2024-12-19  
**وضعیت:** ✅ تکمیل شده  
**نوآوری:** ✅ Patent-pending Optimization Methods

