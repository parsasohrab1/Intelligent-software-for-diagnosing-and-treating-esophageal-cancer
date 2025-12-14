"""
ML Training Pipeline with experiment tracking and accuracy optimization
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.utils.class_weight import compute_class_weight
import json
import os

from app.services.ml_models.sklearn_models import (
    LogisticRegressionModel,
    RandomForestModel,
    XGBoostModel,
    LightGBMModel,
)
from app.services.ml_models.neural_network import NeuralNetworkModel

# Import accuracy optimization modules (optional - handle import errors gracefully)
try:
    from app.services.ml_improvements.accuracy_optimizer import (
        AccuracyOptimizer,
        HyperparameterTuner,
        FeatureEngineer
    )
    ACCURACY_OPTIMIZATION_AVAILABLE = True
except ImportError:
    ACCURACY_OPTIMIZATION_AVAILABLE = False
    AccuracyOptimizer = None
    HyperparameterTuner = None
    FeatureEngineer = None


class MLTrainingPipeline:
    """ML Training Pipeline with experiment tracking"""

    def __init__(self, experiment_name: str = "default", optimize_accuracy: bool = True):
        self.experiment_name = experiment_name
        self.models = {}
        self.experiments = []
        self.best_model = None
        self.best_score = 0.0
        self.optimize_accuracy = optimize_accuracy and ACCURACY_OPTIMIZATION_AVAILABLE
        self.accuracy_optimizer = AccuracyOptimizer() if (optimize_accuracy and ACCURACY_OPTIMIZATION_AVAILABLE) else None
        self.feature_engineer = FeatureEngineer() if (optimize_accuracy and ACCURACY_OPTIMIZATION_AVAILABLE) else None
        self.hyperparameter_tuner = HyperparameterTuner() if (optimize_accuracy and ACCURACY_OPTIMIZATION_AVAILABLE) else None

    def prepare_data(
        self,
        data: pd.DataFrame,
        target_column: str,
        test_size: float = 0.2,
        val_size: float = 0.1,
        random_state: int = 42,
        preprocess: bool = True,
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """Prepare train/val/test split with optional preprocessing for better accuracy"""
        X = data.drop(columns=[target_column])
        y = data[target_column]

        # Handle missing values
        if preprocess and self.feature_engineer:
            imputer = SimpleImputer(strategy='median')
            X = pd.DataFrame(
                imputer.fit_transform(X),
                columns=X.columns,
                index=X.index
            )

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Train/val split
        X_train, X_val, y_train, y_val = train_test_split(
            X_train,
            y_train,
            test_size=val_size / (1 - test_size),
            random_state=random_state,
            stratify=y_train,
        )

        # Feature scaling for better accuracy
        if preprocess and self.feature_engineer:
            scaler = StandardScaler()
            X_train = pd.DataFrame(
                scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
            X_val = pd.DataFrame(
                scaler.transform(X_val),
                columns=X_val.columns,
                index=X_val.index
            )
            X_test = pd.DataFrame(
                scaler.transform(X_test),
                columns=X_test.columns,
                index=X_test.index
            )

        return X_train, y_train, X_val, y_val, X_test, y_test

    def train_model(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        optimize: bool = True,
        **kwargs
    ) -> Dict:
        """Train a specific model with accuracy optimization"""
        # Get optimal hyperparameters if optimization is enabled
        if optimize and self.hyperparameter_tuner and ACCURACY_OPTIMIZATION_AVAILABLE:
            optimal_params = self.hyperparameter_tuner.get_optimal_hyperparameters(model_name)
            # Merge with user-provided kwargs (user kwargs take precedence)
            kwargs = {**optimal_params, **kwargs}
        
        # Initialize model
        if model_name == "LogisticRegression":
            model = LogisticRegressionModel(**kwargs)
        elif model_name == "RandomForest":
            model = RandomForestModel(**kwargs)
        elif model_name == "XGBoost":
            model = XGBoostModel(**kwargs)
        elif model_name == "LightGBM":
            model = LightGBMModel(**kwargs)
        elif model_name == "NeuralNetwork":
            model = NeuralNetworkModel(**kwargs)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        # Handle class imbalance for better accuracy
        if optimize:
            try:
                classes = np.unique(y_train)
                class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
                class_weight_dict = dict(zip(classes, class_weights))
                
                # Add class_weight to kwargs if model supports it
                if hasattr(model.model, 'set_params'):
                    try:
                        model.model.set_params(class_weight=class_weight_dict)
                    except:
                        pass
            except:
                pass

        # Train
        training_history = model.train(
            X_train, y_train, X_val, y_val, **kwargs
        )

        # Store model
        self.models[model_name] = model

        # Evaluate on validation set if available
        if X_val is not None and y_val is not None:
            val_metrics = model.evaluate(X_val, y_val)
            training_history.update(val_metrics)
            
            # Add optimization info
            if optimize:
                training_history['optimization_enabled'] = True
                training_history['optimal_hyperparameters'] = kwargs

        return training_history

    def train_all_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        models: Optional[List[str]] = None,
    ) -> Dict:
        """Train all baseline models"""
        if models is None:
            models = ["LogisticRegression", "RandomForest", "XGBoost", "LightGBM"]

        results = {}

        for model_name in models:
            print(f"\nTraining {model_name}...")
            try:
                history = self.train_model(
                    model_name, X_train, y_train, X_val, y_val
                )
                results[model_name] = history

                # Track best model
                score = history.get("val_accuracy", history.get("train_accuracy", 0))
                if score > self.best_score:
                    self.best_score = score
                    self.best_model = self.models[model_name]

            except Exception as e:
                print(f"Error training {model_name}: {str(e)}")
                results[model_name] = {"error": str(e)}

        return results

    def cross_validate(
        self,
        model_name: str,
        X: pd.DataFrame,
        y: pd.Series,
        cv: int = 5,
        **kwargs
    ) -> Dict:
        """Perform cross-validation"""
        if model_name not in self.models:
            self.train_model(model_name, X, y, **kwargs)

        model = self.models[model_name]

        # Cross-validation
        cv_scores = cross_val_score(
            model.model, X, y, cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42), scoring="accuracy"
        )

        return {
            "cv_scores": cv_scores.tolist(),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
        }

    def evaluate_model(
        self,
        model_name: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict:
        """Evaluate model on test set"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]

        # Predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        # Metrics
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(
                precision_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
            "recall": float(
                recall_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
            "f1_score": float(
                f1_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
        }

        try:
            if len(y_proba.shape) > 1:
                metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba[:, 1]))
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
        except:
            metrics["roc_auc"] = 0.0

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics["confusion_matrix"] = cm.tolist()

        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        metrics["classification_report"] = report

        return metrics

    def compare_models(self, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
        """Compare all trained models"""
        comparison = []

        for model_name, model in self.models.items():
            try:
                metrics = self.evaluate_model(model_name, X_test, y_test)
                comparison.append(
                    {
                        "model": model_name,
                        "accuracy": metrics["accuracy"],
                        "precision": metrics["precision"],
                        "recall": metrics["recall"],
                        "f1_score": metrics["f1_score"],
                        "roc_auc": metrics.get("roc_auc", 0.0),
                    }
                )
            except Exception as e:
                print(f"Error evaluating {model_name}: {str(e)}")

        return pd.DataFrame(comparison)

    def save_experiment(self, output_dir: str = "experiments"):
        """Save experiment results"""
        os.makedirs(output_dir, exist_ok=True)

        experiment_data = {
            "experiment_name": self.experiment_name,
            "timestamp": datetime.now().isoformat(),
            "best_model": self.best_model.model_name if self.best_model else None,
            "best_score": self.best_score,
            "models_trained": list(self.models.keys()),
        }

        # Save experiment metadata
        with open(f"{output_dir}/{self.experiment_name}_metadata.json", "w") as f:
            json.dump(experiment_data, f, indent=2)

        # Save models
        for model_name, model in self.models.items():
            model_path = f"{output_dir}/{self.experiment_name}_{model_name}.pkl"
            model.save_model(model_path)

        print(f"Experiment saved to {output_dir}/")

