import unittest
from fastapi.testclient import TestClient
from api.main import app
from gen.generate import generate_all_data
from models.train import train_rul_models
from models.infer import run_batch_inference
import tempfile
import os
import shutil

class TestAPIPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generate_all_data(seed=42)
        train_rul_models()
        run_batch_inference()
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "synthetic")

    def test_fleet_status_contract(self):
        response = self.client.get("/api/fleet/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "synthetic")
        self.assertIn("mc_count", data)
        self.assertIn("tail_states", data)

    def test_fleet_forecast_contract(self):
        response = self.client.get("/api/fleet/forecast")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "synthetic")
        self.assertEqual(len(data["mc_forecast"]), 7)

    def test_whatif_endpoint(self):
        payload = {"lever": {"type": "expedite_spares", "part_no": "PART-ENG-01"}}
        response = self.client.post("/api/whatif", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data_class"], "synthetic")
        self.assertIn("latency_ms", data)

    def test_audit_verify_endpoint(self):
        response = self.client.get("/api/audit/verify")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["chain_valid"])

if __name__ == "__main__":
    unittest.main()
