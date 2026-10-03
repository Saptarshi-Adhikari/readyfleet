import hashlib
import json
import os
from typing import Dict, Any

METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence", "metrics.json")

def compute_file_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def update_metrics(data: Dict[str, Any], filepath: str = METRICS_PATH) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    existing = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    existing.update(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
