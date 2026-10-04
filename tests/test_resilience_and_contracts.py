"""
READYFLEET Rate Limiting, Resilience, & API Contract Tests
===========================================================
1. Verification of all API endpoints required by the frontend contracts.
2. Rate-limiting backoff test (429 handling & state transitions).
3. In-flight deduplication guard test.
4. Source outage simulation (timeout / 504 -> backoff -> STALE/OFFLINE state).
"""

import unittest
import os
import time
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
from data_sources.scheduler import DataIngestionScheduler, BACKOFF_SEQUENCE
from data_sources.adsb_lol import ADSBLolDataSource
from data_sources.awc_weather import AWCWeatherDataSource


class TestAPIContractsAndResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["READYFLEET_DATA_MODE"] = "REAL_ONLY"
        cls.client = TestClient(app)

    def test_all_frontend_endpoints_exist(self):
        """Verify API contract for every endpoint consumed by the frontend."""
        endpoints = [
            ("/api/health", 200),
            ("/api/data-mode", 200),
            ("/api/data-sources", 200),
            ("/api/fleet/status", 200),
            ("/api/fleet/forecast", 200),
            ("/api/drivers", 200),
            ("/api/predictions/summary", 200),
        ]
        for url, expected_status in endpoints:
            res = self.client.get(url)
            self.assertEqual(
                res.status_code,
                expected_status,
                f"Endpoint {url} returned HTTP {res.status_code} instead of {expected_status}",
            )

    def test_sse_endpoint_connects(self):
        """Verify SSE endpoint returns text/event-stream header."""
        res = self.client.get("/api/stream/events")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))

    def test_adsb_429_rate_limit_backoff(self):
        """Test HTTP 429 response handling and backoff pause logic."""
        scheduler = DataIngestionScheduler()

        # Mock adapter returning HTTP 429
        mock_adapter = MagicMock()
        mock_adapter.fetch_raw.return_value = {
            "status_code": 429,
            "records": [],
            "latency_ms": 45.0,
            "error": "HTTP 429: Too Many Requests",
            "retry_after": 30,
        }
        scheduler.sources["adsb_lol"] = mock_adapter

        # Step 1: Trigger sync -> should record RATE_LIMITED and backoff
        res1 = scheduler.sync_source("adsb_lol")
        self.assertEqual(res1["status"], "RATE_LIMITED")
        self.assertEqual(scheduler.freshness["adsb_lol"]["status"], "RATE_LIMITED")
        self.assertEqual(scheduler.freshness["adsb_lol"]["rate_limit_count"], 1)

        # Step 2: Trigger immediate second sync while in backoff -> must NOT call API
        res2 = scheduler.sync_source("adsb_lol")
        self.assertTrue(res2.get("cached", False))
        # Adapter fetch_raw should have been called EXACTLY ONCE
        mock_adapter.fetch_raw.assert_called_once()

    def test_awc_timeout_stale_handling(self):
        """Test AWC timeout handling and transition to DEGRADED/OFFLINE."""
        scheduler = DataIngestionScheduler()

        mock_adapter = MagicMock()
        mock_adapter.fetch_raw.return_value = {
            "status_code": 504,
            "records": [],
            "latency_ms": 8000.0,
            "error": "The read operation timed out",
            "retry_after": None,
        }
        scheduler.sources["awc_weather"] = mock_adapter

        res = scheduler.sync_source("awc_weather")
        self.assertIn(res["status"], ("DEGRADED", "OFFLINE"))
        self.assertEqual(scheduler.freshness["awc_weather"]["timeout_count"], 1)

    def test_inflight_deduplication_guard(self):
        """Test that parallel triggers for an in-flight fetch return cached state without calling fetch twice."""
        scheduler = DataIngestionScheduler()
        mock_adapter = MagicMock()
        
        # Simulate in-flight flag
        scheduler._in_flight["adsb_lol"] = True
        scheduler.sources["adsb_lol"] = mock_adapter

        res = scheduler.sync_source("adsb_lol")
        self.assertTrue(res.get("cached", False))
        mock_adapter.fetch_raw.assert_not_called()


if __name__ == "__main__":
    unittest.main()
