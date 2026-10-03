from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import datetime

class BaseDataSource(ABC):
    def __init__(self, name: str, source_type: str, data_mode: str):
        self.name = name
        self.source_type = source_type  # HISTORICAL_REAL, LIVE_REAL, SYNTHETIC
        self.data_mode = data_mode        # DEMO_SYNTHETIC, HISTORICAL_REAL, LIVE_REAL, HYBRID

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def ingest(self, raw_input: Any) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def get_provenance(self, record_id: str, is_synthetic: int = 0, quality: str = "GOOD") -> Dict[str, Any]:
        return {
            "source_name": self.name,
            "source_type": self.source_type,
            "record_id": record_id,
            "ingestion_ts": datetime.datetime.now().isoformat(),
            "synthetic": is_synthetic,
            "data_quality": quality
        }
