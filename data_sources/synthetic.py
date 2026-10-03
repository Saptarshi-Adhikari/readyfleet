from typing import Dict, Any, List
from data_sources.base import BaseDataSource
from gen.generate import generate_all_data

class SyntheticDataSource(BaseDataSource):
    def __init__(self):
        super().__init__(name="READYFLEET_GENERATOR", source_type="SYNTHETIC", data_mode="DEMO_SYNTHETIC")

    def health_check(self) -> bool:
        return True

    def ingest(self, seed: int = 42) -> List[Dict[str, Any]]:
        generate_all_data(seed=seed)
        return [{"status": "ingested", "seed": seed}]

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        raw_record["synthetic"] = 1
        raw_record["provenance"] = self.get_provenance(
            record_id=str(raw_record.get("id", "syn-0")),
            is_synthetic=1
        )
        return raw_record
