"""
Tests for Clinical Decision Support services
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender
from app.services.cds.prognostic_scorer import PrognosticScorer
from app.services.cds.data_completeness import (
    validate_patient_data,
    validate_cancer_data,
    validate_cds_inputs,
)


class TestCDSDataCompleteness:
    """Test CDS input completeness validation"""

    def test_complete_patient_data(self):
        result = validate_patient_data({
            "age": 65,
            "gender": "Male",
            "bmi": 28,
            "smoking": False,
            "alcohol": False,
            "gerd": True,
            "barretts_esophagus": False,
            "family_history": False,
        })
        assert result["is_complete"] is True
        assert result["completeness_score"] == 1.0
        assert len(result["warnings"]) == 0

    def test_missing_required_patient_fields(self):
        result = validate_patient_data({})
        assert result["is_complete"] is False
        assert "age" in result["missing_required"]
        assert "gender" in result["missing_required"]
        assert any(w["severity"] == "error" for w in result["warnings"])

    def test_missing_cancer_staging(self):
        result = validate_cancer_data(None)
        assert result["is_complete"] is False
        assert "cancer_data" in result["missing_required"]

    def test_unknown_pdl1_status(self):
        result = validate_cancer_data({
            "t_stage": "T2",
            "n_stage": "N1",
            "m_stage": "M0",
            "pdl1_status": "Unknown",
        })
        assert "pdl1_status" in result["missing_recommended"]

    def test_full_cds_validation_low_reliability(self):
        result = validate_cds_inputs({"age": 65}, None, context="full")
        assert result["reliability"] == "low"
        assert result["prediction_reliable"] is False


class TestRiskPredictor:
    """Test Risk Predictor service"""
    
    @pytest.fixture
    def predictor(self):
        """Create RiskPredictor instance"""
        return RiskPredictor()
    
    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data"""
        return {
            "age": 65,
            "gender": "M",
            "tumor_stage": "T2",
            "lymph_nodes": 2,
            "histology": "adenocarcinoma"
        }
    
    def test_predictor_initialization(self, predictor):
        """Test RiskPredictor initialization"""
        assert predictor is not None
    
    def test_calculate_risk_score(self, predictor, sample_patient_data):
        """Test risk score calculation"""
        risk = predictor.calculate_risk_score(sample_patient_data)
        
        assert risk is not None
        assert isinstance(risk, dict)
        assert "risk_score" in risk
        assert "risk_category" in risk
        assert "recommendation" in risk
    
    def test_predict_with_model(self, predictor, sample_patient_data):
        """Test risk prediction with model"""
        mock_model = Mock()
        mock_model.predict_proba = Mock(return_value=np.array([[0.3, 0.7]]))
        mock_model.feature_names = ['age', 'is_male', 'smoking', 'alcohol', 'bmi', 'gerd', 'barretts_esophagus', 'family_history']
        
        risk = predictor.predict_with_model(sample_patient_data, mock_model)
        
        assert risk is not None
        assert isinstance(risk, dict)
        assert "risk_score" in risk


class TestTreatmentRecommender:
    """Test Treatment Recommender service"""
    
    @pytest.fixture
    def recommender(self):
        """Create TreatmentRecommender instance"""
        return TreatmentRecommender()
    
    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data"""
        return {
            "age": 65,
            "tumor_stage": "T2",
            "lymph_nodes": 2,
            "performance_status": 1,
            "comorbidities": []
        }
    
    def test_recommender_initialization(self, recommender):
        """Test TreatmentRecommender initialization"""
        assert recommender is not None
    
    def test_recommend_treatment(self, recommender, sample_patient_data):
        """Test treatment recommendation"""
        recommendations = recommender.recommend_treatment(sample_patient_data)
        
        assert recommendations is not None
        assert isinstance(recommendations, (list, dict))
    
    def test_recommend_treatment_with_guidelines(self, recommender, sample_patient_data):
        """Test that recommendations are generated against NCCN guidelines"""
        recommendations = recommender.recommend_treatment(sample_patient_data)

        assert recommendations is not None
        assert isinstance(recommendations, (list, dict))
        assert recommendations.get("guidelines") == "NCCN"


class TestPrognosticScorer:
    """Test Prognostic Scorer service"""
    
    @pytest.fixture
    def scorer(self):
        """Create PrognosticScorer instance"""
        return PrognosticScorer()
    
    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data"""
        return {
            "age": 65,
            "tumor_stage": "T2",
            "lymph_nodes": 2,
            "histology": "adenocarcinoma",
            "performance_status": 1
        }
    
    def test_scorer_initialization(self, scorer):
        """Test PrognosticScorer initialization"""
        assert scorer is not None
    
    def test_calculate_prognostic_score(self, scorer, sample_patient_data):
        """Test prognostic score calculation"""
        score = scorer.calculate_prognostic_score(sample_patient_data)
        
        assert score is not None
        assert isinstance(score, (dict, float, int))
    
    def test_calculate_prognostic_score_with_cancer_data(self, scorer, sample_patient_data):
        """Test prognostic score calculation combining patient and cancer characteristics"""
        cancer_data = {"tumor_size_cm": 4.5, "grade": "G3", "lymphovascular_invasion": True}

        score = scorer.calculate_prognostic_score(sample_patient_data, cancer_data)

        assert score is not None
        assert isinstance(score, (dict, float, int))

