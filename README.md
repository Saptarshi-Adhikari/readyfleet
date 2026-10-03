# READYFLEET — Master Execution Index & SIH 2026 Judge Verification Guide

Welcome to **READYFLEET** (SIH 2026 Problem Statement **SIH26249 — Air Power: Predictive Maintenance & Fleet Availability**).

---

## 🎯 System Positioning

READYFLEET operates strictly as a:
> **SIH DEMO-READY / PROTOTYPE-READY: Digital Twin Prototype / Simulated Fleet Twin with Live Public Operational & Weather Data**

It demonstrates an AI-enabled fleet digital-twin platform with live public operational/weather synchronization, benchmark-based health intelligence, and strict provenance and decision-boundary controls for future authorized defence integration.

---

## 📊 Data-Source Classification & Reality Matrix

| Stream | Current Source | Reality Classification | Authorization / Status |
| :--- | :--- | :--- | :--- |
| **Operations** | `adsb.lol` API | `LIVE REAL PUBLIC` | Verified / Active Open Data |
| **Weather** | `AWC Weather API` | `LIVE REAL` | Verified / Active NOAA METAR |
| **Maintenance** | `FAA SDRS` | `HISTORICAL REAL` | Verified / Historical Batch |
| **Health / RUL ML** | `NASA N-CMAPSS` | `BENCHMARK` | Benchmark Turbofan Dataset |
| **Crew Capacity** | Current Prototype | `SYNTHETIC` | Prototype Configured Stream |
| **Spares Inventory** | Current Prototype | `SYNTHETIC` | Prototype Configured Stream |
| **Defence MC/PMC/NMC** | Current Prototype | `CONFIGURED SYNTHETIC` | Decision Boundary Isolated |
| **Defence HUMS Telemetry** | None Publicly Integrated | `NOT AVAILABLE` | Requires Authorized Defence Feed |

---

## 🏗️ System Architecture Flow

```
External APIs (adsb.lol / AWC Weather)
  ↓
Source Adapters & Rate Limiters (data_sources/adsb_lol.py, awc_weather.py)
  ↓
Validation & Normalization (data_sources/base.py)
  ↓
Provenance Engine (source_id, ingestion_ts, synthetic=0)
  ↓
SQLite Persistence & Trusted Identity Check (core/identity.py)
  ↓
Digital Twin Stream Registry (twins maintain separate stream provenance)
  ↓
Decision Engine (core/aggregator.py — MC/PMC/NMC isolated from public ADS-B/weather)
  ↓
FastAPI SSE Event Bus (api/main.py — broadcast_sse_event)
  ↓
React Console (frontend/src/hooks/useLiveEvents.ts — SSE subscriber with deduplication)
```

---

## ⚡ Clean Reproduction & Startup Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 1. Backend Startup
```bash
# Navigate to project root
cd readyfleet

# Install Python dependencies
pip install fastapi uvicorn scikit-learn pandas numpy pytest pydantic pyyaml

# Initialize database & benchmark models
python gen/db.py && python gen/generate.py && python models/train.py && python models/infer.py

# Launch FastAPI backend server on port 8080 (starts automatic background ingestion workers)
python -m uvicorn api.main:app --host 127.0.0.1 --port 8080
```

### 2. Frontend Startup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies & start Vite dev server
npm install
npm run dev -- --port 5173
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Canonical Verification Command

To run the complete automated test suite (35 unit & integration tests covering identity safety, live ingestion fabric, OpenSky neutral semantics, decision boundaries, API endpoints, core aggregator, and RUL ML pipeline):

```bash
python -m unittest discover -s tests -p "test_*.py"
```

To build production frontend assets:
```bash
cd frontend && npm run build
```

---

## 🔌 Production Extension Rationale

Authorized defence HUMS recorders, technician schedule databases, and spare parts ERP feeds can replace the synthetic placeholder streams directly via the `BaseDataSource` abstraction without requiring any changes to the overarching decision engine or web console interface.
