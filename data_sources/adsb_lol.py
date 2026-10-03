from typing import Dict, Any, List
import urllib.request
import json
from data_sources.base import BaseDataSource

class ADSBLolDataSource(BaseDataSource):
    """Adapter for adsb.lol Open-Data Live Aircraft ADS-B Operational Telemetry."""
    def __init__(self):
        super().__init__(name="adsb.lol", source_type="LIVE_REAL", data_mode="LIVE_REAL")

    def health_check(self) -> bool:
        try:
            req = urllib.request.Request("https://api.adsb.lol/v2/ladd", headers={"User-Agent": "READYFLEET-Console/1.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                return res.status == 200
        except Exception:
            return False

    def ingest(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.health_check():
            return []
        try:
            url = "https://api.adsb.lol/v2/ladd"
            req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Console/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                ac_list = data.get("ac", [])[:limit]
                return [self.normalize(ac) for ac in ac_list]
        except Exception as e:
            print(f"Error fetching adsb.lol states: {e}")
            return []

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
            "altitude": 0 if on_ground else alt_baro,
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=hex_id, is_synthetic=0)
        }
