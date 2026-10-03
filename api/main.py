from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

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

app = FastAPI(
    title="READYFLEET Decision Intelligence API",
    description="Fleet-Availability Decision Layer for Air Power (SIH26249)",
    version="1.0.0"
)

from data_sources.manager import get_active_data_sources

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "READYFLEET API", "data_class": "synthetic"}

@app.get("/api/data-mode")
def get_data_mode():
    _, prov = get_active_data_sources()
    return {
        "data_class": "hybrid_prototype",
        "provenance": prov
    }

@app.get("/api/fleet/status", response_model=FleetStatusResponse)
def get_fleet_status():
    state = load_fleet_state()
    res = evaluate_fleet_availability(state)
    summary = res["summary"]
    return FleetStatusResponse(
        total_tails=summary["total_tails"],
        mc_count=summary["mc_count"],
        pmc_count=summary["pmc_count"],
        nmc_count=summary["nmc_count"],
        current_mc_rate=summary["current_mc_rate"],
        tail_states=res["tail_states"]
    )

@app.get("/api/fleet/forecast", response_model=ForecastResponse)
def get_fleet_forecast():
    state = load_fleet_state()
    res = evaluate_fleet_availability(state)
    return ForecastResponse(
        mc_forecast=res["mc_forecast"],
        unfilled_sorties=res["unfilled_sorties"]
    )

@app.get("/api/drivers")
def get_nmc_drivers():
    state = load_fleet_state()
    drivers = rank_nmc_drivers(state)
    return {"data_class": "synthetic", "drivers": drivers}

@app.post("/api/whatif", response_model=WhatIfResponse)
def run_whatif_simulation(req: WhatIfRequest):
    state = load_fleet_state()
    base_eval = evaluate_fleet_availability(state)
    eval_res, meta = apply_whatif_lever(state, req.lever)
    
    return WhatIfResponse(
        latency_ms=meta["latency_ms"],
        before_mc_rate=base_eval["summary"]["current_mc_rate"],
        after_mc_rate=eval_res["summary"]["current_mc_rate"],
        mc_forecast=eval_res["mc_forecast"],
        unfilled_sorties=eval_res["unfilled_sorties"]
    )

@app.post("/api/cannibalization/advice", response_model=CannibalResponse)
def request_cannibalization_advice(req: CannibalRequest):
    state = load_fleet_state()
    approved, msg, details = evaluate_cannibalization_proposal(
        state, req.donor_tail, req.recipient_tail, req.comp_class
    )
    if approved:
        record_cannibalization_debt(req.donor_tail, req.recipient_tail, req.comp_class)
        
    return CannibalResponse(
        approved=approved,
        message=msg,
        details=details
    )

@app.get("/api/aircraft/{tail_no}")
def get_aircraft_detail(tail_no: str):
    state = load_fleet_state()
    ac_df = state["aircraft"]
    ac_row = ac_df[ac_df["tail_no"] == tail_no]
    if ac_row.empty:
        raise HTTPException(status_code=404, detail="Aircraft tail number not found")
        
    ac_info = ac_row.iloc[0].to_dict()
    
    # Get components and predictions
    comps_df = state["components"]
    ac_comps = comps_df[comps_df["tail_no"] == tail_no]
    preds_df = state["predictions"]
    
    components_detail = []
    blocking_constraint = None
    
    for _, comp in ac_comps.iterrows():
        comp_id = comp["id"]
        pred_row = preds_df[preds_df["component_id"] == comp_id]
        rul = pred_row["predicted_rul_h"].values[0] if not pred_row.empty else 999.0
        ci_low = pred_row["ci_low"].values[0] if not pred_row.empty else 0.0
        ci_high = pred_row["ci_high"].values[0] if not pred_row.empty else 999.0
        
        comp_data = {
            "id": int(comp["id"]),
            "comp_class": comp["comp_class"],
            "serial_no": comp["serial_no"],
            "installed_cycles": int(comp["installed_cycles"]),
            "installed_hours": float(comp["installed_hours"]),
            "predicted_rul_h": float(rul),
            "ci_low": float(ci_low),
            "ci_high": float(ci_high),
            "threshold_h": 24.0,
            "status": "CRITICAL" if rul < 24.0 else "HEALTHY"
        }
        components_detail.append(comp_data)
        
        if rul < 24.0 and blocking_constraint is None:
            blocking_constraint = {
                "reason": f"{comp['comp_class'].upper()} RUL ({rul:.1f}h) BELOW 24h THRESHOLD",
                "required_action": f"Perform {comp['comp_class']} overhaul / replacement",
                "required_spare": f"PART-{comp['comp_class'][:3].upper()}-01",
                "required_trade": comp["comp_class"],
                "est_duration": "4.5 Hours"
            }
            
    eval_res = evaluate_fleet_availability(state)
    reasons = eval_res["tail_grounding_reasons"].get(tail_no, [])

    return {
        "data_class": "synthetic",
        "aircraft": ac_info,
        "components": components_detail,
        "grounding_reasons": reasons,
        "blocking_constraint": blocking_constraint or {
            "reason": "NONE - AIRCRAFT IS FLYABLE / MC",
            "required_action": "Standard Pre-Flight Inspection",
            "required_spare": "NONE",
            "required_trade": "AVIONICS",
            "est_duration": "1.0 Hour"
        }
    }

@app.get("/api/maintenance/overview")
def get_maintenance_overview():
    state = load_fleet_state()
    spares_df = state["spares"].to_dict(orient="records")
    crew_df = state["crew"].to_dict(orient="records")
    eval_res = evaluate_fleet_availability(state)
    
    # Maintenance Queue derived from NMC & PMC tails
    queue = []
    for tail, status in eval_res["tail_states"].items():
        if status in ["NMC", "PMC"]:
            reasons = eval_res["tail_grounding_reasons"].get(tail, ["Scheduled Service Required"])
            queue.append({
                "tail_no": tail,
                "status": status,
                "issue": reasons[0] if reasons else "Routine Inspection",
                "priority": "P1" if status == "NMC" else "P2",
                "required_action": "Inspect & Replace Component",
                "est_duration": "4.0h"
            })

    return {
        "data_class": "synthetic",
        "queue": queue,
        "spares": spares_df,
        "crew": crew_df
    }

@app.get("/api/audit/verify")
def verify_audit_chain():
    is_valid = verify_audit_log()
    return {"data_class": "synthetic", "chain_valid": is_valid}

# Mount frontend static files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    if os.path.exists(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
