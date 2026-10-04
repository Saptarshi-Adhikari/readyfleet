"""
READYFLEET Data Ingestion Scheduler
=====================================
Background scheduler that syncs all configured real data sources
on a controlled, rate-limit safe periodic schedule.

Design principles:
- Single background ingestion owner (in-flight deduplication guards).
- Conservative configurable polling intervals (ADSB_POLL_INTERVAL_SECONDS, AWC_POLL_INTERVAL_SECONDS).
- HTTP 429 rate limiting with exponential backoff & Retry-After header parsing.
- Explicit timeouts (connect/read) and error state machines.
- Server-side caching of last good payloads with STALE/RATE_LIMITED/OFFLINE markers.
- Zero fake/synthetic fallback numbers in REAL_ONLY mode.
"""

import os
import time
import datetime
import random
from typing import Dict, Any, List, Optional
from data_sources.adsb_lol import ADSBLolDataSource
from data_sources.awc_weather import AWCWeatherDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.synthetic import SyntheticDataSource

BACKOFF_SEQUENCE = [15, 30, 60, 120, 300]


class DataIngestionScheduler:
    """
    Manages all data source adapters, rate-limiting backoffs,
    in-flight request deduplication, and authoritative metrics.
    """

    def __init__(self):
        self.sources: Dict[str, Any] = {
            "adsb_lol": ADSBLolDataSource(),
            "awc_weather": AWCWeatherDataSource(),
            "faa_sdr": FAASDRDataSource(),
            "synthetic": SyntheticDataSource(),
        }

        # Configurable polling intervals (in seconds)
        self.adsb_poll_interval = int(os.environ.get("ADSB_POLL_INTERVAL_SECONDS", "60"))
        self.awc_poll_interval = int(os.environ.get("AWC_POLL_INTERVAL_SECONDS", "180"))

        # In-flight deduplication guard
        self._in_flight: Dict[str, bool] = {
            "adsb_lol": False,
            "awc_weather": False,
        }

        # Authoritative freshness, failure counters, and metrics state per source
        self.freshness: Dict[str, Dict[str, Any]] = {
            "adsb_lol": {
                "source_id": "adsb_lol",
                "name": "adsb.lol Open-Data ADS-B",
                "domain": "Operations",
                "source_type": "LIVE_REAL",
                "status": "ONLINE",
                "freshness": "FRESH",
                "enabled": True,
                "consecutive_failures": 0,
                "last_success": None,
                "last_failure": None,
                "last_status_code": 200,
                "next_retry_at": 0.0,
                "current_backoff": 0,
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "rate_limit_count": 0,
                "timeout_count": 0,
                "average_latency_ms": 0.0,
                "last_latency_ms": 0.0,
                "last_sync": "NEVER",
                "record_count": 0,
                "last_good_payload": [],
                "last_good_timestamp": None,
            },
            "awc_weather": {
                "source_id": "awc_weather",
                "name": "NOAA AWC METAR",
                "domain": "Weather",
                "source_type": "LIVE_REAL",
                "status": "ONLINE",
                "freshness": "FRESH",
                "enabled": True,
                "consecutive_failures": 0,
                "last_success": None,
                "last_failure": None,
                "last_status_code": 200,
                "next_retry_at": 0.0,
                "current_backoff": 0,
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "rate_limit_count": 0,
                "timeout_count": 0,
                "average_latency_ms": 0.0,
                "last_latency_ms": 0.0,
                "last_sync": "NEVER",
                "record_count": 0,
                "last_good_payload": [],
                "last_good_timestamp": None,
            },
            "faa_sdrs": {
                "source_id": "faa_sdrs",
                "name": "FAA Service Difficulty Reports",
                "domain": "Maintenance",
                "source_type": "HISTORICAL_REAL",
                "status": "READY",
                "freshness": "CURRENT",
                "enabled": True,
                "consecutive_failures": 0,
                "last_sync": "BATCH_LOADED",
                "note": "FAA SDRS — historical batch dataset. No live API polling.",
            },
            "n_cmapss": {
                "source_id": "n_cmapss",
                "name": "NASA N-CMAPSS Turbofan Benchmark",
                "domain": "Health / RUL",
                "source_type": "BENCHMARK_SYNTHETIC",
                "status": "MODEL_ONLY",
                "freshness": "CURRENT",
                "enabled": True,
                "consecutive_failures": 0,
                "last_sync": "STATIC_DATASET",
                "note": "N-CMAPSS — static NASA benchmark dataset used for RUL model training.",
            },
            "synthetic": {
                "source_id": "synthetic",
                "name": "READYFLEET Synthetic Generator",
                "domain": "Logistics / Simulation",
                "source_type": "SYNTHETIC",
                "status": "BLOCKED",
                "freshness": "BLOCKED",
                "enabled": False,
                "consecutive_failures": 0,
                "last_sync": "N/A",
                "note": "Synthetic generator — blocked in REAL_ONLY mode.",
            },
        }

    def sync_source(self, source_id: str) -> Dict[str, Any]:
        """
        Sync a single live source safely with backoff & deduplication.
        """
        if source_id not in ("adsb_lol", "awc_weather"):
            return {"source_id": source_id, "status": "static_skipped"}

        metrics = self.freshness[source_id]
        now_ts = time.time()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Backoff guard: check if source is currently paused in rate limit / outage backoff
        if now_ts < metrics["next_retry_at"]:
            return {
                "source_id": source_id,
                "status": metrics["status"],
                "freshness": metrics["freshness"],
                "message": f"Source paused due to backoff. Next retry at {metrics['next_retry_at']}",
                "cached": True,
            }

        # 2. In-flight guard: prevent duplicate requests for the same source
        if self._in_flight.get(source_id, False):
            return {
                "source_id": source_id,
                "status": metrics["status"],
                "message": "Fetch already in progress (in-flight deduplicated).",
                "cached": True,
            }

        self._in_flight[source_id] = True
        adapter = self.sources[source_id]

        try:
            metrics["request_count"] += 1
            res = adapter.fetch_raw()

            status_code = res.get("status_code", 500)
            records = res.get("records", [])
            latency = res.get("latency_ms", 0.0)
            error_msg = res.get("error")
            retry_after = res.get("retry_after")

            metrics["last_status_code"] = status_code
            metrics["last_latency_ms"] = latency
            # Moving average latency
            prev_avg = metrics["average_latency_ms"]
            sc = metrics["request_count"]
            metrics["average_latency_ms"] = (prev_avg * (sc - 1) + latency) / max(sc, 1)

            if status_code == 200:
                metrics["status"] = "ONLINE"
                metrics["freshness"] = "FRESH"
                metrics["consecutive_failures"] = 0
                metrics["current_backoff"] = 0
                metrics["next_retry_at"] = 0.0
                metrics["last_success"] = now_str
                metrics["last_sync"] = now_str
                metrics["success_count"] += 1
                metrics["record_count"] = len(records)
                metrics["last_good_payload"] = records
                metrics["last_good_timestamp"] = now_str

                return {
                    "source_id": source_id,
                    "status": "ONLINE",
                    "freshness": "FRESH",
                    "records_ingested": len(records),
                    "timestamp": now_str,
                    "latency_ms": latency,
                }
            elif status_code == 429:
                metrics["rate_limit_count"] += 1
                metrics["failure_count"] += 1
                metrics["consecutive_failures"] += 1
                metrics["last_failure"] = now_str
                metrics["status"] = "RATE_LIMITED"
                metrics["freshness"] = "STALE" if metrics["last_good_timestamp"] else "DATA_UNAVAILABLE"

                # Calculate exponential backoff
                backoff_idx = min(metrics["consecutive_failures"] - 1, len(BACKOFF_SEQUENCE) - 1)
                delay_sec = retry_after if retry_after is not None else BACKOFF_SEQUENCE[backoff_idx]
                # Add 0-2s jitter
                delay_sec += random.uniform(0.5, 2.0)
                metrics["current_backoff"] = delay_sec
                metrics["next_retry_at"] = now_ts + delay_sec

                return {
                    "source_id": source_id,
                    "status": "RATE_LIMITED",
                    "freshness": metrics["freshness"],
                    "error": error_msg or "HTTP 429 Too Many Requests",
                    "next_retry_at": metrics["next_retry_at"],
                }
            else:
                metrics["failure_count"] += 1
                metrics["consecutive_failures"] += 1
                metrics["last_failure"] = now_str
                if status_code == 504 or "timeout" in str(error_msg).lower():
                    metrics["timeout_count"] += 1

                metrics["status"] = "OFFLINE" if metrics["consecutive_failures"] >= 3 else "DEGRADED"
                metrics["freshness"] = "STALE" if metrics["last_good_timestamp"] else "DATA_UNAVAILABLE"

                backoff_idx = min(metrics["consecutive_failures"] - 1, len(BACKOFF_SEQUENCE) - 1)
                delay_sec = BACKOFF_SEQUENCE[backoff_idx] + random.uniform(0.5, 2.0)
                metrics["current_backoff"] = delay_sec
                metrics["next_retry_at"] = now_ts + delay_sec

                return {
                    "source_id": source_id,
                    "status": metrics["status"],
                    "freshness": metrics["freshness"],
                    "error": error_msg or f"HTTP {status_code}",
                    "next_retry_at": metrics["next_retry_at"],
                }
        finally:
            self._in_flight[source_id] = False

    def sync_all(self) -> Dict[str, Any]:
        """
        Sync all live sources according to their schedule.
        """
        results = {}
        for s_id in ["adsb_lol", "awc_weather"]:
            results[s_id] = self.sync_source(s_id)

        for s_id in ["faa_sdrs", "n_cmapss", "synthetic"]:
            results[s_id] = {
                "source_id": s_id,
                "status": self.freshness.get(s_id, {}).get("status", "UNKNOWN"),
                "freshness": self.freshness.get(s_id, {}).get("freshness", "UNKNOWN"),
            }

        return results


# Shared singleton instance
scheduler_instance = DataIngestionScheduler()
