import asyncio
import time
import datetime
from typing import Dict, Any, List
from data_sources.adsb_lol import ADSBLolDataSource
from data_sources.awc_weather import AWCWeatherDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.synthetic import SyntheticDataSource

class DataIngestionScheduler:
    def __init__(self):
        self.sources = {
            "adsb_lol": ADSBLolDataSource(),
            "awc_weather": AWCWeatherDataSource(),
            "faa_sdr": FAASDRDataSource(),
            "synthetic": SyntheticDataSource()
        }
        self.freshness = {
            "adsb_lol": {"status": "ONLINE", "last_sync": "N/A", "freshness": "FRESH"},
            "awc_weather": {"status": "ONLINE", "last_sync": "N/A", "freshness": "FRESH"},
            "faa_sdr": {"status": "ONLINE", "last_sync": "N/A", "freshness": "BATCH"},
            "synthetic": {"status": "ONLINE", "last_sync": "LOCAL", "freshness": "SYNTHETIC"}
        }

    def sync_source(self, source_id: str) -> Dict[str, Any]:
        if source_id not in self.sources:
            return {"error": "Source not found"}

        src = self.sources[source_id]
        now_str = datetime.datetime.now().isoformat()
        
        try:
            records = src.ingest()
            self.freshness[source_id] = {
                "status": "ONLINE" if src.health_check() else "OFFLINE",
                "last_sync": now_str,
                "freshness": "FRESH",
                "record_count": len(records)
            }
            return {"source_id": source_id, "status": "synced", "records_ingested": len(records), "timestamp": now_str}
        except Exception as e:
            self.freshness[source_id] = {
                "status": "ERROR",
                "last_sync": now_str,
                "freshness": "STALE",
                "error": str(e)
            }
            return {"source_id": source_id, "status": "error", "message": str(e)}

    def sync_all(self) -> Dict[str, Any]:
        results = {}
        for s_id in self.sources:
            results[s_id] = self.sync_source(s_id)
        return results

scheduler_instance = DataIngestionScheduler()
