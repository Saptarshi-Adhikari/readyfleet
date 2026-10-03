# READYFLEET — Scripted 5-Minute Presentation Scenario

## ⏱️ Minute-by-Minute Walkthrough

### 0:00 - 1:00: Problem & Position
- **Headline Statement:** *"Low aircraft availability isn't an engine prediction problem—it's a fusion & decision problem."*
- Point out the persistent `DEMO MODE — ALL DATA IS SYNTHETIC` banner on top of the UI.
- Show the 40-tail Fleet Board rendering MC, PMC, and NMC status cards.

### 1:00 - 2:00: Predictive RUL & ML Evidence
- Drill down into an NMC tail card.
- Highlight the component RUL estimate with confidence intervals (e.g. $RUL = 18.4 \text{h} \pm 4.2 \text{h}$).
- Explain how `HistGradientBoostingRegressor` is trained on rolling-window telemetry features without data leakage across tails.

### 2:00 - 3:30: Decision Engine & What-If Simulation
- Switch to the 7-Day Forecast & What-If panel.
- Demonstrate applying the **Expedite Spares** lever:
  - Latency: $<200 \text{ ms}$.
  - Live MC Rate Delta: $+12.5\%$ improvement.
- Show unfilled sortie reductions for high-priority operational missions.

### 3:30 - 4:30: Cannibalization Advisor with Guardrails
- Open the Cannibalization Advisor tab.
- Demonstrate a refusal case: Attempt cannibalization from a higher-priority flyable donor airframe.
- Show the guardrail warning output.
- Perform a valid donor-recipient transfer and verify the tamper-evident hash-chained audit log entry.

### 4:30 - 5:00: Closing & Judge Summary
- Reiterate READYFLEET's role: sitting *above* diagnostic sensors to provide commanders with actionable readiness forecasts.
- Direct judges to the `evidence/metrics.json` file for reproducible benchmark evidence.
