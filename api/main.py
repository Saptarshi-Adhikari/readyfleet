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

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "READYFLEET API", "data_class": "synthetic"}

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
