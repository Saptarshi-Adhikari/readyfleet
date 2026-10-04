import unittest
from data_sources.base import BaseDataSource
from data_sources.synthetic import SyntheticDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.opensky import OpenSkyDataSource
from data_sources.manager import get_active_data_sources

class TestDataIntegrationLayer(unittest.TestCase):
    def test_synthetic_source(self):
        src = SyntheticDataSource()
        self.assertTrue(src.health_check())
        self.assertEqual(src.source_type, "SYNTHETIC")

    def test_faa_sdr_normalization(self):
        src = FAASDRDataSource()
        raw = {"n_number": "12345", "component_type": "ENGINE", "report_date": "2026-05-10", "labor_hours": 6.5, "control_no": "SDR-999"}
        norm = src.normalize(raw)
        self.assertEqual(norm["tail_no"], "REAL-12345")
        self.assertEqual(norm["comp_class"], "engine")
        self.assertEqual(norm["synthetic"], 0)
        self.assertEqual(norm["provenance"]["source_name"], "FAA_SDR")

    def test_opensky_normalization(self):
        src = OpenSkyDataSource()
        raw_state = ["a123b4", "N12345  ", "United States", 1600000000, 1600000000, -120.0, 38.0, 10000, False]
        norm = src.normalize(raw_state)
        self.assertEqual(norm["tail_no"], "ADS-N12345")
        self.assertEqual(norm["synthetic"], 0)
        self.assertEqual(norm["provenance"]["source_name"], "OpenSky_Network")

    def test_data_manager_provenance(self):
        sources, prov = get_active_data_sources()
        self.assertIn("mode", prov)
        self.assertIn("sources", prov)
        self.assertIn("health", prov["sources"])

if __name__ == "__main__":
    unittest.main()
