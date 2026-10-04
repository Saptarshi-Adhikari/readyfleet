"""
READYFLEET Production REAL_ONLY Mode & Isolation Verification Tests
===================================================================
Tests to verify:
1. Default DATA_MODE is REAL_ONLY.
2. Synthetic fallback is blocked from populating production API outputs in REAL_ONLY mode.
3. Benchmark N-CMAPSS data is classified as MODEL_ONLY / PREDICTED, never as live aircraft telemetry.
4. Unavailable logistics (spares / crew) return N/A instead of fake synthetic numbers.
5. Live endpoints carry explicit provenance metadata.
"""

import unittest
import os
from fastapi.testclient import TestClient

from api.main import app
from data_sources.manager import get_data_mode, get_active_data_sources
from core.provenance import build_fleet_provenance_summary, KNOWN_SOURCES


class TestProductionRealOnlyMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["READYFLEET_DATA_MODE"] = "REAL_ONLY"
        cls.client = TestClient(app)

    def test_default_data_mode_is_real_only(self):
        self.assertEqual(get_data_mode(), "REAL_ONLY")

    def test_api_health_reports_real_only(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_mode"], "REAL_ONLY")

    def test_api_data_mode_endpoint_provenance(self):
        response = self.client.get("/api/data-mode")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_mode"], "REAL_ONLY")
        self.assertTrue(data["synthetic_blocked"])
        self.assertIn("provenance", data)

    def test_api_data_sources_registry(self):
        response = self.client.get("/api/data-sources")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_mode"], "REAL_ONLY")
        sources = {s["source_id"]: s for s in data["sources"]}
        
        # Verify active real sources
        self.assertEqual(sources["adsb_lol"]["type"], "LIVE_REAL")
        self.assertEqual(sources["awc_weather"]["type"], "LIVE_REAL")
        self.assertEqual(sources["faa_sdrs"]["type"], "HISTORICAL_REAL")
        
        # Verify benchmark isolation
        self.assertEqual(sources["n_cmapss"]["type"], "BENCHMARK_SYNTHETIC")
        self.assertEqual(sources["n_cmapss"]["status"], "MODEL_ONLY")
        
        # Verify synthetic blocking
        self.assertEqual(sources["synthetic"]["type"], "SYNTHETIC")
        self.assertIn("BLOCKED", sources["synthetic"]["status"])
        self.assertFalse(sources["synthetic"]["enabled"])
        
        # Verify missing military sources
        self.assertEqual(sources["defence_hums"]["type"], "NOT_AVAILABLE")
        self.assertEqual(sources["military_mro"]["type"], "NOT_AVAILABLE")

    def test_fleet_status_carries_real_only_data_class(self):
        response = self.client.get("/api/fleet/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "REAL_ONLY")

    def test_predictions_summary_marked_predicted(self):
        response = self.client.get("/api/predictions/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "PREDICTED")
        self.assertIn("provenance_note", data)

    def test_maintenance_overview_synthetic_isolation(self):
        response = self.client.get("/api/maintenance/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "REAL_ONLY")
        # Synthetic spares and crew must be empty / N/A in REAL_ONLY mode
        self.assertEqual(data["spares"], [])
        self.assertEqual(data["crew"], [])
        self.assertIn("N/A", data["spares_status"])
        self.assertIn("N/A", data["crew_status"])


if __name__ == "__main__":
    unittest.main()
