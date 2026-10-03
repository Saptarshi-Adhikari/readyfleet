import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List
from core.state import load_thresholds

def evaluate_fleet_availability(state: Dict[str, Any], config_path: str = None) -> Dict[str, Any]:
    thresholds = load_thresholds() if config_path is None else load_thresholds(config_path)
    crit_rul_threshold = thresholds.get("critical_rul_h", 24.0)

    aircraft_df = state["aircraft"]
    components_df = state["components"]
    spares_df = state["spares"]
    crew_df = state["crew"]
    sorties_df = state["sorties"]
    preds_df = state["predictions"]

    # Merge component predictions with spares
    comp_preds = components_df.merge(preds_df, left_on="id", right_on="component_id", how="left")
    comp_preds = comp_preds.merge(spares_df, left_on="comp_class", right_on="comp_class", how="left")

    tail_states = {}
    tail_grounding_reasons = {}

    for _, ac in aircraft_df.iterrows():
        tail_no = ac["tail_no"]
        ac_comps = comp_preds[comp_preds["tail_no"] == tail_no]

        is_nmc = False
        reasons = []

        for _, comp in ac_comps.iterrows():
            rul = comp.get("predicted_rul_h", 999.0)
            qty_hand = comp.get("qty_on_hand", 0)
            lead_h = comp.get("lead_time_h", 0.0)

            # R1: RUL < 24h critical threshold
            if rul < crit_rul_threshold:
                is_nmc = True
                reasons.append(f"R1: Critical RUL {rul:.1f}h < {crit_rul_threshold}h on {comp['comp_class']}")

            # R2: Supply grounding - RUL < lead time and zero stock
            if rul < lead_h and qty_hand == 0:
                is_nmc = True
                reasons.append(f"R2: No spare on hand for {comp['comp_class']} (Lead time {lead_h:.0f}h)")

        if is_nmc:
            status = "NMC"
        else:
            # Check if PMC (e.g. slight RUL degradation or minor warning)
            min_rul = ac_comps["predicted_rul_h"].min() if not ac_comps.empty else 999.0
            status = "PMC" if min_rul < 50.0 else "MC"

        tail_states[tail_no] = status
        tail_grounding_reasons[tail_no] = reasons

    total_tails = len(aircraft_df)
    mc_tails = sum(1 for s in tail_states.values() if s == "MC")
    pmc_tails = sum(1 for s in tail_states.values() if s == "PMC")
    nmc_tails = sum(1 for s in tail_states.values() if s == "NMC")

    current_mc_rate = float(mc_tails / total_tails) if total_tails > 0 else 0.0

    # 7-day forecast projection & unfilled sortie count
    mc_forecast = []
    unfilled_sorties = []
    today = datetime.date.today()

    for day_offset in range(7):
        # Projected degradation over 7 days (~5h flight time / day)
        proj_mc_tails = max(0, mc_tails - int(day_offset * 0.8))
        proj_mc_rate = float(proj_mc_tails / total_tails)
        mc_forecast.append(proj_mc_rate)

        # Count unfilled sorties
        s_date = (today + datetime.timedelta(days=day_offset)).isoformat()
        day_sorties = sorties_df[sorties_df["date"] == s_date] if "date" in sorties_df.columns else pd.DataFrame()
        needed = len(day_sorties)
        unfilled = max(0, needed - proj_mc_tails)
        unfilled_sorties.append(unfilled)

    return {
        "tail_states": tail_states,
        "tail_grounding_reasons": tail_grounding_reasons,
        "summary": {
            "total_tails": total_tails,
            "mc_count": mc_tails,
            "pmc_count": pmc_tails,
            "nmc_count": nmc_tails,
            "current_mc_rate": current_mc_rate
        },
        "mc_forecast": mc_forecast,
        "unfilled_sorties": unfilled_sorties,
        "data_class": "synthetic"
    }
