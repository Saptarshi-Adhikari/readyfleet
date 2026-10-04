from typing import Dict, Any, List
import urllib.request
import urllib.error
import json
import time
from data_sources.base import BaseDataSource

class ADSBLolDataSource(BaseDataSource):
    """Adapter for adsb.lol Open-Data Live Aircraft ADS-B Operational Telemetry."""
    def __init__(self):
        super().__init__(name="adsb.lol", source_type="LIVE_REAL", data_mode="LIVE_REAL")

    def health_check(self) -> bool:
        res = self.fetch_raw(limit=1)
        return res["status_code"] == 200

    def fetch_raw(self, limit: int = 10) -> Dict[str, Any]:
        start_t = time.time()
        url = "https://api.adsb.lol/v2/ladd"
        req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Console/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                latency_ms = (time.time() - start_t) * 1000.0
                raw_bytes = res.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                ac_list = data.get("ac", [])[:limit]
                records = [self.normalize(ac) for ac in ac_list]
                return {
                    "status_code": 200,
                    "records": records,
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

    def ingest(self, limit: int = 10) -> List[Dict[str, Any]]:
        res = self.fetch_raw(limit=limit)
        return res["records"]

    def normalize(self, raw_ac: Dict[str, Any]) -> Dict[str, Any]:
        hex_id = raw_ac.get("hex", "unknown")
        flight = raw_ac.get("flight", hex_id).strip()
        alt_baro = raw_ac.get("alt_baro", 0)
        on_ground = alt_baro == "ground" or raw_ac.get("ground", False)
        
        return {
            "tail_no": f"ADS-{flight.upper()}",
            "type": raw_ac.get("t", "General Aviation"),
            "base": "Live-Airspace",
            "operational_state": "ON_GROUND" if on_ground else "AIRBORNE",
            "status": "UNKNOWN",  # Never infer MC/PMC/NMC from ADS-B
            "latitude": raw_ac.get("lat"),
            "longitude": raw_ac.get("lon"),
            "altitude": 0 if on_ground else (alt_baro if isinstance(alt_baro, (int, float)) else 0),
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=hex_id, is_synthetic=0)
        }
