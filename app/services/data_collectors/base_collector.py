"""
Base class for data collectors
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd


class BaseDataCollector(ABC):
    """Base class for all data collectors"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.collected_data: List[Dict] = []

    @abstractmethod
    def discover_datasets(self, query: str) -> List[Dict]:
        """Discover relevant datasets"""
        pass

    @abstractmethod
    def download_dataset(self, dataset_id: str, output_path: str) -> bool:
        """Download a specific dataset"""
        pass

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> Dict:
        """Validate downloaded data"""
        pass

    def get_metadata(self, dataset_id: str) -> Dict:
        """Get metadata for a dataset"""
        return {}

