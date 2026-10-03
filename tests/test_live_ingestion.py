import unittest
import os
import yaml
import json
from data_sources.adsb_lol import ADSBADotLolAdapter
from data_sources.awc_weather import AWCWeatherAdapter
from data_sources.scheduler import IngestionScheduler

class TestLiveIngestionFabric(unittest.TestCase):

    def test_master_registry_files_exist(self):
        csv_path = os.path.join("research", "data_source_master.csv")
        json_path = os.path.join("research", "data_source_master.json")
        yaml_path = os.path.join("config", "data_sources.yaml")
        
        self.assertTrue(os.path.exists(csv_path), "Master CSV registry missing")
        self.assertTrue(os.path.exists(json_path), "Master JSON registry missing")
        self.assertTrue(os.path.exists(yaml_path), "Master YAML config missing")

        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            self.assertIn("sources", cfg)
            source_ids = [s["source_id"] for s in cfg["sources"]]
            self.assertIn("adsb_lol", source_ids)
            self.assertIn("awc_weather", source_ids)

    def test_adsb_lol_normalization(self):
        adapter = ADSBADotLolAdapter()
        mock_raw = {
            "hex": "a1b2c3",
            "flight": "TEST101",
            "lat": 28.5,
            "lon": 77.2,
            "alt_baro": 15000,
            "gs": 250,
            "track": 180,
            "r": "VT-TEST",
            "t": "C172"
        }
        norm = adapter.normalize(mock_raw)
        self.assertEqual(norm["registration"], "VT-TEST")
        self.assertEqual(norm["flight_state"], "AIRBORNE")
        self.assertEqual(norm["altitude_ft"], 15000)
        self.assertEqual(norm["synthetic"], 0)
        self.assertEqual(norm["provenance"]["source_id"], "adsb_lol")

    def test_awc_weather_normalization(self):
        adapter = AWCWeatherAdapter()
        mock_raw = {
            "icaoId": "VIDP",
            "temp": 28.0,
            "dewp": 20.0,
            "wspd": 12.0,
            "wdir": 90,
            "visib": 5.0,
            "rawOb": "METAR VIDP 040300Z 09012KT 5000 HZ FEW030 28/20 Q1012 NOSIG"
        }
        norm = adapter.normalize(mock_raw)
        self.assertEqual(norm["station"], "VIDP")
        self.assertEqual(norm["temp_c"], 28.0)
        self.assertEqual(norm["synthetic"], 0)
        self.assertEqual(norm["provenance"]["source_id"], "awc_weather")

    def test_scheduler_sync_and_freshness(self):
        sched = IngestionScheduler()
        results = sched.sync_all()
        self.assertIn("adsb_lol", results)
        self.assertIn("awc_weather", results)
        self.assertIn(results["adsb_lol"]["status"], ["SUCCESS", "FALLBACK_USED"])
        self.assertIn(results["awc_weather"]["status"], ["SUCCESS", "FALLBACK_USED"])

    def test_error_recovery_graceful(self):
        adapter = ADSBADotLolAdapter()
        # Test handling of empty/malformed response
        malformed = adapter.normalize({})
        self.assertEqual(malformed["synthetic"], 0)
        self.assertEqual(malformed["flight_state"], "UNKNOWN")

if __name__ == "__main__":
    unittest.main()
