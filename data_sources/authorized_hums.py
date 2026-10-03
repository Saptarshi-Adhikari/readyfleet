from typing import Dict, Any, List
import pandas as pd
from data_sources.base import BaseDataSource

class AuthorizedHUMSDataSource(BaseDataSource):
    """Adapter for Authorized Longitudinal HUMS Telemetry & Health Datasets."""
    def __init__(self):
        super().__init__(name="AUTHORIZED_HUMS", source_type="HISTORICAL_REAL", data_mode="HISTORICAL_REAL")

    def health_check(self) -> bool:
        return True

    def ingest(self, filepath: str) -> List[Dict[str, Any]]:
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        elif filepath.endswith(".parquet"):
            df = pd.read_parquet(filepath)
        else:
            df = pd.read_json(filepath)

        records = df.to_dict(orient="records")
        return [self.normalize(r) for r in records]

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "aircraft_id": str(raw_record.get("aircraft_id", "AC-01")),
            "component_id": str(raw_record.get("component_id", "COMP-01")),
            "comp_class": str(raw_record.get("comp_class", "engine")).lower(),
            "cycle": int(raw_record.get("cycle", 1)),
            "sensor_name": str(raw_record.get("sensor_name", "sensor_1")),
            "sensor_value": float(raw_record.get("sensor_value", 0.0)),
            "target_rul": float(raw_record["target_rul"]) if "target_rul" in raw_record else None,
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=str(raw_record.get("id", "hums-0")), is_synthetic=0)
        }
