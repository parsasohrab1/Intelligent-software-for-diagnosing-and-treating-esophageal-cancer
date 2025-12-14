"""
Metadata management for collected datasets
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from app.core.mongodb import get_mongodb_database


class MetadataManager:
    """Manage metadata for collected datasets"""

    def __init__(self):
        self.db = get_mongodb_database()
        self.collection = self.db["dataset_metadata"] if self.db is not None else None

    def store_metadata(self, metadata: Dict) -> str:
        """Store dataset metadata"""
        if self.collection is None:
            raise ValueError("MongoDB is not available")
        metadata["created_at"] = datetime.now().isoformat()
        metadata["updated_at"] = datetime.now().isoformat()

        result = self.collection.insert_one(metadata)
        return str(result.inserted_id)

    def get_metadata(self, dataset_id: str) -> Optional[Dict]:
        """Get metadata for a dataset"""
        if self.collection is None:
            return None
        metadata = self.collection.find_one({"dataset_id": dataset_id})
        if metadata:
            metadata["_id"] = str(metadata["_id"])
        return metadata

    def search_metadata(
        self,
        query: Optional[str] = None,
        source: Optional[str] = None,
        data_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Search metadata"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Limit to prevent timeouts
        max_limit = 1000
        effective_limit = min(limit, max_limit) if limit > max_limit else limit
        
        search_filter = {}

        if query:
            search_filter["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"keywords": {"$regex": query, "$options": "i"}},
            ]

        if source:
            search_filter["source"] = source

        if data_type:
            search_filter["data_type"] = data_type

        if self.collection is None:
            return []
        
        try:
            # Use list() to materialize cursor and prevent timeout issues
            results = list(self.collection.find(search_filter).limit(effective_limit))
            return [self._format_result(r) for r in results]
        except Exception as e:
            logger.error(f"Error searching metadata: {e}")
            return []

    def update_metadata(self, dataset_id: str, updates: Dict) -> bool:
        """Update metadata"""
        if self.collection is None:
            return False
        updates["updated_at"] = datetime.now().isoformat()
        result = self.collection.update_one(
            {"dataset_id": dataset_id}, {"$set": updates}
        )
        return result.modified_count > 0

    def delete_metadata(self, dataset_id: str) -> bool:
        """Delete metadata"""
        if self.collection is None:
            return False
        result = self.collection.delete_one({"dataset_id": dataset_id})
        return result.deleted_count > 0

    def get_all_metadata(self, limit: int = 1000) -> List[Dict]:
        """Get all metadata"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Limit to prevent timeouts
        max_limit = 1000
        effective_limit = min(limit, max_limit) if limit > max_limit else limit
        
        if self.collection is None:
            return []
        
        try:
            results = list(self.collection.find().limit(effective_limit))
            return [self._format_result(r) for r in results]
        except Exception as e:
            logger.error(f"Error getting all metadata: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get metadata statistics"""
        if self.collection is None:
            return {
                "total_datasets": 0,
                "by_source": {},
                "by_data_type": {},
            }
        
        total = self.collection.count_documents({})

        # Count by source
        sources = self.collection.distinct("source")
        source_counts = {}
        for source in sources:
            source_counts[source] = self.collection.count_documents({"source": source})

        # Count by data type
        data_types = self.collection.distinct("data_type")
        type_counts = {}
        for data_type in data_types:
            type_counts[data_type] = self.collection.count_documents(
                {"data_type": data_type}
            )

        return {
            "total_datasets": total,
            "by_source": source_counts,
            "by_data_type": type_counts,
        }

    def _format_result(self, result: Dict) -> Dict:
        """Format MongoDB result"""
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result

