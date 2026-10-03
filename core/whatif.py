import time
import json
from typing import Dict, Any, List
from core.state import clone_state
from core.aggregator import evaluate_fleet_availability

def apply_whatif_lever(state: Dict[str, Any], lever: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    cloned = clone_state(state)
    lever_type = lever.get("type")

    if lever_type == "expedite_spares":
        part_no = lever.get("part_no")
        spares = cloned["spares"]
        mask = spares["part_no"] == part_no
        if mask.any():
            # Expediting reduces lead time to expedited_lead_time_h
            exp_lead = spares.loc[mask, "expedited_lead_time_h"].values[0]
            spares.loc[mask, "lead_time_h"] = exp_lead
            spares.loc[mask, "qty_on_hand"] += 1  # Simulate expedited unit arrival

    elif lever_type == "reassign_crew":
        from_trade = lever.get("from_trade")
        to_trade = lever.get("to_trade")
        hours = lever.get("hours", 4.0)
        crew = cloned["crew"]
        
        mask_from = crew["trade"] == from_trade
        mask_to = crew["trade"] == to_trade
        if mask_from.any() and mask_to.any():
            crew.loc[mask_from, "available_h_per_day"] = crew.loc[mask_from, "available_h_per_day"].apply(lambda h: max(0.0, h - hours))
            crew.loc[mask_to, "available_h_per_day"] += hours

    elif lever_type == "cannibalize":
        donor_tail = lever.get("donor_tail")
        recipient_tail = lever.get("recipient_tail")
        comp_class = lever.get("comp_class")
        
        comps = cloned["components"]
        preds = cloned["predictions"]
        
        # Move donor's component RUL to recipient
        donor_comp = comps[(comps["tail_no"] == donor_tail) & (comps["comp_class"] == comp_class)]
        rec_comp = comps[(comps["tail_no"] == recipient_tail) & (comps["comp_class"] == comp_class)]
        
        if not donor_comp.empty and not rec_comp.empty:
            donor_id = donor_comp["id"].values[0]
            rec_id = rec_comp["id"].values[0]
            
            donor_rul = preds.loc[preds["component_id"] == donor_id, "predicted_rul_h"].values[0]
            
            # Recipient gets donor RUL, donor component gets set to 0.0 RUL (grounded)
            preds.loc[preds["component_id"] == rec_id, "predicted_rul_h"] = donor_rul
            preds.loc[preds["component_id"] == donor_id, "predicted_rul_h"] = 0.0

    start_t = time.perf_counter()
    eval_result = evaluate_fleet_availability(cloned)
    latency_ms = (time.perf_counter() - start_t) * 1000.0

    meta = {
        "latency_ms": latency_ms,
        "lever_applied": lever
    }
    return eval_result, meta
