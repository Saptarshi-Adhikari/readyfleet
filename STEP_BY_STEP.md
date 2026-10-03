# READYFLEET — Execution Blueprint & Step-by-Step Guide

This guide details the sequential steps required to build, test, and execute **READYFLEET** (SIH26249 — Air Power: Predictive Maintenance & Fleet Availability).

---

## 🛠 Prerequisites & Dependencies

Ensure you have Python 3.10+ installed. Install project dependencies:

```bash
pip install fastapi uvicorn scikit-learn pandas numpy pytest pydantic pyyaml
```

---

## 🚀 Step-by-Step Execution Sequence

### Step 1: Scaffold & Database Initialization (Tasks T1–T2)
Initialize directory structures and populate SQLite database schemas.

```bash
# 1. Verify directory creation
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['gen', 'features', 'models', 'core', 'api', 'web', 'config', 'tests', 'demo', 'evidence']]"

# 2. Run SQLite schema initialization script
python gen/db.py
```
*Expected Output:* Creates `readyfleet.db` containing all 10 core tables (`aircraft`, `component`, `sensor_reading`, `maintenance_record`, `spare`, `crew`, `sortie`, `prediction`, `scenario`, `audit_log`).

---

### Step 2: Synthetic Data Generation & Determinism (Tasks T3–T4)
Generate synthetic 5-stream dataset with multi-sensor exponential degradation curves and recorded random seeds.

```bash
# Generate synthetic fleet data
python gen/generate.py
```
*Expected Output:* populates `readyfleet.db` with ~40 tails, sensor logs, spare inventory, crew capacity, and 7-day sortie demand schedules. Outputs SHA-256 hash verifying seed determinism.

---

### Step 3: Feature Store & ML Model Training (Tasks T5–T7)
Extract rolling-window sensor features, train `HistGradientBoostingRegressor` per component class, evaluate baseline comparisons, and generate initial prediction confidence intervals.

```bash
# 1. Build features and train RUL model
python models/train.py

# 2. Evaluate model performance (Generate judge evidence printout)
python models/eval.py

# 3. Execute batch inference service
python models/infer.py
```
*Expected Output:* `models/eval.py` prints RMSE/MAE comparisons vs naive mean baseline. Writes metrics and model artifacts to `models/model.pkl` and `evidence/metrics.json`.

---

### Step 4: Rule Aggregator, What-If & Decision Engines (Tasks T8–T12)
Run core decision algorithms, including MC-rate availability calculations, What-If state patching, NMC driver ranking, and cannibalization advice.

```bash
# Execute unit test suite for core rules engine
pytest tests/test_core.py
```
*Expected Output:* Green test suite confirming pure state transformations, sub-200ms What-If recomputations, cannibalization guardrail enforcement, and hash-chained audit logging.

---

### Step 5: Launch Local FastAPI & Canvas 2D Web Application (Tasks T13–T17)
Launch the FastAPI backend serving both REST endpoints and static Canvas 2D frontend.

```bash
# Start backend server
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```
*Access Application:* Open `http://127.0.0.1:8000/` in browser to view the Canvas 2D Fleet Board, Tail Drill-Downs, 7-Day Forecast Chart, What-If Controls, and Audit Logs.  
*API Documentation:* Open `http://127.0.0.1:8000/docs` for interactive OpenAPI specs.

---

### Step 6: Final Verification & Evidence Bundling (Tasks T18–T19)
Run full test suite and build evidence outputs for judging presentation.

```bash
# Run complete test suite and generate evidence bundle
pytest
python demo/prepare_evidence.py
```
*Expected Output:* `evidence/` folder populated with verified eval printouts, SHA-256 determinism proofs, latency records, and contract test logs.

---

## 📑 Verification Checklist for Judges

- [ ] **"SYNTHETIC DATA" Banner:** Present on every screen and API response (`"data_class": "synthetic"`).
- [ ] **Decision Layer Focus:** System operates *above* diagnostic sensors/HUMS, fusing spares, crew, records, and sortie priority.
- [ ] **RUL Model Evidence:** Printed RMSE/MAE comparisons proving prediction validity over baseline models.
- [ ] **Sub-200ms What-If Response:** Real-time scenario diff calculation on fleet MC rates.
