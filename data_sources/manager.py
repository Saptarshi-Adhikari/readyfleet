"""
READYFLEET Data Source Manager
================================
Controls which data sources are active based on READYFLEET_DATA_MODE env var.

DATA MODES:
    HYBRID (default) : Real sources used where available; synthetic fallback where not.
    REAL_ONLY        : Only real/historical data. Synthetic sources raise errors if accessed.
    DEMO_SYNTHETIC   : Full synthetic demo mode (original behaviour).

Synthetic is NEVER blocked entirely — it powers the ML training pipeline
and digital twin simulation. But in REAL_ONLY mode it cannot populate
any API response or UI value.
"""

import os
from typing import Dict, Any, Tuple

from data_sources.synthetic import SyntheticDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.opensky import OpenSkyDataSource
from data_sources.adsb_lol import ADSBLolDataSource
from data_sources.awc_weather import AWCWeatherDataSource

def get_data_mode() -> str:
    return os.environ.get("READYFLEET_DATA_MODE", "REAL_ONLY")

READYFLEET_DATA_MODE = get_data_mode()

# ─────────────────────────────────────────────────────────────────────────────
# Source registry type annotations
# ─────────────────────────────────────────────────────────────────────────────
SourceRegistry = Dict[str, Any]
ProvenanceSummary = Dict[str, Any]


def get_active_data_sources() -> Tuple[SourceRegistry, ProvenanceSummary]:
    """
    Return the active data source registry and a provenance summary dict.

    In REAL_ONLY mode the synthetic source is included but tagged as
    BLOCKED so callers know not to use it for display values.
    """
    mode = get_data_mode()
    adsb = ADSBLolDataSource()
    awc = AWCWeatherDataSource()
    faa = FAASDRDataSource()
    syn = SyntheticDataSource()

    sources: SourceRegistry = {
        "adsb_lol": adsb,
        "awc_weather": awc,
        "faa_sdr": faa,
        "synthetic": syn,
    }

    # Determine live connectivity
    adsb_live = adsb.health_check() if mode in ("LIVE_REAL", "HYBRID", "REAL_ONLY") else False
    awc_live = awc.health_check() if mode in ("LIVE_REAL", "HYBRID", "REAL_ONLY") else False
    faa_ready = mode in ("HISTORICAL_REAL", "HYBRID", "REAL_ONLY")
    syn_blocked = mode == "REAL_ONLY"

    provenance_summary: ProvenanceSummary = {
        "mode": mode,
        "sources": {
            "ops": {
                "source_id": "adsb_lol",
                "badge": "LIVE REAL (adsb.lol)" if adsb_live else "OFFLINE → NO DATA",
                "online": adsb_live,
            },
            "weather": {
                "source_id": "awc_weather",
                "badge": "LIVE REAL (AWC METAR)" if awc_live else "OFFLINE → NO DATA",
                "online": awc_live,
            },
            "maintenance": {
                "source_id": "faa_sdr",
                "badge": "HISTORICAL REAL (FAA SDRS)" if faa_ready else "DISABLED",
                "available": faa_ready,
            },
            "health": {
                "source_id": "n_cmapss",
                "badge": "BENCHMARK (N-CMAPSS)",
                "type": "BENCHMARK_SYNTHETIC",
            },
            "logistics": {
                "source_id": "synthetic",
                "badge": "BLOCKED (REAL_ONLY mode)" if syn_blocked else "SYNTHETIC FALLBACK",
                "blocked": syn_blocked,
            },
        },
        "synthetic_blocked": syn_blocked,
        "data_gap_notice": (
            "No live military HUMS or classified maintenance data is available. "
            "Fleet readiness figures are simulation-derived. "
            "Production deployment requires direct MRO integration."
        ),
    }

    return sources, provenance_summary
