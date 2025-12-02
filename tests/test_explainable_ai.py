"""
Tests for Explainable AI
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.services.explainable_ai import ExplainableAI


class TestExplainableAI:
    """Test Explainable AI service"""
    
    @pytest.fixture
    def explainer(self):
        """Create ExplainableAI instance"""
        return ExplainableAI()
    
    @pytest.fixture
    def mock_model(self):
        """Create mock model"""
        model = Mock()
        model.predict = Mock(return_value=np.array([1, 0, 1]))
        model.predict_proba = Mock(return_value=np.array([[0.2, 0.8], [0.9, 0.1], [0.3, 0.7]]))
        return model
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data"""
        return pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6],
            'feature3': [7, 8, 9]
        })
    
    def test_explainer_initialization(self, explainer):
        """Test ExplainableAI initialization"""
        assert explainer is not None
    
    def test_calculate_feature_importance(self, explainer, mock_model, sample_data):
        """Test calculating feature importance"""
        # Mock model with feature_importances_
        mock_model.feature_importances_ = np.array([0.3, 0.5, 0.2])
        importance = explainer.calculate_feature_importance(mock_model, sample_data)
        
        assert importance is not None
        assert isinstance(importance, dict)
        assert len(importance) == len(sample_data.columns)
    
    def test_explain_with_shap(self, explainer, mock_model, sample_data):
        """Test explaining with SHAP"""
        explanation = explainer.explain_with_shap(
            mock_model,
            sample_data,
            max_samples=2
        )
        
        assert explanation is not None
        assert isinstance(explanation, dict)
    
    def test_explain_prediction(self, explainer, mock_model, sample_data):
        """Test explaining a prediction"""
        # Mock model with feature_importances_
        mock_model.feature_importances_ = np.array([0.3, 0.5, 0.2])
        explanation = explainer.explain_prediction(
            mock_model,
            sample_data,
            instance_idx=0
        )
        
        assert explanation is not None
        assert isinstance(explanation, dict)
        assert "prediction" in explanation or "feature_importance" in explanation
    
    def test_generate_explanation_report(self, explainer, mock_model, sample_data):
        """Test generating explanation report"""
        # Mock model with feature_importances_
        mock_model.feature_importances_ = np.array([0.3, 0.5, 0.2])
        report = explainer.generate_explanation_report(
            mock_model,
            sample_data
        )
        
        assert report is not None
        assert isinstance(report, dict)
        assert "feature_importance" in report

