from typing import Dict, Any, List
import urllib.request
import urllib.error
import json
import time
from data_sources.base import BaseDataSource

class AWCWeatherDataSource(BaseDataSource):
    """Adapter for NOAA AWC (Aviation Weather Center) METAR Data API."""
    def __init__(self):
        super().__init__(name="AWC_Weather", source_type="LIVE_REAL", data_mode="LIVE_REAL")

    def health_check(self) -> bool:
        res = self.fetch_raw(station_ids="VOTV")
        return res["status_code"] == 200

    def fetch_raw(self, station_ids: str = "VOTV,VIDP,VOHS") -> Dict[str, Any]:
        start_t = time.time()
        url = f"https://aviationweather.gov/api/data/metar?ids={station_ids}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Console/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                latency_ms = (time.time() - start_t) * 1000.0
                records = json.loads(res.read().decode("utf-8"))
                normalized = [self.normalize(r) for r in records]
                return {
                    "status_code": 200,
                    "records": normalized,
                    "latency_ms": latency_ms,
                    "error": None,
                    "retry_after": None,
                }
        except urllib.error.HTTPError as e:
            latency_ms = (time.time() - start_t) * 1000.0
            retry_after = e.headers.get("Retry-After") if e.headers else None
            return {
                "status_code": e.code,
                "records": [],
                "latency_ms": latency_ms,
                "error": f"HTTP {e.code}: {e.reason}",
                "retry_after": int(retry_after) if retry_after and retry_after.isdigit() else None,
            }
        except Exception as e:
            latency_ms = (time.time() - start_t) * 1000.0
            return {
                "status_code": 504 if "timeout" in str(e).lower() else 500,
                "records": [],
                "latency_ms": latency_ms,
                "error": str(e),
                "retry_after": None,
            }

    def ingest(self, station_ids: str = "VOTV,VIDP,VOHS") -> List[Dict[str, Any]]:
        res = self.fetch_raw(station_ids=station_ids)
        return res["records"]

    def normalize(self, raw_metar: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "station": raw_metar.get("icaoId", "VOTV"),
            "raw_text": raw_metar.get("rawOb", ""),
            "temp_c": float(raw_metar.get("temp", 25.0)),
            "dewpoint_c": float(raw_metar.get("dewp", 20.0)),
            "wind_speed_kt": float(raw_metar.get("wspd", 5.0)),
            "visibility_miles": float(raw_metar.get("visib", 10.0)),
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=str(raw_metar.get("metarId", "metar-0")), is_synthetic=0)
        }
