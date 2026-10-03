import os
from data_sources.synthetic import SyntheticDataSource
from data_sources.faa_sdr import FAASDRDataSource
from data_sources.opensky import OpenSkyDataSource

READYFLEET_DATA_MODE = os.environ.get("READYFLEET_DATA_MODE", "HYBRID")

def get_active_data_sources():
    sources = {
        "synthetic": SyntheticDataSource(),
        "faa_sdr": FAASDRDataSource(),
        "opensky": OpenSkyDataSource()
    }
    
    provenance_summary = {
        "mode": READYFLEET_DATA_MODE,
        "ops": "LIVE REAL" if READYFLEET_DATA_MODE in ["LIVE_REAL", "HYBRID"] and sources["opensky"].health_check() else "SYNTHETIC",
        "maintenance": "HISTORICAL REAL" if READYFLEET_DATA_MODE in ["HISTORICAL_REAL", "HYBRID"] else "SYNTHETIC",
        "health": "SYNTHETIC",
        "logistics": "SYNTHETIC"
    }
    return sources, provenance_summary
