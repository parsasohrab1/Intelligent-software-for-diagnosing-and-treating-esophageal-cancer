"""
Model registry for storing and managing trained models
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import pickle

from app.core.mongodb import get_mongodb_database


class ModelRegistry:
    """Registry for managing trained models"""

    def __init__(self, storage_path: str = "models"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.db = get_mongodb_database()
        self.collection = self.db["model_registry"] if self.db is not None else None

    def register_model(
        self,
        model_name: str,
        model_type: str,
        model_path: str,
        metrics: Dict,
        feature_names: List[str],
        training_config: Optional[Dict] = None,
        baseline_statistics: Optional[Dict] = None,
    ) -> str:
        """Register a model in the registry"""
        if self.collection is None:
            raise ValueError("MongoDB is not available")
        
        model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        model_record = {
            "model_id": model_id,
            "model_name": model_name,
            "model_type": model_type,
            "model_path": model_path,
            "metrics": metrics,
            "feature_names": feature_names,
            "training_config": training_config or {},
            "baseline_statistics": baseline_statistics or {},
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        self.collection.insert_one(model_record)
        return model_id

    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model information"""
        if self.collection is None:
            return None
        model = self.collection.find_one({"model_id": model_id})
        if model:
            model["_id"] = str(model["_id"])
        return model

    def list_models(
        self,
        model_type: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> List[Dict]:
        """List all models"""
        if self.collection is None:
            return []
        
        query = {"status": status}
        if model_type:
            query["model_type"] = model_type

        models = self.collection.find(query).sort("created_at", -1).limit(limit)
        return [self._format_result(m) for m in models]

    def get_best_model(self, metric: str = "roc_auc") -> Optional[Dict]:
        """Get best model based on metric"""
        if self.collection is None:
            return None
        
        models = list(self.collection.find({"status": "active"}))

        if not models:
            return None

        best_model = max(
            models,
            key=lambda m: m.get("metrics", {}).get(metric, 0),
        )

        return self._format_result(best_model)

    def update_model_status(self, model_id: str, status: str):
        """Update model status"""
        if self.collection is None:
            return
        self.collection.update_one(
            {"model_id": model_id}, {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
        )

    def delete_model(self, model_id: str):
        """Delete model from registry"""
        if self.collection is None:
            return
        model = self.get_model(model_id)
        if model:
            # Delete file
            if os.path.exists(model["model_path"]):
                os.remove(model["model_path"])

            # Delete from registry
            self.collection.delete_one({"model_id": model_id})

    def _format_result(self, result: Dict) -> Dict:
        """Format MongoDB result"""
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result

