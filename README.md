# READYFLEET — Master Execution Index & Navigation

Welcome to **READYFLEET** (SIH26249 — Air Power: Predictive Maintenance & Fleet Availability). This document serves as the main index for project documentation, build execution tasks, and implementation steps.

---

## 📄 Key Project Files

1. **[TASKS.md](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/TASKS.md)**  
   Contains the complete 6-phase, 19-task checklist (**T1 through T19**) and complete project directory structure map.

2. **[STEP_BY_STEP.md](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/STEP_BY_STEP.md)**  
   Provides detailed command-line instructions, prerequisites, step-by-step build commands, and judge verification criteria.

3. **[`docs/`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs)**  
   Original project specification PDFs:
   - [`00-MASTER-PRD.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/00-MASTER-PRD.pdf) — Master Product Requirements Document & Literature Review
   - [`01-product-overview.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/01-product-overview.pdf) — High-level Vision & Core USP
   - [`02-features-spec.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/02-features-spec.pdf) — P0, P1, P2 Feature specifications
   - [`03-architecture-techstack.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/03-architecture-techstack.pdf) — System architecture & tech stack rationale
   - [`04-data-models-and-logic.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/04-data-models-and-logic.pdf) — SQLite schema, generator logic & math algorithms
   - [`05-build-plan-tasks.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/05-build-plan-tasks.pdf) — Original 36-hour build schedule
   - [`06-demo-and-judge-qa.pdf`](file:///c:/Users/Saptarshi/Desktop/MainFolder/Hackathon/readyfleet/v1/readyfleet/docs/06-demo-and-judge-qa.pdf) — Scripted 5-minute presentation script & Q&A defense

---

## 🎯 Project Summary

READYFLEET solves aircraft availability bottlenecks by fusing 5 data streams into an overarching decision layer:
- **HUMS / IoT signals** (Engine/component health degradation curves)
- **Technical Records** (Maintenance history & cycle metrics)
- **Spares Inventory** (Parts availability & lead times)
- **Crew Capacity** (Trade-wise technician schedules)
- **Sortie Demand** (Operational mission requirements & priority scoring)

---

## 🎯 System Positioning & Data Provenance Architecture

READYFLEET operates strictly as a:
> **Digital Twin Prototype / Simulated Fleet Twin with Live Public Operational & Weather Data**

### Data Stream Classification & Provenance Boundaries:
- **REAL (`LIVE_REAL` / `HISTORICAL_REAL`):**
  - Live Public Flight Operations (`adsb.lol` API — ADS-B positional tracking)
  - Live Aviation Weather (`AWC Weather API` — NOAA METAR environmental observations)
  - Historical Maintenance Records (`FAA SDRS` — Service Difficulty Reporting System)
  - Historical Safety & Incident Information (`NTSB` Aviation Accident Database)
- **BENCHMARK (`BENCHMARK_SYNTHETIC`):**
  - RUL Model Training (`NASA N-CMAPSS` Turbofan Engine Degradation Dataset)
- **SYNTHETIC / CONFIGURED (`CONFIGURED_SYNTHETIC`):**
  - Defence HUMS Telemetry Placeholder
  - Crew Capacity & Skill Mix
  - Spares & Supply Chain Inventory
  - Authoritative Fleet Readiness Classification (`MC` / `PMC` / `NMC`)

*Architectural Boundary Note:* Authorized defence HUMS and maintenance-management feeds can replace these synthetic fallback streams directly without requiring any changes to the overarching decision engine or web console interface.

---

## ⚡ Quick Start Command

To initialize project dependencies and execute the complete pipeline once implementation begins:

```bash
# Install dependencies
pip install fastapi uvicorn scikit-learn pandas numpy pytest pydantic pyyaml

# Run database setup & data generator
python gen/db.py && python gen/generate.py

# Train ML model & execute inference
python models/train.py && python models/infer.py

# Launch application server
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```
