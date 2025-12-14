# بهبودهای دقت در یادگیری ماشین (ML Accuracy Improvements)

## خلاصه بهبودها

این سند تمام بهبودهای اعمال شده برای افزایش دقت مدل‌های یادگیری ماشین را شرح می‌دهد.

## 1. بهینه‌سازی Hyperparameters (پارامترهای بهینه)

### بهبودهای اعمال شده:
- **LogisticRegression**: 
  - `max_iter`: 1000 → 2000
  - `C`: 1.0 (بهینه)
  - `class_weight`: 'balanced' (برای مدیریت عدم تعادل کلاس)
  - `solver`: 'lbfgs' (برای دقت بهتر)

- **RandomForest**:
  - `n_estimators`: 100 → 200
  - `max_depth`: 15 (بهینه)
  - `min_samples_split`: 5
  - `min_samples_leaf`: 2
  - `max_features`: 'sqrt'
  - `class_weight`: 'balanced'

- **XGBoost**:
  - `n_estimators`: 200
  - `max_depth`: 8
  - `learning_rate`: 0.05 (کاهش برای دقت بهتر)
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `min_child_weight`: 3
  - `reg_alpha`: 0.1 (L1 regularization)
  - `reg_lambda`: 1.0 (L2 regularization)

- **LightGBM**:
  - `n_estimators`: 200
  - `max_depth`: 12
  - `learning_rate`: 0.05
  - `num_leaves`: 31
  - `subsample`: 0.8
  - `reg_alpha`: 0.1
  - `reg_lambda`: 0.1

- **NeuralNetwork**:
  - معماری بهبود یافته با BatchNormalization
  - لایه‌های بیشتر (128 → 256 برای deep)
  - Dropout بهینه (0.2-0.4)
  - Early Stopping با patience=10
  - ReduceLROnPlateau برای تنظیم learning rate

## 2. Feature Engineering (مهندسی ویژگی)

### پیش‌پردازش داده:
- **Standard Scaling**: نرمال‌سازی ویژگی‌ها
- **Missing Value Imputation**: جایگزینی مقادیر گمشده با median
- **Feature Selection**: انتخاب ویژگی‌های مهم (KBest, RFE)
- **PCA**: کاهش ابعاد برای مدل‌های پیچیده

## 3. مدیریت عدم تعادل کلاس (Class Imbalance)

- استفاده از `class_weight='balanced'` برای تمام مدل‌ها
- محاسبه خودکار وزن کلاس‌ها
- بهبود دقت در کلاس‌های اقلیت

## 4. Cross-Validation و Early Stopping

- **Stratified K-Fold**: برای تقسیم داده با حفظ نسبت کلاس‌ها
- **Early Stopping**: برای XGBoost و LightGBM (stopping_rounds=10)
- **Early Stopping برای Neural Networks**: با restore_best_weights

## 5. Callbacks برای Neural Networks

- **EarlyStopping**: توقف زودهنگام برای جلوگیری از overfitting
- **ReduceLROnPlateau**: کاهش learning rate هنگام توقف بهبود
- **BatchNormalization**: برای آموزش پایدارتر

## 6. استفاده از ماژول AccuracyOptimizer

### کلاس‌های جدید:
- `AccuracyOptimizer`: کلاس اصلی برای بهینه‌سازی
- `HyperparameterTuner`: تنظیم hyperparameters
- `FeatureEngineer`: مهندسی ویژگی
- `EnsembleBuilder`: ساخت ensemble models

## نحوه استفاده

### در API:
```python
POST /api/v1/ml-models/train
{
    "data_path": "path/to/data.csv",
    "target_column": "target",
    "model_type": "RandomForest",
    "optimize_accuracy": true,  # فعال کردن بهینه‌سازی
    "enable_hyperparameter_tuning": true
}
```

### در کد Python:
```python
from app.services.ml_training import MLTrainingPipeline

pipeline = MLTrainingPipeline(
    experiment_name="my_experiment",
    optimize_accuracy=True  # فعال کردن بهینه‌سازی
)

# آماده‌سازی داده با پیش‌پردازش
X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(
    data,
    target_column="target",
    preprocess=True  # فعال کردن پیش‌پردازش
)

# آموزش با بهینه‌سازی
history = pipeline.train_model(
    "RandomForest",
    X_train,
    y_train,
    X_val,
    y_val,
    optimize=True  # استفاده از hyperparameters بهینه
)
```

## نتایج مورد انتظار

با این بهبودها، انتظار می‌رود:
- **افزایش 5-15% در accuracy** برای اکثر مدل‌ها
- **کاهش overfitting** با استفاده از regularization و early stopping
- **عملکرد بهتر در کلاس‌های اقلیت** با class_weight balanced
- **آموزش پایدارتر** با feature scaling و normalization

## فایل‌های تغییر یافته

1. `app/services/ml_training.py` - اضافه شدن بهینه‌سازی
2. `app/services/ml_models/sklearn_models.py` - بهبود hyperparameters پیش‌فرض
3. `app/services/ml_models/neural_network.py` - بهبود معماری و callbacks
4. `app/services/ml_improvements/accuracy_optimizer.py` - ماژول جدید
5. `app/api/v1/endpoints/ml_models.py` - اضافه شدن گزینه‌های بهینه‌سازی

## نکات مهم

- بهینه‌سازی به صورت پیش‌فرض فعال است (`optimize_accuracy=True`)
- می‌توانید با تنظیم `optimize_accuracy=False` آن را غیرفعال کنید
- Hyperparameter tuning ممکن است زمان بیشتری بگیرد اما دقت را بهبود می‌بخشد
