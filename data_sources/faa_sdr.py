from typing import Dict, Any, List
import pandas as pd
from data_sources.base import BaseDataSource

class FAASDRDataSource(BaseDataSource):
    """Adapter for FAA Service Difficulty Reports (Historical Real Maintenance Data)."""
    def __init__(self):
        super().__init__(name="FAA_SDR", source_type="HISTORICAL_REAL", data_mode="HISTORICAL_REAL")

    def health_check(self) -> bool:
        return True

    def ingest(self, filepath: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_json(filepath)
        records = df.to_dict(orient="records")
        return [self.normalize(r) for r in records]

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tail_no": f"REAL-{raw_record.get('n_number', 'UNKNOWN')}",
            "comp_class": raw_record.get("component_type", "airframe").lower(),
            "opened_at": raw_record.get("report_date", "2026-01-01"),
            "task_type": "unscheduled",
            "crew_hours": float(raw_record.get("labor_hours", 4.0)),
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=str(raw_record.get("control_no", "sdr-1")), is_synthetic=0)
        }
