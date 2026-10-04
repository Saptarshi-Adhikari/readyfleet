"""
READYFLEET Decision Intelligence API
=====================================
FastAPI backend for the READYFLEET fleet readiness platform.

Data provenance is tracked and exposed on every endpoint.
DATA_MODE is enforced globally: synthetic data cannot silently populate
real-data API responses in REAL_ONLY mode.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
import os
import json
import datetime
import uuid
import asyncio

from api.schemas import (
    FleetStatusResponse, ForecastResponse,
    WhatIfRequest, WhatIfResponse,
    CannibalRequest, CannibalResponse
)
from core.state import load_fleet_state
from core.aggregator import evaluate_fleet_availability
from core.whatif import apply_whatif_lever
from core.drivers import rank_nmc_drivers
from core.cannibal import evaluate_cannibalization_proposal, record_cannibalization_debt
from core.audit import verify_audit_log
from core.provenance import build_fleet_provenance_summary, KNOWN_SOURCES

from data_sources.scheduler import scheduler_instance
from data_sources.manager import get_active_data_sources, get_data_mode
from ml.sdr_risk_model import compute_fleet_risk

# ─────────────────────────────────────────────────────────────────────────────
# App Metadata
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="READYFLEET Decision Intelligence API",
    description=(
        "Fleet-Availability Decision Layer for Air Power (SIH26249). "
        "All endpoints carry full data provenance. "
        "PRODUCTION DATA_MODE: REAL_ONLY"
    ),
    version="2.0.0",
)

# ─────────────────────────────────────────────────────────────────────────────
# SSE Subscriber Registry
# ─────────────────────────────────────────────────────────────────────────────

sse_subscribers: List[asyncio.Queue] = []

async def broadcast_sse_event(event_type: str, source_id: str, data: Dict[str, Any]):
    """Broadcast a Server-Sent Event to all connected subscribers."""
    evt_payload = {
        "id": f"evt-{uuid.uuid4().hex[:12]}",
        "event": event_type,
        "source_id": source_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": data,
    }
    msg = f"data: {json.dumps(evt_payload)}\n\n"
    dead = []
    for q in sse_subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        if q in sse_subscribers:
            sse_subscribers.remove(q)


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Background Ingestion
# ─────────────────────────────────────────────────────────────────────────────

background_task_handle: Optional[asyncio.Task] = None

@app.on_event("startup")
async def start_background_ingestion():
    """Launch the periodic data ingestion background worker cleanly."""
    global background_task_handle
    if background_task_handle is not None and not background_task_handle.done():
        return

    async def periodic_ingestion():
        last_status: Dict[str, Any] = {}
        while True:
            try:
                results = scheduler_instance.sync_all()
                curr_status = {
                    s_id: (m.get("status"), m.get("freshness"))
                    for s_id, m in scheduler_instance.freshness.items()
                }
                # Filter SSE event storms: broadcast only on status/freshness state change
                if curr_status != last_status:
                    last_status = curr_status.copy()
                    await broadcast_sse_event("source_status_update", "scheduler", results)
                    await broadcast_sse_event(
                        "operational_update",
                        "adsb_lol",
                        {"freshness": scheduler_instance.freshness.get("adsb_lol", {})}
                    )
                    await broadcast_sse_event(
                        "weather_update",
                        "awc_weather",
                        {"freshness": scheduler_instance.freshness.get("awc_weather", {})}
                    )
            except Exception as e:
                print(f"[BACKGROUND INGESTION WORKER ERROR]: {e}")
            await asyncio.sleep(20)

    background_task_handle = asyncio.create_task(periodic_ingestion())


@app.on_event("shutdown")
async def stop_background_ingestion():
    """Cleanly stop background scheduler on server shutdown / reload."""
    global background_task_handle
    if background_task_handle is not None:
        background_task_handle.cancel()
        background_task_handle = None


# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure / Metadata Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    mode = get_data_mode()
    sources_summary = {
        s_id: scheduler_instance.freshness.get(s_id, {}).get("status", "UNKNOWN")
        for s_id in ["adsb_lol", "awc_weather", "faa_sdrs"]
    }
    return {
        "status": "ok",
        "service": "READYFLEET API",
        "version": "2.0.0",
        "data_mode": mode,
        "sources": sources_summary,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@app.get("/api/data-mode")
def get_data_mode_endpoint():
    """Return current data mode and full provenance summary."""
    mode = get_data_mode()
    prov = build_fleet_provenance_summary(mode)
    _, source_prov = get_active_data_sources()
    return {
        "data_mode": mode,
        "synthetic_blocked": mode == "REAL_ONLY",
        "provenance": prov,
        "source_connectivity": source_prov,
    }


@app.get("/api/data-sources")
def get_data_sources_registry():
    """Return authoritative registry of all configured data sources with metrics."""
    mode = get_data_mode()
    syn_blocked = mode == "REAL_ONLY"

    adsb_m = scheduler_instance.freshness.get("adsb_lol", {})
    awc_m = scheduler_instance.freshness.get("awc_weather", {})
    faa_m = scheduler_instance.freshness.get("faa_sdrs", {})
    nc_m = scheduler_instance.freshness.get("n_cmapss", {})

    return {
        "data_mode": mode,
        "sources": [
            {
                "source_id": "adsb_lol",
                "name": "adsb.lol Open-Data ADS-B",
                "domain": "Operations",
                "type": "LIVE_REAL",
                "status": adsb_m.get("status", "UNKNOWN"),
                "freshness": adsb_m.get("freshness", "STALE"),
                "last_success": adsb_m.get("last_success", "NEVER"),
                "last_failure": adsb_m.get("last_failure"),
                "next_retry_at": adsb_m.get("next_retry_at", 0.0),
                "consecutive_failures": adsb_m.get("consecutive_failures", 0),
                "request_count": adsb_m.get("request_count", 0),
                "success_count": adsb_m.get("success_count", 0),
                "failure_count": adsb_m.get("failure_count", 0),
                "rate_limit_count": adsb_m.get("rate_limit_count", 0),
                "timeout_count": adsb_m.get("timeout_count", 0),
                "average_latency_ms": round(adsb_m.get("average_latency_ms", 0.0), 1),
                "enabled": True,
                "limitation": KNOWN_SOURCES["adsb_lol"]["limitation"],
            },
            {
                "source_id": "awc_weather",
                "name": "NOAA AWC METAR",
                "domain": "Weather",
                "type": "LIVE_REAL",
                "status": awc_m.get("status", "UNKNOWN"),
                "freshness": awc_m.get("freshness", "STALE"),
                "last_success": awc_m.get("last_success", "NEVER"),
                "last_failure": awc_m.get("last_failure"),
                "next_retry_at": awc_m.get("next_retry_at", 0.0),
                "consecutive_failures": awc_m.get("consecutive_failures", 0),
                "request_count": awc_m.get("request_count", 0),
                "success_count": awc_m.get("success_count", 0),
                "failure_count": awc_m.get("failure_count", 0),
                "rate_limit_count": awc_m.get("rate_limit_count", 0),
                "timeout_count": awc_m.get("timeout_count", 0),
                "average_latency_ms": round(awc_m.get("average_latency_ms", 0.0), 1),
                "enabled": True,
                "limitation": KNOWN_SOURCES["awc_weather"]["limitation"],
            },
            {
                "source_id": "faa_sdrs",
                "name": "FAA Service Difficulty Reports",
                "domain": "Maintenance",
                "type": "HISTORICAL_REAL",
                "status": faa_m.get("status", "READY"),
                "freshness": faa_m.get("freshness", "CURRENT"),
                "last_update": faa_m.get("last_sync", "BATCH"),
                "enabled": True,
                "limitation": KNOWN_SOURCES["faa_sdr"]["limitation"],
            },
            {
                "source_id": "n_cmapss",
                "name": "NASA N-CMAPSS Turbofan Benchmark",
                "domain": "Health / RUL",
                "type": "BENCHMARK_SYNTHETIC",
                "status": nc_m.get("status", "MODEL_ONLY"),
                "freshness": nc_m.get("freshness", "CURRENT"),
                "last_update": "STATIC_DATASET",
                "enabled": True,
                "limitation": KNOWN_SOURCES["n_cmapss"]["limitation"],
            },
            {
                "source_id": "synthetic",
                "name": "READYFLEET Synthetic Generator",
                "domain": "Logistics / Simulation",
                "type": "SYNTHETIC",
                "status": "BLOCKED (REAL_ONLY)" if syn_blocked else "ACTIVE",
                "freshness": "BLOCKED" if syn_blocked else "SIMULATION",
                "enabled": not syn_blocked,
                "limitation": KNOWN_SOURCES["synthetic"]["limitation"],
            },
            {
                "source_id": "defence_hums",
                "name": "Defence HUMS Telemetry",
                "domain": "Aircraft Health",
                "type": "NOT_AVAILABLE",
                "status": "NOT CONNECTED",
                "freshness": "N/A",
                "enabled": False,
                "limitation": "No public live military HUMS data exists.",
            },
            {
                "source_id": "military_mro",
                "name": "Defence MRO Logistics & Spares",
                "domain": "Logistics / Spares / Crew",
                "type": "NOT_AVAILABLE",
                "status": "NOT CONNECTED",
                "freshness": "N/A",
                "enabled": False,
                "limitation": "Classified military logistics database.",
            },
        ],
    }


@app.post("/api/data-sources/sync-all")
async def sync_all_data_sources():
    """Manually trigger a full sync of all configured data sources."""
    results = scheduler_instance.sync_all()
    await broadcast_sse_event("source_status_update", "manual_trigger", results)
    return {"status": "complete", "results": results}


# ─────────────────────────────────────────────────────────────────────────────
# SSE Event Stream
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/stream/events")
async def sse_event_stream():
    """Server-Sent Events stream for live data updates."""
    async def event_generator():
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        sse_subscribers.append(q)
        try:
            init_msg = json.dumps({
                "event": "connected",
                "data_mode": get_data_mode(),
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            yield f"data: {init_msg}\n\n"
            while True:
                msg = await q.get()
                yield msg
        except asyncio.CancelledError:
            pass
        finally:
            if q in sse_subscribers:
                sse_subscribers.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─────────────────────────────────────────────────────────────────────────────
# Fleet Status Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/fleet/status", response_model=FleetStatusResponse)
def get_fleet_status():
    """Fleet readiness summary: MC/PMC/NMC counts and rates."""
    mode = get_data_mode()
    state = load_fleet_state()
    res = evaluate_fleet_availability(state)
    summary = res["summary"]
    return FleetStatusResponse(
        data_class="REAL_ONLY" if mode == "REAL_ONLY" else "HYBRID",
        total_tails=summary["total_tails"],
        mc_count=summary["mc_count"],
        pmc_count=summary["pmc_count"],
        nmc_count=summary["nmc_count"],
        current_mc_rate=summary["current_mc_rate"],
        tail_states=res["tail_states"],
    )


@app.get("/api/fleet/forecast", response_model=ForecastResponse)
def get_fleet_forecast():
    """7-day MC rate forecast based on current degradation trajectories."""
    mode = get_data_mode()
    state = load_fleet_state()
    res = evaluate_fleet_availability(state)
    return ForecastResponse(
        data_class="PREDICTED" if mode == "REAL_ONLY" else "HYBRID",
        mc_forecast=res["mc_forecast"],
        unfilled_sorties=res["unfilled_sorties"],
    )


@app.get("/api/drivers")
def get_nmc_drivers():
    """Top grounding constraints ranked by operational impact."""
    state = load_fleet_state()
    drivers = rank_nmc_drivers(state)
    mode = get_data_mode()
    return {
        "data_class": "PREDICTED" if mode == "REAL_ONLY" else "SIMULATION",
        "provenance_note": "Grounding drivers are derived from RUL model predictions "
                          "(N-CMAPSS benchmark-trained). NOT from real HUMS telemetry.",
        "drivers": drivers,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Predictions & Risk Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/predictions")
def get_fleet_predictions():
    """
    Fleet-wide component predictions with full provenance.

    Returns RUL predictions AND maintenance risk scores.
    Each value is labelled with its data_class and provenance.
    """
    state = load_fleet_state()
    components = state["components"]
    predictions = state["predictions"]

    try:
        from gen.db import get_connection, DB_PATH
        import pandas as pd
        conn = get_connection(DB_PATH)
        maint_records = pd.read_sql_query(
            "SELECT * FROM maintenance_record WHERE component_id IS NOT NULL", conn
        )
        conn.close()
    except Exception:
        maint_records = None

    # Compute risk scores via real SDR-trained model
    risk_results = compute_fleet_risk(components, predictions, maint_records)

    # Augment with RUL data
    pred_map = {}
    for _, row in predictions.iterrows():
        pred_map[int(row["component_id"])] = {
            "predicted_rul_h": float(row.get("predicted_rul_h", 999.0)),
            "ci_low": float(row.get("ci_low", 0.0)),
            "ci_high": float(row.get("ci_high", 999.0)),
        }

    output = []
    for risk in risk_results:
        cid = risk["component_id"]
        rul_data = pred_map.get(cid, {"predicted_rul_h": None, "ci_low": None, "ci_high": None})
        output.append({
            "component_id": cid,
            "tail_no": risk["tail_no"],
            "serial_no": risk["serial_no"],
            "comp_class": risk["comp_class"],
            # RUL from N-CMAPSS-trained model
            "rul": {
                "predicted_rul_h": rul_data["predicted_rul_h"],
                "ci_low": rul_data["ci_low"],
                "ci_high": rul_data["ci_high"],
                "data_class": "PREDICTED",
                "model_source": "N-CMAPSS (Benchmark Synthetic)",
                "provenance_note": "RUL predicted by HistGBR model trained on NASA N-CMAPSS. "
                                  "NOT equivalent to real HUMS sensor data.",
            },
            # Risk from FAA SDR priors
            "maintenance_risk": {
                "risk_score": risk["risk_score"],
                "risk_tier": risk["risk_tier"],
                "contributing_factors": risk["contributing_factors"],
                "data_class": "PREDICTED",
                "model_source": "FAA SDR Historical Priors + N-CMAPSS",
                "provenance": risk["provenance"],
            },
            "installed_hours": risk["installed_hours"],
        })

    return {
        "data_class": "PREDICTED",
        "provenance_note": (
            "All predictions are model outputs, NOT observed sensor readings. "
            "RUL: N-CMAPSS benchmark-trained model. "
            "Risk: FAA SDR historical failure rate priors."
        ),
        "predictions": output,
    }


@app.get("/api/predictions/summary")
def get_predictions_summary():
    """High-level fleet risk summary for the dashboard."""
    state = load_fleet_state()
    components = state["components"]
    predictions = state["predictions"]

    risk_results = compute_fleet_risk(components, predictions)

    critical = [r for r in risk_results if r["risk_tier"] == "CRITICAL"]
    high = [r for r in risk_results if r["risk_tier"] == "HIGH"]
    medium = [r for r in risk_results if r["risk_tier"] == "MEDIUM"]
    low = [r for r in risk_results if r["risk_tier"] == "LOW"]

    return {
        "data_class": "PREDICTED",
        "summary": {
            "total_components": len(risk_results),
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
            "avg_risk_score": float(
                sum(r["risk_score"] for r in risk_results) / max(len(risk_results), 1)
            ),
        },
        "top_critical": [
            {
                "tail_no": r["tail_no"],
                "comp_class": r["comp_class"],
                "risk_score": r["risk_score"],
                "risk_tier": r["risk_tier"],
                "contributing_factors": r["contributing_factors"],
            }
            for r in sorted(critical, key=lambda x: -x["risk_score"])[:5]
        ],
        "provenance_note": "Risk scores computed from FAA SDR failure rate priors. "
                          "PREDICTED — not observed.",
    }


@app.get("/api/provenance/sources")
def get_provenance_sources():
    """Complete source registry with provenance metadata for all configured sources."""
    return {
        "data_mode": get_data_mode(),
        "sources": KNOWN_SOURCES,
        "data_gap_notice": (
            "No publicly available live military HUMS, classified maintenance logs, "
            "or authoritative MC/PMC/NMC data exists. Fleet readiness classifications "
            "shown are simulation-derived. Production requires direct IAF/MoD integration."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Aircraft Detail
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/aircraft/{tail_no}")
def get_aircraft_detail(tail_no: str):
    """Full aircraft detail with RUL, risk scores, and provenance for each component."""
    state = load_fleet_state()
    ac_df = state["aircraft"]
    ac_row = ac_df[ac_df["tail_no"] == tail_no]
    if ac_row.empty:
        raise HTTPException(status_code=404, detail="Aircraft tail number not found")

    ac_info = ac_row.iloc[0].to_dict()
    comps_df = state["components"]
    ac_comps = comps_df[comps_df["tail_no"] == tail_no]
    preds_df = state["predictions"]

    # Risk scoring
    risk_results = compute_fleet_risk(ac_comps, preds_df)
    risk_map = {r["component_id"]: r for r in risk_results}

    components_detail = []
    blocking_constraint = None

    for _, comp in ac_comps.iterrows():
        comp_id = int(comp["id"])
        pred_row = preds_df[preds_df["component_id"] == comp_id]
        rul = float(pred_row["predicted_rul_h"].values[0]) if not pred_row.empty else None
        ci_low = float(pred_row["ci_low"].values[0]) if not pred_row.empty else None
        ci_high = float(pred_row["ci_high"].values[0]) if not pred_row.empty else None

        risk = risk_map.get(comp_id, {})

        comp_data = {
            "id": comp_id,
            "comp_class": comp["comp_class"],
            "serial_no": comp["serial_no"],
            "installed_cycles": int(comp["installed_cycles"]),
            "installed_hours": float(comp["installed_hours"]),
            # RUL
            "predicted_rul_h": rul,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "rul_data_class": "PREDICTED" if rul is not None else "NOT AVAILABLE",
            "rul_provenance": "N-CMAPSS benchmark-trained HistGBR model",
            # Status
            "threshold_h": 24.0,
            "status": (
                "CRITICAL" if rul is not None and rul < 24.0
                else "WARNING" if rul is not None and rul < 50.0
                else "HEALTHY" if rul is not None
                else "UNKNOWN"
            ),
            # Risk
            "risk_score": risk.get("risk_score"),
            "risk_tier": risk.get("risk_tier"),
            "contributing_factors": risk.get("contributing_factors", []),
            "risk_data_class": "PREDICTED",
            "risk_provenance": "FAA SDR failure rate priors",
        }
        components_detail.append(comp_data)

        if rul is not None and rul < 24.0 and blocking_constraint is None:
            blocking_constraint = {
                "reason": f"{comp['comp_class'].upper()} RUL ({rul:.1f}h) BELOW 24h THRESHOLD",
                "required_action": f"Perform {comp['comp_class']} overhaul / replacement",
                "required_spare": f"PART-{comp['comp_class'][:3].upper()}-01",
                "required_trade": comp["comp_class"],
                "est_duration": "4.5 Hours",
                "data_class": "DERIVED",
            }

    eval_res = evaluate_fleet_availability(state)
    reasons = eval_res["tail_grounding_reasons"].get(tail_no, [])
    mode = get_data_mode()

    return {
        "data_class": "REAL_ONLY" if mode == "REAL_ONLY" else "HYBRID",
        "provenance_note": (
            "Aircraft identity: REAL ADS-B / FAA registry. "
            "RUL predictions: PREDICTED (N-CMAPSS-trained model). "
            "Risk scores: PREDICTED (FAA SDR priors)."
        ),
        "aircraft": ac_info,
        "components": components_detail,
        "grounding_reasons": reasons,
        "blocking_constraint": blocking_constraint or {
            "reason": "NONE — AIRCRAFT IS FLYABLE / MC",
            "required_action": "Standard Pre-Flight Inspection",
            "required_spare": "NONE",
            "required_trade": "AVIONICS",
            "est_duration": "1.0 Hour",
            "data_class": "DERIVED",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance Overview
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/maintenance/overview")
def get_maintenance_overview():
    """Maintenance queue, spares, and crew status with provenance."""
    mode = get_data_mode()
    state = load_fleet_state()
    spares_df = state["spares"].to_dict(orient="records") if mode != "REAL_ONLY" else []
    crew_df = state["crew"].to_dict(orient="records") if mode != "REAL_ONLY" else []
    eval_res = evaluate_fleet_availability(state)

    queue = []
    for tail, status in eval_res["tail_states"].items():
        if status in ("NMC", "PMC"):
            reasons = eval_res["tail_grounding_reasons"].get(tail, ["Scheduled Service Required"])
            queue.append({
                "tail_no": tail,
                "status": status,
                "issue": reasons[0] if reasons else "Routine Inspection",
                "priority": "P1" if status == "NMC" else "P2",
                "required_action": "Inspect & Replace Component",
                "est_duration": "4.0h",
                "data_class": "PREDICTED" if mode == "REAL_ONLY" else "SIMULATION",
            })

    return {
        "data_class": "REAL_ONLY" if mode == "REAL_ONLY" else "SIMULATION",
        "provenance_note": (
            "Maintenance queue derived from FAA SDR failure risk priors and N-CMAPSS RUL predictions. "
            "Spares and crew telemetry: N/A (No verified real military MRO database connected)."
            if mode == "REAL_ONLY" else
            "Maintenance queue is simulation-derived from RUL model predictions. Spares and crew data are synthetic."
        ),
        "queue": queue,
        "spares": spares_df,
        "crew": crew_df,
        "spares_status": "N/A — No verified real source available" if mode == "REAL_ONLY" else "SYNTHETIC",
        "crew_status": "N/A — No verified real source available" if mode == "REAL_ONLY" else "SYNTHETIC",
    }


# ─────────────────────────────────────────────────────────────────────────────
# What-If Simulation
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/whatif", response_model=WhatIfResponse)
def run_whatif_simulation(req: WhatIfRequest):
    """Run a what-if scenario against current fleet state."""
    state = load_fleet_state()
    base_eval = evaluate_fleet_availability(state)
    eval_res, meta = apply_whatif_lever(state, req.lever)

    return WhatIfResponse(
        latency_ms=meta["latency_ms"],
        before_mc_rate=base_eval["summary"]["current_mc_rate"],
        after_mc_rate=eval_res["summary"]["current_mc_rate"],
        mc_forecast=eval_res["mc_forecast"],
        unfilled_sorties=eval_res["unfilled_sorties"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cannibalization Advisor
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/cannibalization/advice", response_model=CannibalResponse)
def request_cannibalization_advice(req: CannibalRequest):
    """Evaluate a cannibalization proposal between donor and recipient aircraft."""
    state = load_fleet_state()
    approved, msg, details = evaluate_cannibalization_proposal(
        state, req.donor_tail, req.recipient_tail, req.comp_class
    )
    if approved:
        record_cannibalization_debt(req.donor_tail, req.recipient_tail, req.comp_class)

    return CannibalResponse(approved=approved, message=msg, details=details)


# ─────────────────────────────────────────────────────────────────────────────
# Audit Chain
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/audit/verify")
def verify_audit_chain():
    """Verify the integrity of the audit hash chain."""
    is_valid = verify_audit_log()
    return {
        "data_class": "AUDIT",
        "chain_valid": is_valid,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Static Frontend
# ─────────────────────────────────────────────────────────────────────────────

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    if os.path.exists(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
