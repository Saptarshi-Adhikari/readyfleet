from typing import Dict, Any, List
import urllib.request
import json
from data_sources.base import BaseDataSource

class AWCWeatherDataSource(BaseDataSource):
    """Adapter for NOAA AWC (Aviation Weather Center) METAR Data API."""
    def __init__(self):
        super().__init__(name="AWC_Weather", source_type="LIVE_REAL", data_mode="LIVE_REAL")

    def health_check(self) -> bool:
        try:
            url = "https://aviationweather.gov/api/data/metar?ids=VOTV&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Console/1.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                return res.status == 200
        except Exception:
            return False

    def ingest(self, station_ids: str = "VOTV,VIDP,VOHS") -> List[Dict[str, Any]]:
        if not self.health_check():
            return []
        try:
            url = f"https://aviationweather.gov/api/data/metar?ids={station_ids}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Console/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                records = json.loads(res.read().decode("utf-8"))
                return [self.normalize(r) for r in records]
        except Exception as e:
            print(f"Error fetching AWC weather METARs: {e}")
            return []

    def normalize(self, raw_metar: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "station": raw_metar.get("icaoId", "VOTV"),
            "raw_text": raw_metar.get("rawOb", ""),
            "temp_c": float(raw_metar.get("temp", 25.0)),
            "dewpoint_c": float(raw_metar.get("dewp", 20.0)),
            "wind_speed_kt": float(raw_metar.get("wspd", 5.0)),
            "visibility_miles": float(raw_record_vis := raw_metar.get("visib", 10.0)),
            "synthetic": 0,
            "provenance": self.get_provenance(record_id=str(raw_metar.get("metarId", "metar-0")), is_synthetic=0)
        }
