# طرح خروجی‌گیری ONNX/TensorRT — چرا در این تغییر پیاده‌سازی نشد

## هدف این سند

این سند به‌جای پیاده‌سازی جعلی (fake stub) برای export مدل‌ها به ONNX/TensorRT، به‌صورت شفاف توضیح می‌دهد که:
1. وضعیت فعلی کد نسبت به ONNX/TensorRT چیست،
2. چرا در این تغییر پیاده‌سازی واقعی انجام نشد،
3. برای پیاده‌سازی واقعی در آینده چه مراحلی لازم است.

یک ممیزی (audit) قبلی مشخص کرد که فایل `app/services/realtime/edge_computing.py` از قبل حاوی ارجاعات و stubهایی به ONNX/TensorRT است بدون پیاده‌سازی واقعی. هدف این تغییر، **جلوگیری از تکرار همان الگو** با اضافه‌کردن یک stub جعلی دیگر است؛ به همین دلیل به‌جای کد، این سند مستندسازی شد.

## ۱. وضعیت فعلی کد

در فایل `app/services/realtime/edge_computing.py` نقل‌قول مستقیم زیر وجود دارد (خطوط ۱۴۲ تا ۱۵۲):

```python
def _optimize_with_tensorrt(self, model: Any, model_format: str) -> Optional[Any]:
    """بهینه‌سازی با TensorRT (NVIDIA Jetson)"""
    try:
        import tensorrt as trt
        # TensorRT optimization logic
        logger.info("Optimizing model with TensorRT")
        # Implementation would go here
        return model
    except ImportError:
        logger.warning("TensorRT not available")
        return None
```

همچنین در همان فایل، پارامتر `model_format` در چند جا مقدار `"onnx"` را به‌عنوان یک فرمت مجاز در docstring ذکر می‌کند (خط ۱۱۴: `model_format: فرمت مدل (tensorflow, pytorch, onnx)`) و `use_tensorrt: True` در تنظیمات دستگاه Jetson تنظیم شده (خط ۶۴)، اما هیچ منطق واقعی export یا بارگذاری مدل ONNX/TensorRT در کد وجود ندارد — فقط `# Implementation would go here`.

## ۲. چرا در این تغییر پیاده‌سازی نشد

بررسی مستقیم محیط اجرا (از ریشه ریپازیتوری) نتیجه زیر را داد:

```
$ python -c "import onnx; print('onnx version:', onnx.__version__)"
onnx version: 1.22.0
```

پکیج `onnx` نصب است (نسخه ۱.۲۲.۰). اما:

```
$ python -c "import skl2onnx"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'skl2onnx'
```

```
$ python -c "import tensorrt"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'tensorrt'
```

پکیج‌های `skl2onnx` و `tensorrt` نصب **نیستند**. علاوه بر این:

- **دسترسی به شبکه وجود ندارد**: در این محیط اجرا امکان `pip install` برای نصب `skl2onnx` یا `tensorrt` وجود ندارد.
- **حتی در صورت نصب `tensorrt`، هیچ GPU در این محیط وجود ندارد** تا بتوان خروجی TensorRT را واقعاً ساخت یا تست کرد (TensorRT فقط روی سخت‌افزار NVIDIA کار می‌کند).
- بنابراین حتی اگر کد export نوشته می‌شد، امکان تست واقعی (export گرفتن از یک مدل واقعی، بارگذاری آن، و مقایسه خروجی) در این محیط وجود نداشت — و نوشتن چنین کدی بدون تست، دقیقاً همان الگوی «stub جعلی» است که قرار است از آن اجتناب شود.

نتیجه: افزودن کد export در این وضعیت یا (الف) یک stub تست‌نشده و بالقوه غلط تولید می‌کرد، یا (ب) نیازمند نصب پکیج‌هایی بود که در این محیط ممکن نیست. به همین دلیل تصمیم گرفته شد که به‌جای کد، این طرح مستند شود.

## ۳. مراحل پیاده‌سازی واقعی برای آینده

### ۳.۱ مدل‌های scikit-learn / XGBoost / LightGBM

فایل: `app/services/ml_models/sklearn_models.py`

کلاس‌های موجود: `LogisticRegressionModel`، `RandomForestModel`، `XGBoostModel`، `LightGBMModel` (همگی از `BaseMLModel` ارث‌بری می‌کنند).

- باید متد `export_to_onnx(self, filepath: str)` به `BaseMLModel` یا به هر یک از این کلاس‌ها اضافه شود.
- پکیج لازم: `skl2onnx` (برای `LogisticRegressionModel` و `RandomForestModel`)؛ برای `XGBoostModel` و `LightGBMModel` باید از `onnxmltools` یا مسیر تبدیل اختصاصی خود XGBoost/LightGBM به ONNX استفاده شود (این دو کتابخانه توسط `skl2onnx` به‌طور کامل پشتیبانی نمی‌شوند و نیاز به بررسی جداگانه دارند).
- این پکیج‌ها در حال حاضر نصب نیستند و باید ابتدا نصب و تست شوند.

### ۳.۲ مدل شبکه عصبی

فایل: `app/services/ml_models/neural_network.py`

کلاس: `NeuralNetworkModel` — بر اساس بررسی import های فایل (خطوط ۹ تا ۱۶)، این کلاس از **TensorFlow/Keras** استفاده می‌کند (`import tensorflow as tf`, `from tensorflow import keras`)، نه PyTorch. این import به‌صورت اختیاری (try/except) انجام شده و در صورت نبود TensorFlow، خطای `ImportError` صریح پرتاب می‌شود (خط ۴۱).

- بنابراین برای export این مدل باید از `tf2onnx` استفاده شود (نه `torch.onnx.export`، چون فریمورک پایتورچ نیست).
- باید متد `export_to_onnx(self, filepath: str)` به `NeuralNetworkModel` اضافه شود که مدل Keras بارگذاری‌شده (`self.model`) را با `tf2onnx.convert.from_keras` به ONNX تبدیل کند.
- پکیج `tf2onnx` در حال حاضر نصب نیست.

### ۳.۳ طرح تأیید صحت (verification plan)

پس از نصب پکیج‌های لازم و پیاده‌سازی `export_to_onnx`:

1. یک مدل را روی داده واقعی/نمونه آموزش دهید.
2. مدل را با `export_to_onnx` به فرمت ONNX خروجی بگیرید.
3. فایل ONNX را با `onnxruntime.InferenceSession` بارگذاری کنید.
4. روی یک نمونه‌ی نگه‌داشته‌شده (held-out sample) از داده تست:
   - پیش‌بینی مدل اصلی (sklearn/xgboost/lightgbm/keras) را بگیرید.
   - پیش‌بینی مدل ONNX را بگیرید.
   - دو خروجی را با `numpy.allclose` (یا معیار مشابه) و تلورانس مشخص (مثلاً `atol=1e-4`) مقایسه کنید.
5. نتیجه مقایسه (تطابق/عدم تطابق و میزان اختلاف) باید در گزارش تست یا PR مربوطه ثبت شود.
6. برای مسیر TensorRT (مخصوص `edge_computing.py`)، تست واقعی فقط روی سخت‌افزار دارای GPU انویدیا (مثلاً NVIDIA Jetson) قابل انجام است؛ بدون چنین سخت‌افزاری، مسیر TensorRT نباید به‌عنوان کامل یا تست‌شده علامت‌گذاری شود.

## ۴. هشدار مهم

**تا زمانی که مراحل بخش ۳ عملاً پیاده‌سازی و طبق طرح تأیید صحت بخش ۳.۳ تست نشده باشند، قابلیت export به ONNX/TensorRT نباید در هیچ سند پروژه (README، UPDATE_SUGGESTIONS، PRODUCT_OPTIMIZATION_SUGGESTIONS و غیره) به‌عنوان «پیاده‌سازی‌شده» یا «انجام‌شده» علامت‌گذاری شود.** وضعیت فعلی همان stub موجود در `edge_computing.py` است که در بخش ۱ نقل شد و باید همچنان به‌عنوان کار ناتمام (TODO) شناخته شود.
