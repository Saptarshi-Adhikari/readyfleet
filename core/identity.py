from typing import Dict, Any, Optional
import pandas as pd

def resolve_trusted_twin_identity(
    observation: Dict[str, Any], 
    trusted_identity_map: Dict[str, str] = None
) -> Optional[str]:
    """
    Identity-Safety Evaluator for READYFLEET Digital Twin Platform.
    
    Rules:
    1. Returns twin tail_no ONLY if an exact, explicit trusted mapping exists 
       (e.g., exact ICAO24 or explicit registration alias in trusted registry).
    2. REJECTS fuzzy name matching, geographic proximity, type similarity, callsign guessing.
    3. If no trusted match exists, returns None (observation is persisted in stream, 
       emitting operational_update, but DOES NOT touch defence twin state).
    """
    if trusted_identity_map is None:
        # Default authoritative identity map for READYFLEET prototype
        trusted_identity_map = {
            "A1B2C3": "RF-001",
            "VT-TEST": "RF-002",
            "A89F12": "RF-003",
            "VT-RF001": "RF-001",
            "VT-RF002": "RF-002",
            "VT-RF003": "RF-003",
            "VT-RF004": "RF-004",
            "VT-RF005": "RF-005"
        }

    raw_icao = str(observation.get("hex", "") or observation.get("icao24", "")).upper().strip()
    raw_reg = str(observation.get("registration", "") or observation.get("r", "")).upper().strip()
    raw_tail = str(observation.get("tail_no", "")).upper().strip()

    # Exact lookup 1: ICAO24
    if raw_icao and raw_icao in trusted_identity_map:
        return trusted_identity_map[raw_icao]

    # Exact lookup 2: Registration
    if raw_reg and raw_reg in trusted_identity_map:
        return trusted_identity_map[raw_reg]

    # Exact lookup 3: Direct Tail Match if in trusted map
    if raw_tail and raw_tail in trusted_identity_map.values():
        return raw_tail

    # Reject fuzzy / proximity / type / callsign matching
    return None
