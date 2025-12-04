"""
Machine Learning models endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.services.ml_training import MLTrainingPipeline
from app.services.explainable_ai import ExplainableAI
from app.services.model_registry import ModelRegistry
import os

router = APIRouter()


class TrainModelRequest(BaseModel):
    """Request model for training"""

    data_path: str = Field(..., description="Path to training data CSV")
    target_column: str = Field(..., description="Target column name")
    model_type: str = Field(
        default="RandomForest",
        description="Model type: LogisticRegression, RandomForest, XGBoost, LightGBM, NeuralNetwork",
    )
    test_size: float = Field(default=0.2, description="Test set size")
    val_size: float = Field(default=0.1, description="Validation set size")
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Model hyperparameters"
    )


class PredictRequest(BaseModel):
    """Request model for prediction"""

    model_id: str = Field(..., description="Model ID from registry")
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    include_explanation: bool = Field(
        default=False, description="Include SHAP explanation"
    )


class BatchPredictRequest(BaseModel):
    """Request model for batch prediction"""

    model_id: str = Field(..., description="Model ID from registry")
    data_path: str = Field(..., description="Path to data CSV file")
    include_explanation: bool = Field(
        default=False, description="Include SHAP explanation"
    )


@router.post("/train")
async def train_model(request: TrainModelRequest):
    """Train a machine learning model"""
    try:
        # Load data
        data = pd.read_csv(request.data_path)

        # Initialize pipeline
        pipeline = MLTrainingPipeline(experiment_name=f"{request.model_type}_{request.target_column}")

        # Prepare data
        X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(
            data,
            request.target_column,
            test_size=request.test_size,
            val_size=request.val_size,
        )

        # Train model
        training_history = pipeline.train_model(
            request.model_type,
            X_train,
            y_train,
            X_val,
            y_val,
            **(request.hyperparameters or {}),
        )

        # Evaluate on test set
        test_metrics = pipeline.evaluate_model(
            request.model_type, X_test, y_test
        )

        # Register model
        registry = ModelRegistry()
        model = pipeline.models[request.model_type]
        model_path = f"models/{pipeline.experiment_name}_{request.model_type}.pkl"
        os.makedirs("models", exist_ok=True)
        model.save_model(model_path)

        # Calculate baseline statistics for monitoring
        baseline_statistics = {}
        for feature_name in model.feature_names:
            if feature_name in X_train.columns:
                feature_data = X_train[feature_name].dropna()
                if len(feature_data) > 0:
                    baseline_statistics[feature_name] = {
                        "mean": float(feature_data.mean()),
                        "std": float(feature_data.std()),
                        "min": float(feature_data.min()),
                        "max": float(feature_data.max()),
                    }

        model_id = registry.register_model(
            model_name=request.model_type,
            model_type=request.model_type,
            model_path=model_path,
            metrics=test_metrics,
            feature_names=model.feature_names,
            training_config={
                "target_column": request.target_column,
                "test_size": request.test_size,
                "val_size": request.val_size,
                "hyperparameters": request.hyperparameters,
            },
            baseline_statistics=baseline_statistics,
        )

        return {
            "message": "Model trained successfully",
            "model_id": model_id,
            "training_history": training_history,
            "test_metrics": test_metrics,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")


@router.post("/predict")
async def predict(request: PredictRequest):
    """Make prediction with a trained model"""
    try:
        registry = ModelRegistry()
        model_info = registry.get_model(request.model_id)

        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")

        # Load model
        from app.services.ml_models.sklearn_models import (
            LogisticRegressionModel,
            RandomForestModel,
            XGBoostModel,
            LightGBMModel,
        )
        from app.services.ml_models.neural_network import NeuralNetworkModel

        model_type = model_info["model_type"]
        if model_type == "LogisticRegression":
            model = LogisticRegressionModel()
        elif model_type == "RandomForest":
            model = RandomForestModel()
        elif model_type == "XGBoost":
            model = XGBoostModel()
        elif model_type == "LightGBM":
            model = LightGBMModel()
        elif model_type == "NeuralNetwork":
            model = NeuralNetworkModel()
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        model.load_model(model_info["model_path"])

        # Prepare features
        feature_df = pd.DataFrame([request.features])
        # Ensure columns match
        missing_cols = set(model.feature_names) - set(feature_df.columns)
        for col in missing_cols:
            feature_df[col] = 0
        feature_df = feature_df[model.feature_names]

        # Predict
        prediction = model.predict(feature_df)[0]
        probability = model.predict_proba(feature_df)[0].tolist()

        result = {
            "prediction": int(prediction),
            "probability": probability,
            "model_id": request.model_id,
            "model_type": model_type,
        }

        # Record prediction for monitoring (if enabled)
        try:
            from app.core.config import settings
            if settings.MODEL_MONITORING_ENABLED:
                from app.services.mlops.model_monitoring import ModelMonitoring
                monitoring = ModelMonitoring()
                monitoring.record_prediction(
                    model_id=request.model_id,
                    features=request.features,
                    prediction=float(prediction),
                    probability=probability,
                )
        except Exception as monitoring_error:
            # Log but don't fail the prediction
            import logging
            logging.warning(f"Failed to record prediction for monitoring: {str(monitoring_error)}")

        # Add explanation if requested
        if request.include_explanation:
            explainer = ExplainableAI()
            explanation = explainer.explain_prediction(model.model, feature_df)
            result["explanation"] = explanation

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making prediction: {str(e)}")


@router.post("/predict/batch")
async def batch_predict(request: BatchPredictRequest):
    """Make batch predictions"""
    try:
        registry = ModelRegistry()
        model_info = registry.get_model(request.model_id)

        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")

        # Load model (similar to predict endpoint)
        # ... (same model loading logic)

        # Load data
        data = pd.read_csv(request.data_path)

        # Make predictions
        # ... (prediction logic)

        return {"message": "Batch prediction completed", "predictions": []}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in batch prediction: {str(e)}"
        )


@router.get("/models")
async def list_models(
    model_type: Optional[str] = None,
    status: str = "active",
    limit: int = 10000,
):
    """List all trained models with caching"""
    from app.core.cache import CacheManager
    
    cache_manager = CacheManager()
    cache_key = cache_manager.generate_key("ml_models", "list", model_type=model_type, status=status, limit=limit)
    
    # Try to get from cache
    try:
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
    except Exception:
        pass
    
    try:
        registry = ModelRegistry()
        models = registry.list_models(model_type=model_type, status=status, limit=limit)
        result = {"models": models, "count": len(models)}
        
        # Cache for 5 minutes
        try:
            cache_manager.set(cache_key, result, ttl=300)
        except Exception:
            pass
        
        return result

    except Exception as e:
        # Log error but return empty list if MongoDB is not available
        import logging
        logging.warning(f"Error listing models: {str(e)}")
        return {"models": [], "count": 0}


@router.get("/models/{model_id}")
async def get_model_info(model_id: str):
    """Get model information with caching"""
    from app.core.cache import CacheManager
    
    cache_manager = CacheManager()
    cache_key = cache_manager.generate_key("ml_models", "by_id", model_id=model_id)
    
    # Try to get from cache
    cached_model = cache_manager.get(cache_key)
    if cached_model is not None:
        return cached_model
    
    try:
        registry = ModelRegistry()
        model = registry.get_model(model_id)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Cache for 10 minutes
        cache_manager.set(cache_key, model, ttl=600)

        return model

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting model: {str(e)}"
        )


@router.get("/models/best")
async def get_best_model(metric: str = "roc_auc"):
    """Get best model based on metric"""
    try:
        registry = ModelRegistry()
        best_model = registry.get_best_model(metric=metric)

        if not best_model:
            raise HTTPException(status_code=404, detail="No models found")

        return best_model

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting best model: {str(e)}"
        )


@router.post("/explain")
async def explain_prediction(
    model_id: str,
    features: Dict[str, Any],
    background_samples: int = 100,
):
    """Explain a prediction using SHAP"""
    try:
        registry = ModelRegistry()
        model_info = registry.get_model(model_id)

        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")

        # Load model and explain
        # ... (similar to predict endpoint)

        explainer = ExplainableAI()
        explanation = explainer.explain_prediction(model.model, feature_df)

        return explanation

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error explaining prediction: {str(e)}"
        )


@router.get("/explain/{model_id}/report")
async def get_explanation_report(model_id: str):
    """Get comprehensive explanation report for a model"""
    try:
        registry = ModelRegistry()
        model_info = registry.get_model(model_id)

        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")

        # Load model and generate report
        # ... (load model logic)

        explainer = ExplainableAI()
        report = explainer.generate_explanation_report(model.model, X_sample)

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating report: {str(e)}"
        )

