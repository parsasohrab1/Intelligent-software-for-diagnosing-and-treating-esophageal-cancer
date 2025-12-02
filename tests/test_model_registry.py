"""
Tests for model registry
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.services.model_registry import ModelRegistry


class TestModelRegistry:
    """Test model registry"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def mock_mongodb_collection(self):
        """Mock MongoDB collection"""
        mock_collection = MagicMock()
        mock_collection.find_one = Mock(return_value=None)
        mock_collection.find = Mock(return_value=[])
        mock_collection.insert_one = Mock(return_value=Mock(inserted_id="test_id"))
        mock_collection.update_one = Mock(return_value=Mock(modified_count=1))
        mock_collection.delete_one = Mock(return_value=Mock(deleted_count=1))
        return mock_collection
    
    @pytest.fixture
    def registry(self, temp_dir, mock_mongodb_collection):
        """Create model registry instance with mocked MongoDB"""
        with patch("app.services.model_registry.get_mongodb_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.__getitem__ = Mock(return_value=mock_mongodb_collection)
            mock_get_db.return_value = mock_db
            
            registry = ModelRegistry(storage_path=temp_dir)
            registry.collection = mock_mongodb_collection
            return registry
    
    def test_registry_initialization(self, registry):
        """Test model registry initialization"""
        assert registry.storage_path is not None
        assert os.path.exists(registry.storage_path)
        assert registry.collection is not None
    
    def test_register_model(self, registry):
        """Test registering a model"""
        model_id = registry.register_model(
            model_name="test_model",
            model_type="logistic_regression",
            model_path="/path/to/model.pkl",
            metrics={"accuracy": 0.95},
            feature_names=["feature1", "feature2"]
        )
        
        assert model_id is not None
        assert registry.collection.insert_one.called
    
    def test_get_model(self, registry):
        """Test getting model information"""
        # Mock find_one to return a model
        mock_model = {
            "model_id": "test_model_123",
            "model_name": "test_model",
            "model_type": "logistic_regression",
            "status": "active",
            "_id": "mongodb_id"
        }
        registry.collection.find_one = Mock(return_value=mock_model)
        
        model = registry.get_model("test_model_123")
        
        assert model is not None
        assert model["model_id"] == "test_model_123"
        assert "_id" in model
    
    def test_list_models(self, registry):
        """Test listing models"""
        # Mock find to return models
        mock_models = [
            {"model_id": "model1", "status": "active", "_id": "id1"},
            {"model_id": "model2", "status": "active", "_id": "id2"},
        ]
        mock_cursor = MagicMock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.__iter__ = Mock(return_value=iter(mock_models))
        registry.collection.find = Mock(return_value=mock_cursor)
        
        models = registry.list_models()
        
        assert len(models) == 2
        assert all("_id" in m for m in models)
    
    def test_get_best_model(self, registry):
        """Test getting best model"""
        mock_models = [
            {"model_id": "model1", "metrics": {"roc_auc": 0.8}, "status": "active"},
            {"model_id": "model2", "metrics": {"roc_auc": 0.9}, "status": "active"},
        ]
        registry.collection.find = Mock(return_value=mock_models)
        
        best_model = registry.get_best_model(metric="roc_auc")
        
        assert best_model is not None
        assert best_model["model_id"] == "model2"
    
    def test_update_model_status(self, registry):
        """Test updating model status"""
        registry.update_model_status("test_model_123", "archived")
        
        assert registry.collection.update_one.called
    
    def test_delete_model(self, registry):
        """Test deleting a model"""
        # Mock get_model to return a model
        mock_model = {
            "model_id": "test_model_123",
            "model_path": "/path/to/model.pkl"
        }
        registry.get_model = Mock(return_value=mock_model)
        
        # Mock os.path.exists and os.remove
        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                registry.delete_model("test_model_123")
                
                assert mock_remove.called
                assert registry.collection.delete_one.called

