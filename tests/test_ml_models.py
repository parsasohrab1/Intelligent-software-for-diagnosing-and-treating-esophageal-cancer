"""
Tests for ML models
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.services.ml_models.base_model import BaseMLModel
from app.services.ml_models.sklearn_models import (
    LogisticRegressionModel,
    RandomForestModel,
)
from app.services.ml_models.neural_network import NeuralNetworkModel


class _ConcreteMLModel(BaseMLModel):
    """Minimal concrete subclass for exercising BaseMLModel's shared (non-abstract) behavior."""

    def build_model(self, input_shape=None, **kwargs):
        self.model = "stub-model"

    def train(self, X_train, y_train, X_val=None, y_val=None, **kwargs):
        self.is_trained = True
        return {"status": "trained"}

    def predict(self, X):
        return np.zeros(len(X))

    def predict_proba(self, X):
        return np.zeros((len(X), 2))


class TestBaseMLModel:
    """Test base ML model class"""

    def test_base_model_is_abstract(self):
        """BaseMLModel defines build_model/train/predict/predict_proba as abstract - it must not be instantiable directly"""
        with pytest.raises(TypeError):
            BaseMLModel(model_name="test_model")

    def test_base_model_initialization(self):
        """Test base model initialization via a concrete subclass"""
        model = _ConcreteMLModel(model_name="test_model")
        assert model.model is None
        assert model.model_name == "test_model"
        assert model.is_trained is False

    def test_base_model_train_sets_is_trained(self):
        """Test that a concrete subclass's train() updates shared base-class state"""
        model = _ConcreteMLModel(model_name="test")
        X = pd.DataFrame({'f1': [1, 3], 'f2': [2, 4]})
        y = pd.Series([0, 1])

        model.train(X, y)
        assert model.is_trained is True

    def test_base_model_save_model(self):
        """Test that save_model works"""
        model = _ConcreteMLModel(model_name="test")
        import tempfile
        import os

        # NamedTemporaryFile holds an exclusive lock on Windows until closed,
        # so grab the path and close the handle before save_model() reopens it.
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        model.save_model(tmp_path)
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_base_model_load_model(self):
        """Test that load_model works"""
        model = _ConcreteMLModel(model_name="test")
        import tempfile
        import pickle
        import os
        
        # Save a test model
        test_data = {
            "model": None,
            "model_name": "test",
            "feature_names": [],
            "is_trained": False
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        with open(tmp_path, "wb") as f:
            pickle.dump(test_data, f)

        model.load_model(tmp_path)
        assert model.model_name == "test"
        os.unlink(tmp_path)


class TestLogisticRegressionModel:
    """Test Logistic Regression model"""
    
    def test_lr_initialization(self):
        """Test logistic regression initialization"""
        model = LogisticRegressionModel()
        assert model.model_name == "LogisticRegression"
        assert model.model is not None
    
    def test_lr_train(self):
        """Test logistic regression training"""
        model = LogisticRegressionModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        history = model.train(X_train, y_train)
        assert model.is_trained is True
        assert model.model is not None
        assert "train_accuracy" in history
    
    def test_lr_predict(self):
        """Test logistic regression prediction"""
        model = LogisticRegressionModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        model.train(X_train, y_train)
        
        X_test = pd.DataFrame({
            'feature1': [2, 6],
            'feature2': [3, 7]
        })
        predictions = model.predict(X_test)
        
        assert len(predictions) == 2
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_lr_predict_proba(self):
        """Test logistic regression probability prediction"""
        model = LogisticRegressionModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        model.train(X_train, y_train)
        
        X_test = pd.DataFrame({
            'feature1': [2],
            'feature2': [3]
        })
        probabilities = model.predict_proba(X_test)
        
        assert probabilities.shape[0] == 1
        assert probabilities.shape[1] == 2
        assert np.allclose(probabilities.sum(axis=1), 1.0)


class TestRandomForestModel:
    """Test Random Forest model"""
    
    def test_rf_initialization(self):
        """Test random forest initialization"""
        model = RandomForestModel()
        assert model.model_name == "RandomForest"
        assert model.model is not None
    
    def test_rf_train(self):
        """Test random forest training"""
        model = RandomForestModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        history = model.train(X_train, y_train)
        assert model.is_trained is True
        assert model.model is not None
        assert "train_accuracy" in history
    
    def test_rf_predict(self):
        """Test random forest prediction"""
        model = RandomForestModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        model.train(X_train, y_train)
        
        X_test = pd.DataFrame({
            'feature1': [2, 6],
            'feature2': [3, 7]
        })
        predictions = model.predict(X_test)
        
        assert len(predictions) == 2
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_rf_feature_importance(self):
        """Test random forest feature importance"""
        model = RandomForestModel()
        X_train = pd.DataFrame({
            'feature1': [1, 3, 5, 7],
            'feature2': [2, 4, 6, 8]
        })
        y_train = pd.Series([0, 1, 0, 1])
        
        model.train(X_train, y_train)
        
        # Check if model has feature_importances_ attribute
        if hasattr(model.model, 'feature_importances_'):
            importance = model.model.feature_importances_
            assert len(importance) == 2
            assert all(imp >= 0 for imp in importance)
        else:
            pytest.skip("Model does not have feature_importances_")


class TestNeuralNetworkModel:
    """Test Neural Network model"""
    
    def test_nn_initialization(self):
        """Test neural network initialization"""
        model = NeuralNetworkModel()
        assert model.model_name == "NeuralNetwork"
        assert model.model is None
    
    @pytest.mark.skip(reason="Requires TensorFlow, may fail in test environment")
    def test_nn_train(self):
        """Test neural network training"""
        model = NeuralNetworkModel()
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        
        model.train(X, y, epochs=1, batch_size=2)
        assert model.model is not None
    
    @pytest.mark.skip(reason="Requires TensorFlow, may fail in test environment")
    def test_nn_predict(self):
        """Test neural network prediction"""
        model = NeuralNetworkModel()
        X_train = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y_train = np.array([0, 1, 0, 1])
        
        model.train(X_train, y_train, epochs=1, batch_size=2)
        
        X_test = np.array([[2, 3], [6, 7]])
        predictions = model.predict(X_test)
        
        assert len(predictions) == 2
        assert all(0 <= pred <= 1 for pred in predictions)

