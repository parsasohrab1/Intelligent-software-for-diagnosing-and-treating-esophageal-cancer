"""
Scikit-learn based models
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
import lightgbm as lgb

from app.services.ml_models.base_model import BaseMLModel


class LogisticRegressionModel(BaseMLModel):
    """Logistic Regression model"""

    def __init__(self, **kwargs):
        super().__init__("LogisticRegression", **kwargs)
        # Improved defaults for better accuracy
        default_params = {
            'max_iter': 2000,
            'C': 1.0,
            'penalty': 'l2',
            'solver': 'lbfgs',
            'class_weight': 'balanced',
            'random_state': 42
        }
        default_params.update(kwargs)
        self.model = LogisticRegression(**default_params)

    def build_model(self, input_shape: Optional[int] = None, **kwargs):
        """Build model"""
        default_params = {
            'max_iter': 2000,
            'C': 1.0,
            'penalty': 'l2',
            'solver': 'lbfgs',
            'class_weight': 'balanced',
            'random_state': 42
        }
        default_params.update(kwargs)
        self.model = LogisticRegression(**default_params)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train model"""
        self.feature_names = X_train.columns.tolist()
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Calculate training metrics
        train_pred = self.model.predict(X_train)
        train_score = self.model.score(X_train, y_train)

        history = {"train_accuracy": train_score}

        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            history["val_accuracy"] = val_score

        self.training_history = history
        return history

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict_proba(X)


class RandomForestModel(BaseMLModel):
    """Random Forest model"""

    def __init__(self, n_estimators: int = 200, **kwargs):
        super().__init__("RandomForest", **kwargs)
        # Improved defaults for better accuracy
        default_params = {
            'n_estimators': n_estimators,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'class_weight': 'balanced',
            'random_state': 42,
            'n_jobs': -1
        }
        default_params.update(kwargs)
        self.model = RandomForestClassifier(**default_params)

    def build_model(self, input_shape: Optional[int] = None, **kwargs):
        """Build model"""
        default_params = {
            'n_estimators': kwargs.get("n_estimators", 200),
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'class_weight': 'balanced',
            'random_state': 42,
            'n_jobs': -1
        }
        default_params.update({k: v for k, v in kwargs.items() if k != "n_estimators"})
        self.model = RandomForestClassifier(**default_params)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train model"""
        self.feature_names = X_train.columns.tolist()
        self.model.fit(X_train, y_train)
        self.is_trained = True

        train_score = self.model.score(X_train, y_train)
        history = {"train_accuracy": train_score}

        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            history["val_accuracy"] = val_score

        self.training_history = history
        return history

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained")
        return dict(zip(self.feature_names, self.model.feature_importances_))


class XGBoostModel(BaseMLModel):
    """XGBoost model"""

    def __init__(self, **kwargs):
        super().__init__("XGBoost", **kwargs)
        # Improved defaults for better accuracy
        default_params = {
            'n_estimators': 200,
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42,
            'eval_metric': 'logloss',
            'use_label_encoder': False
        }
        default_params.update(kwargs)
        self.model = xgb.XGBClassifier(**default_params)

    def build_model(self, input_shape: Optional[int] = None, **kwargs):
        """Build model"""
        default_params = {
            'n_estimators': 200,
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42,
            'eval_metric': 'logloss',
            'use_label_encoder': False
        }
        default_params.update(kwargs)
        self.model = xgb.XGBClassifier(**default_params)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train model"""
        self.feature_names = X_train.columns.tolist()

        eval_set = []
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=kwargs.get("verbose", False),
        )
        self.is_trained = True

        train_pred = self.model.predict(X_train)
        train_score = self.model.score(X_train, y_train)
        history = {"train_accuracy": train_score}

        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            history["val_accuracy"] = val_score

        self.training_history = history
        return history

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained")
        return dict(zip(self.feature_names, self.model.feature_importances_))


class LightGBMModel(BaseMLModel):
    """LightGBM model"""

    def __init__(self, **kwargs):
        super().__init__("LightGBM", **kwargs)
        # Improved defaults for better accuracy
        default_params = {
            'n_estimators': 200,
            'max_depth': 12,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'random_state': 42,
            'verbose': -1
        }
        default_params.update(kwargs)
        self.model = lgb.LGBMClassifier(**default_params)

    def build_model(self, input_shape: Optional[int] = None, **kwargs):
        """Build model"""
        default_params = {
            'n_estimators': 200,
            'max_depth': 12,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'random_state': 42,
            'verbose': -1
        }
        default_params.update(kwargs)
        self.model = lgb.LGBMClassifier(**default_params)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train model"""
        self.feature_names = X_train.columns.tolist()

        eval_set = []
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
            if eval_set
            else None,
        )
        self.is_trained = True

        train_score = self.model.score(X_train, y_train)
        history = {"train_accuracy": train_score}

        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            history["val_accuracy"] = val_score

        self.training_history = history
        return history

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained")
        return dict(zip(self.feature_names, self.model.feature_importances_))

