# READYFLEET — Execution & Task Plan

**Project Name:** READYFLEET (SIH26249 — Air Power: Predictive Maintenance & Fleet Availability)
**Target Platform:** Laptop-Local Decision Intelligence Layer (FastAPI + Vanilla JS Canvas 2D + SQLite + Scikit-Learn)

---

## 📌 Implementation Strategy & Phase Breakdown

The build follow a 6-phase executable strategy (**T1 through T19**):

1. **Phase A: Data Foundation (T1–T4)** — Setup scaffold, database schema, synthetic generator with 5-stream fusion (HUMS, spares, crew, records, sorties) and seed determinism.
2. **Phase B: ML Evidence (T5–T7)** — Feature store, `HistGradientBoosting` RUL models per component class, metric evaluations (RMSE/MAE vs baseline), and batch inference service with confidence intervals.
3. **Phase C: Decision Logic (T8–T12)** — Fleet availability aggregator, What-If scenario engine, NMC-driver ranker, Cannibalization advisor with hard guardrails & debt ledger, and crew scheduler.
4. **Phase D: API Layer (T13)** — FastAPI endpoints delivering standardized Pydantic responses tagged with `"data_class": "synthetic"`.
5. **Phase E: Canvas 2D Dashboard (T14–T17)** — Fleet board, tail drill-down + explainability panel, 7-day forecast chart + what-if controls, cannibalization & audit logs.
6. **Phase F: Demo & Verification (T18–T19)** — Scripted 5-minute demo scenario rehearsed, pytest suite, and evidence bundling.

---

## 📋 Task Checklist (T1 — T19)

### Phase A — Data Foundation

- [x] **T1. Project Scaffold & Configuration**
  - Directories: `gen/`, `features/`, `models/`, `core/`, `api/`, `web/`, `config/`, `tests/`
  - Base files: `config/thresholds.yaml`, `requirements.txt`, `api/main.py`, `README.md`
- [x] **T2. SQLite Schema & DB Helper**
  - Files: `gen/schema.sql`, `gen/db.py`
  - 10 tables: `aircraft`, `component`, `sensor_reading`, `maintenance_record`, `spare`, `crew`, `sortie`, `prediction`, `scenario`, `audit_log`
- [x] **T3. Synthetic Generator v1 (Components & Sensors)**
  - Files: `gen/degradation.py`, `gen/generate.py`
  - Multi-sensor exponential degradation curves + 5% infant mortality + no-fault units.
- [x] **T4. Synthetic Generator v2 (Spares, Crew, Sorties, Records) & Determinism**
  - Files: `gen/seed.py`, extend `gen/generate.py`
  - Full 5-stream data fusion + SHA-256 seed determinism verification.

### Phase B — ML Evidence

- [x] **T5. Feature Store (Single Code Path)**
  - Files: `features/build.py`
  - Windowed stats (rolling mean/std/min/max/slope over 10/30 cycles) + operational setting one-hots.
- [x] **T6. RUL Model Training & Evaluation**
  - Files: `models/train.py`, `models/eval.py`, `models/registry.py`
  - Capped RUL (125h) target, split by tail ID, `HistGradientBoostingRegressor` evaluation vs naive mean baseline.
- [x] **T7. Prediction Intervals & Inference Service**
  - Files: `models/infer.py`
  - Quantile prediction intervals (`ci_low`, `ci_high`) written to DB per run.

### Phase C — Decision Logic

- [x] **T8. Fleet Availability Aggregator**
  - Files: `core/state.py`, `core/aggregator.py`
  - Rules R1/R2/R3 translating state to MC/PMC/NMC per tail and 7-day MC-rate forecast.
- [x] **T9. What-If Scenario Engine**
  - Files: `core/whatif.py`
  - Pure state patching (expedite spares, reassign crew, cannibalize) with sub-200ms latency.
- [x] **T10. NMC-Driver Ranker**
  - Files: `core/drivers.py`
  - Ranks top 5 fleet grounding constraints by impact score.
- [x] **T11. Cannibalization Advisor + Guardrails + Debt Ledger**
  - Files: `core/cannibal.py`
  - Advisor proposing donor airframes subject to priority, NMC status, and CANN-rate limits.
- [x] **T12. Crew 1-Day Greedy Scheduler + Hash-Chained Audit Log**
  - Files: `core/scheduler.py`, `core/audit.py`
  - Priority-weighted crew allocation and tamper-evident hash-chained audit logging.

### Phase D — API Layer

- [x] **T13. FastAPI Endpoints & Contracts**
  - Files: `api/schemas.py`, `api/routes/*.py`
  - REST endpoints for fleet status, tail details, forecasts, what-if simulations, cannibalization advice, and audit logs.

### Phase E — Canvas 2D Dashboard

- [x] **T14. Fleet Board (Canvas 2D)**
  - Files: `web/index.html`, `web/app.js`, `web/fleet.js`, `web/style.css`
  - Interactive grid displaying tail status cards, MC/PMC/NMC counts, and persistent `SYNTHETIC DATA` banner.
- [x] **T15. Tail Drill-Down & Explainability Panel**
  - Files: `web/tail.js`
  - Per-component RUL breakdown, prediction intervals, and top feature contribution text.
- [x] **T16. Forecast Chart & What-If Controls**
  - Files: `web/forecast.js`, `web/whatif.js`
  - Canvas line chart of 7-day MC forecast and live scenario delta panel.
- [x] **T17. Cannibalization Advisor UI & Audit Log Tab**
  - Files: `web/cannibal.js`, `web/audit.js`
  - Donor selection interface with guardrail status indicators and reverse-chronological audit trail.

### Phase F — Demo & Evidence

- [x] **T18. Scripted Demo Scenario & Honesty Pass**
  - Files: `demo/scenario.md`
  - Pre-packaged 7-day demo script with verified MC rate deltas and honesty banner sweep.
- [x] **T19. Evidence Bundle & Test Suite**
  - Files: `tests/*`, `evidence/`
  - Complete automated test suite (`pytest`) capturing evaluation metrics, determinism hash, and performance latency.

---

## 🛠 File Hierarchy Map

```
readyfleet/
├── config/
│   └── thresholds.yaml         # Configuration & thresholds for rules engine
├── gen/
│   ├── schema.sql              # 10 SQLite database table definitions
│   ├── db.py                   # SQLite setup & helper methods
│   ├── degradation.py          # Multi-sensor physics-degradation logic
│   ├── seed.py                 # Seed management & SHA-256 verification
│   └── generate.py             # Full 5-stream dataset synthesis script
├── features/
│   └── build.py                # Feature extraction pipeline (train & infer)
├── models/
│   ├── train.py                # Model training logic (HistGradientBoosting)
│   ├── eval.py                 # Judge-facing metrics & evaluation printouts
│   ├── registry.py             # Model artifact persistence & loader
│   └── infer.py                # Batch prediction & confidence interval service
├── core/
│   ├── state.py                # State snapshot extraction & cloning
│   ├── aggregator.py           # Fleet availability & MC-rate rules engine
│   ├── whatif.py               # Scenario simulation & lever diff engine
│   ├── drivers.py              # Binding constraint & NMC driver ranker
│   ├── cannibal.py             # Cannibalization advisor & guardrails logic
│   ├── scheduler.py            # Crew capacity scheduler
│   └── audit.py                # Tamper-evident hash-chained audit logger
├── api/
│   ├── main.py                 # FastAPI application entrypoint
│   ├── schemas.py              # Pydantic data validation schemas
│   └── routes/                 # API endpoint handlers
├── web/
│   ├── index.html              # Single Page Application HTML shell
│   ├── style.css               # Vanilla CSS design tokens & layout rules
│   ├── app.js                  # Main JS router & view switcher
│   ├── fleet.js                # Canvas 2D Fleet Board renderer
│   ├── tail.js                 # Tail drill-down & ML explainability UI
│   ├── forecast.js             # Canvas 2D 7-Day MC forecast line chart
│   ├── whatif.js               # What-if lever controls & delta panel
│   ├── cannibal.js             # Cannibalization advisor interface
│   └── audit.js                # Audit log viewer
├── demo/
│   └── scenario.md             # 5-minute scripted presentation walkthrough
├── evidence/
│   └── metrics.json            # Benchmark printouts & evidence output
├── tests/                      # Pytest unit & contract test suite
├── requirements.txt            # Python dependencies
└── TASKS.md                    # Project build tracker (this file)
```
