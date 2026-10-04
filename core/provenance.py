"""
READYFLEET Provenance Tracking System
======================================
Every data point that enters READYFLEET must carry a provenance record.

Provenance record fields:
    source_id       : Identifier of the data source (e.g. "faa_sdr", "adsb_lol", "synthetic")
    source_type     : Classification: LIVE_REAL | HISTORICAL_REAL | BENCHMARK_SYNTHETIC | SYNTHETIC
    dataset_name    : Human-readable dataset name (e.g. "FAA SDRS", "N-CMAPSS")
    license         : License / usage terms (e.g. "Public Domain", "CC-BY 4.0")
    ingest_ts       : ISO-8601 ingestion timestamp
    record_id       : Unique record identifier within source
    is_synthetic    : 1 if synthetic/benchmark, 0 if real
    data_quality    : GOOD | DEGRADED | UNKNOWN
    gap_present     : True if this record fills a gap via fallback
    fallback_reason : If gap_present, why fallback was used
"""

import datetime
from typing import Dict, Any, Optional

# ---------------------------------------------------------------------------
# Canonical source registry — a single source of truth for all known sources
# ---------------------------------------------------------------------------
KNOWN_SOURCES: Dict[str, Dict[str, str]] = {
    "adsb_lol": {
        "name": "adsb.lol Open-Data ADS-B",
        "source_type": "LIVE_REAL",
        "domain": "Operations / Airspace Telemetry",
        "license": "Public Domain / Open-Data",
        "description": "Live ADS-B position & flight state from adsb.lol community feed.",
        "limitation": "Provides civil/GA aircraft operational state only. "
                      "CANNOT infer MC/PMC/NMC, health, or maintenance status.",
    },
    "awc_weather": {
        "name": "NOAA AWC METAR",
        "source_type": "LIVE_REAL",
        "domain": "Weather / Meteorology",
        "license": "Public Domain (NOAA)",
        "description": "Real-time METAR weather observations from Aviation Weather Center.",
        "limitation": "Weather context only. Not linked to any aircraft readiness decision.",
    },
    "faa_sdr": {
        "name": "FAA Service Difficulty Reports (SDRS)",
        "source_type": "HISTORICAL_REAL",
        "domain": "Maintenance / Safety Reports",
        "license": "Public Domain (FAA)",
        "description": "Historical real-world maintenance difficulty reports from FAA SDRS database.",
        "limitation": "Civil aviation fleet only. Provides component failure frequency data "
                      "to train maintenance risk models — not a direct readiness input.",
    },
    "ntsb": {
        "name": "NTSB Aviation Accident Database",
        "source_type": "HISTORICAL_REAL",
        "domain": "Safety / Accident Analysis",
        "license": "Public Domain (NTSB)",
        "description": "Historical aviation accident and incident investigation data.",
        "limitation": "Civil accident data. Used to compute component failure risk priors.",
    },
    "n_cmapss": {
        "name": "NASA N-CMAPSS Turbofan Benchmark",
        "source_type": "BENCHMARK_SYNTHETIC",
        "domain": "Health / RUL Model Training",
        "license": "NASA Open Dataset (CC-BY)",
        "description": "NASA turbofan engine degradation simulation dataset used to train RUL models.",
        "limitation": "Simulated sensor degradation data. ML model predictions must be clearly "
                      "labelled as BENCHMARK-TRAINED and NOT as real engine health readings.",
    },
    "synthetic": {
        "name": "READYFLEET Synthetic Generator",
        "source_type": "SYNTHETIC",
        "domain": "Fleet Simulation / Demo",
        "license": "Internal / Demo Only",
        "description": "Procedurally generated synthetic fleet data for simulation and demo purposes.",
        "limitation": "All values are fabricated. MUST NOT be displayed as real operational data.",
    },
}


def make_provenance(
    source_id: str,
    record_id: str,
    data_quality: str = "GOOD",
    gap_present: bool = False,
    fallback_reason: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a full provenance record for a data point."""
    src = KNOWN_SOURCES.get(source_id, {
        "name": source_id,
        "source_type": "UNKNOWN",
        "domain": "Unknown",
        "license": "Unknown",
        "description": "Unregistered source.",
        "limitation": "Provenance unknown.",
    })

    return {
        "source_id": source_id,
        "source_name": src["name"],
        "source_type": src["source_type"],
        "domain": src["domain"],
        "license": src["license"],
        "limitation": src["limitation"],
        "record_id": record_id,
        "ingest_ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "is_synthetic": 1 if src["source_type"] in ("SYNTHETIC", "BENCHMARK_SYNTHETIC") else 0,
        "data_quality": data_quality,
        "gap_present": gap_present,
        "fallback_reason": fallback_reason,
        **(extra or {}),
    }


def provenance_badge(prov: Dict[str, Any]) -> str:
    """Return a short display badge string for a provenance record."""
    stype = prov.get("source_type", "UNKNOWN")
    name = prov.get("source_name", prov.get("source_id", "?"))
    if stype == "LIVE_REAL":
        return f"LIVE REAL ({name})"
    if stype == "HISTORICAL_REAL":
        return f"HISTORICAL REAL ({name})"
    if stype == "BENCHMARK_SYNTHETIC":
        return f"BENCHMARK ({name})"
    if stype == "SYNTHETIC":
        return f"SYNTHETIC ({name})"
    return f"UNKNOWN ({name})"


def is_real(prov: Dict[str, Any]) -> bool:
    """Return True if provenance indicates actual (non-synthetic) data."""
    return prov.get("is_synthetic", 1) == 0


def assert_no_synthetic_in_real_mode(prov: Dict[str, Any], data_mode: str) -> None:
    """Raise ValueError if synthetic data is used in REAL_ONLY mode."""
    if data_mode == "REAL_ONLY" and prov.get("is_synthetic", 1) == 1:
        raise ValueError(
            f"DATA_MODE=REAL_ONLY: Synthetic/benchmark data from "
            f"'{prov.get('source_id')}' cannot be used in this mode. "
            f"No data -> No number."
        )


# ---------------------------------------------------------------------------
# Fleet-level provenance summary (for API /api/data-mode)
# ---------------------------------------------------------------------------
def build_fleet_provenance_summary(data_mode: str) -> Dict[str, Any]:
    """Return a structured provenance summary for the full fleet."""
    return {
        "mode": data_mode,
        "sources": {
            "operations": {
                "source_id": "adsb_lol",
                "source_type": "LIVE_REAL",
                "badge": "LIVE REAL (adsb.lol)",
                "limitation": KNOWN_SOURCES["adsb_lol"]["limitation"],
            },
            "weather": {
                "source_id": "awc_weather",
                "source_type": "LIVE_REAL",
                "badge": "LIVE REAL (AWC METAR)",
                "limitation": KNOWN_SOURCES["awc_weather"]["limitation"],
            },
            "maintenance": {
                "source_id": "faa_sdr",
                "source_type": "HISTORICAL_REAL",
                "badge": "HISTORICAL REAL (FAA SDRS)",
                "limitation": KNOWN_SOURCES["faa_sdr"]["limitation"],
            },
            "safety": {
                "source_id": "ntsb",
                "source_type": "HISTORICAL_REAL",
                "badge": "HISTORICAL REAL (NTSB)",
                "limitation": KNOWN_SOURCES["ntsb"]["limitation"],
            },
            "rul_health": {
                "source_id": "n_cmapss",
                "source_type": "BENCHMARK_SYNTHETIC",
                "badge": "BENCHMARK (N-CMAPSS)",
                "limitation": KNOWN_SOURCES["n_cmapss"]["limitation"],
            },
            "logistics_crew": {
                "source_id": "synthetic",
                "source_type": "SYNTHETIC",
                "badge": "SYNTHETIC FALLBACK",
                "limitation": KNOWN_SOURCES["synthetic"]["limitation"],
            },
        },
        "data_gap_notice": (
            "No publicly available live military HUMS, classified maintenance logs, "
            "or authoritative MC/PMC/NMC data exists. Fleet readiness classifications "
            "shown are derived from simulation / benchmark-trained ML. "
            "Production deployment requires direct IAF/MoD MRO system integration."
        ),
    }
