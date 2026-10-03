import unittest
from data_sources.opensky import OpenSkyDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.authorized_hums import AuthorizedHUMSDataSource
from models.registry import load_model_artifact

class TestRealDataSemantics(unittest.TestCase):
    def test_opensky_neutral_semantics(self):
        src = OpenSkyDataSource()
        # Raw state with on_ground = True
        raw_ground = ["a123", "N123", "US", 0, 0, 0, 0, 0, True]
        norm_ground = src.normalize(raw_ground)
        self.assertEqual(norm_ground["operational_state"], "ON_GROUND")
        self.assertEqual(norm_ground["status"], "UNKNOWN")  # Does not invent MC/PMC/NMC

        # Raw state with on_ground = False
        raw_air = ["a123", "N123", "US", 0, 0, 0, 0, 1000, False]
        norm_air = src.normalize(raw_air)
        self.assertEqual(norm_air["operational_state"], "AIRBORNE")
        self.assertEqual(norm_air["status"], "UNKNOWN")

    def test_faa_sdr_maintenance_semantics(self):
        src = FAASDRDataSource()
        raw = {"n_number": "999", "component_type": "AVIONICS", "report_date": "2026-06-01", "labor_hours": 3.0}
        norm = src.normalize(raw)
        self.assertEqual(norm["task_type"], "unscheduled")
        self.assertEqual(norm["comp_class"], "avionics")

    def test_hums_adapter(self):
        src = AuthorizedHUMSDataSource()
        raw = {"aircraft_id": "AC-100", "comp_class": "ENGINE", "cycle": 50, "sensor_name": "s1", "sensor_value": 520.5, "target_rul": 75.0}
        norm = src.normalize(raw)
        self.assertEqual(norm["target_rul"], 75.0)
        self.assertEqual(norm["synthetic"], 0)

    def test_model_registry_provenance(self):
        model, met = load_model_artifact("engine")
        self.assertIn("dataset_name", met)
        self.assertIn("data_type", met)
        self.assertEqual(met["data_type"], "BENCHMARK_SYNTHETIC")

if __name__ == "__main__":
    unittest.main()
