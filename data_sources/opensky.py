from typing import Dict, Any, List
import urllib.request
import json
from data_sources.base import BaseDataSource

class OpenSkyDataSource(BaseDataSource):
    """Adapter for OpenSky Network ADS-B Operational Aircraft Flight Data."""
    def __init__(self):
        super().__init__(name="OpenSky_Network", source_type="LIVE_REAL", data_mode="LIVE_REAL")

    def health_check(self) -> bool:
        try:
            req = urllib.request.Request("https://opensky-network.org/api/states/all", headers={"User-Agent": "READYFLEET/1.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                return res.status == 200
        except Exception:
            return False

    def ingest(self, bbox: tuple = None) -> List[Dict[str, Any]]:
        if not self.health_check():
            print("OpenSky API offline. Returning empty live records.")
            return []
        try:
            url = "https://opensky-network.org/api/states/all"
            req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                states = data.get("states", [])[:10]
                return [self.normalize(s) for s in states]
        except Exception as e:
            print(f"Error fetching OpenSky states: {e}")
            return []

    def normalize(self, raw_state: list) -> Dict[str, Any]:
        icao24 = raw_state[0] if len(raw_state) > 0 else "unknown"
        callsign = raw_state[1].strip() if len(raw_state) > 1 and raw_state[1] else icao24
        on_ground = raw_state[8] if len(raw_state) > 8 else True
        op_state = "ON_GROUND" if on_ground else "AIRBORNE"
        
        return {
            "tail_no": f"ADS-{callsign.upper()}",
            "type": "Commercial/GA",
            "base": "Live-Airspace",
            "operational_state": op_state,
            "status": "UNKNOWN",  # Do not infer MC/PMC/NMC from ADS-B visibility
            "latitude": raw_state[6] if len(raw_state) > 6 else None,
            "longitude": raw_state[5] if len(raw_state) > 5 else None,
            "altitude": raw_state[7] if len(raw_state) > 7 else None,
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=icao24, is_synthetic=0)
        }
