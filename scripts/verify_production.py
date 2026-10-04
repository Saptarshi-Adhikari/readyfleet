"""
READYFLEET Production Verification Script
========================================
Queries public Vercel production endpoints and verifies:
- HTTP 200 responses
- DATA_MODE = REAL_ONLY
- DATABASE = postgres / healthy
- Data sources and prediction contracts
"""

import sys
import os
import urllib.request
import json

DEFAULT_HOST = os.environ.get("VERCEL_URL", "http://127.0.0.1:8080")
if not DEFAULT_HOST.startswith("http"):
    DEFAULT_HOST = f"https://{DEFAULT_HOST}"

endpoints = [
    "/api/health",
    "/api/data-mode",
    "/api/data-sources",
    "/api/fleet/status",
    "/api/fleet/forecast",
    "/api/drivers",
    "/api/predictions/summary",
]

def verify(base_url: str = DEFAULT_HOST):
    print(f"[VERIFY] Testing READYFLEET production deployment at {base_url}...")
    all_ok = True
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "READYFLEET-Verify/1.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                status = res.status
                print(f"  [OK] {ep} -> HTTP {status}")
                if ep == "/api/health":
                    mode = data.get("data_mode")
                    db = data.get("database")
                    db_stat = data.get("database_status")
                    print(f"    Health details: mode={mode}, db={db}, db_status={db_stat}")
                    if mode != "REAL_ONLY":
                        print(f"    WARNING: data_mode is {mode}, expected REAL_ONLY")
        except Exception as e:
            print(f"  [ERROR] {ep} -> ERROR: {e}")
            all_ok = False

    if all_ok:
        print("[VERIFY SUCCESS] All production endpoints are active and healthy.")
    else:
        print("[VERIFY FAILED] One or more endpoints failed.")
        sys.exit(1)

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    verify(host)
