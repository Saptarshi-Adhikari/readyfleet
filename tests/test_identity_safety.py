import unittest
import os
from core.identity import resolve_trusted_twin_identity
from data_sources.adsb_lol import ADSBLolDataSource
from data_sources.awc_weather import AWCWeatherDataSource
from core.state import load_fleet_state
from core.aggregator import evaluate_fleet_availability

class TestIdentityAndReadinessSafety(unittest.TestCase):

    def test_valid_trusted_identity_match(self):
        # Exact ICAO24 match
        obs1 = {"hex": "A1B2C3", "flight": "VT-RF001"}
        twin1 = resolve_trusted_twin_identity(obs1)
        self.assertEqual(twin1, "RF-001")

        # Exact registration match
        obs2 = {"registration": "VT-RF002"}
        twin2 = resolve_trusted_twin_identity(obs2)
        self.assertEqual(twin2, "RF-002")

    def test_unknown_identity_rejected(self):
        obs = {"hex": "UNKNOWN999", "flight": "CIV-9999"}
        twin = resolve_trusted_twin_identity(obs)
        self.assertIsNone(twin, "Untrusted aircraft observation must NOT match a defence twin")

    def test_fuzzy_and_proximity_rejected(self):
        # Fuzzy name match
        obs_fuzzy = {"flight": "RF-001-NEAR"}
        self.assertIsNone(resolve_trusted_twin_identity(obs_fuzzy))

        # Geographic proximity alone
        obs_prox = {"lat": 28.56, "lon": 77.10, "flight": "GUEST-01"}
        self.assertIsNone(resolve_trusted_twin_identity(obs_prox))

    def test_adsb_cannot_change_readiness(self):
        state_before = load_fleet_state()
        eval_before = evaluate_fleet_availability(state_before)
        
        # Simulate ADS-B operational normalization
        adapter = ADSBLolDataSource()
        mock_ac = {"hex": "A1B2C3", "flight": "VT-RF001", "alt_baro": "ground"}
        norm = adapter.normalize(mock_ac)

        # Operational status must be ON_GROUND, but fleet readiness status remains UNKNOWN / unchanged
        self.assertEqual(norm["operational_state"], "ON_GROUND")
        self.assertEqual(norm["status"], "UNKNOWN")

        # Evaluate fleet readiness again - must be identical
        state_after = load_fleet_state()
        eval_after = evaluate_fleet_availability(state_after)

        self.assertEqual(eval_before["summary"]["mc_count"], eval_after["summary"]["mc_count"])
        self.assertEqual(eval_before["summary"]["nmc_count"], eval_after["summary"]["nmc_count"])

    def test_weather_cannot_change_readiness(self):
        state_before = load_fleet_state()
        eval_before = evaluate_fleet_availability(state_before)

        adapter = AWCWeatherDataSource()
        mock_metar = {"icaoId": "VIDP", "temp": 45.0, "visib": 0.5, "rawOb": "METAR STORM"}
        norm = adapter.normalize(mock_metar)

        # METAR normalizes as weather observation, not component health
        self.assertEqual(norm["station"], "VIDP")
        self.assertNotIn("predicted_rul_h", norm)

        state_after = load_fleet_state()
        eval_after = evaluate_fleet_availability(state_after)
        self.assertEqual(eval_before["summary"]["mc_count"], eval_after["summary"]["mc_count"])

    def test_end_to_end_identity_isolation_acceptance(self):
        # Case 1: Trusted identity observation
        trusted_obs = {"hex": "A1B2C3", "flight": "VT-RF001", "alt_baro": 20000}
        adapter = ADSBLolDataSource()
        norm_trusted = adapter.normalize(trusted_obs)
        matched_twin = resolve_trusted_twin_identity(trusted_obs)

        self.assertEqual(matched_twin, "RF-001")
        self.assertEqual(norm_trusted["operational_state"], "AIRBORNE")

        # Case 2: Untrusted identity observation
        untrusted_obs = {"hex": "FF9900", "flight": "UNKNOWN-JET"}
        norm_untrusted = adapter.normalize(untrusted_obs)
        unmatched_twin = resolve_trusted_twin_identity(untrusted_obs)

        self.assertIsNone(unmatched_twin)
        self.assertEqual(norm_untrusted["operational_state"], "AIRBORNE")
        # Ensure defence aircraft twins remain untouched for untrusted observations

if __name__ == "__main__":
    unittest.main()
