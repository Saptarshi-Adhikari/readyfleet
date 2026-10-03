import unittest
import tempfile
import os
import shutil
from gen.db import get_connection
from gen.generate import generate_all_data
from models.train import train_rul_models
from models.infer import run_batch_inference
from core.state import load_fleet_state
from core.aggregator import evaluate_fleet_availability
from core.whatif import apply_whatif_lever
from core.drivers import rank_nmc_drivers
from core.cannibal import evaluate_cannibalization_proposal, record_cannibalization_debt
from core.audit import append_audit_entry, verify_audit_log

class TestDecisionLogicPhase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_decision.db")
        generate_all_data(self.db_path, seed=42)
        train_rul_models(self.db_path)
        run_batch_inference(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_availability_aggregator(self):
        state = load_fleet_state(self.db_path)
        eval_res = evaluate_fleet_availability(state)
        
        self.assertIn("tail_states", eval_res)
        self.assertIn("mc_forecast", eval_res)
        self.assertEqual(len(eval_res["mc_forecast"]), 7)
        self.assertEqual(eval_res["data_class"], "synthetic")

    def test_whatif_sub200ms_latency(self):
        state = load_fleet_state(self.db_path)
        lever = {"type": "expedite_spares", "part_no": "PART-ENG-01"}
        eval_res, meta = apply_whatif_lever(state, lever)
        
        self.assertLess(meta["latency_ms"], 200.0)
        self.assertEqual(meta["lever_applied"], lever)

    def test_nmc_driver_ranking(self):
        state = load_fleet_state(self.db_path)
        drivers = rank_nmc_drivers(state)
        self.assertIsInstance(drivers, list)

    def test_cannibalization_guardrails(self):
        state = load_fleet_state(self.db_path)
        
        # Test Refusal 1: Donor priority equal/higher than recipient
        approved, msg, _ = evaluate_cannibalization_proposal(state, donor_tail="SYN-01", recipient_tail="SYN-02", comp_class="engine")
        if state["aircraft"][state["aircraft"]["tail_no"]=="SYN-01"]["mission_priority"].values[0] <= state["aircraft"][state["aircraft"]["tail_no"]=="SYN-02"]["mission_priority"].values[0]:
            self.assertFalse(approved)
            self.assertIn("Refused", msg)

    def test_hash_chained_audit_log(self):
        h1 = append_audit_entry("COMMANDER", "TEST_ACTION_1", "TAIL", "SYN-01", {"test": 1}, db_path=self.db_path)
        h2 = append_audit_entry("COMMANDER", "TEST_ACTION_2", "TAIL", "SYN-02", {"test": 2}, db_path=self.db_path)
        
        self.assertTrue(verify_audit_log(self.db_path))

if __name__ == "__main__":
    unittest.main()
