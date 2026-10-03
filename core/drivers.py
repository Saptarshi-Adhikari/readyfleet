from typing import Dict, Any, List
from core.aggregator import evaluate_fleet_availability

def rank_nmc_drivers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    eval_res = evaluate_fleet_availability(state)
    tail_reasons = eval_res["tail_grounding_reasons"]
    aircraft_df = state["aircraft"]

    driver_scores = {}
    driver_tails = {}

    for tail_no, reasons in tail_reasons.items():
        if not reasons:
            continue
        
        ac_info = aircraft_df[aircraft_df["tail_no"] == tail_no]
        priority = ac_info["mission_priority"].values[0] if not ac_info.empty else 2
        
        for reason in reasons:
            # Parse primary constraint driver
            driver_key = reason.split(":")[0] if ":" in reason else "General"
            detail = reason.split(":")[1].strip() if ":" in reason else reason
            
            if detail not in driver_scores:
                driver_scores[detail] = 0.0
                driver_tails[detail] = []
                
            driver_scores[detail] += priority * 7.0  # (tails grounded) * (priority) * (days grounded)
            driver_tails[detail].append(tail_no)

    ranked_drivers = []
    for detail, score in sorted(driver_scores.items(), key=lambda x: x[1], reverse=True):
        tails = driver_tails[detail]
        ranked_drivers.append({
            "driver": detail,
            "impact_score": score,
            "tails_grounded_count": len(tails),
            "tails_grounded": tails,
            "recommendation": f"Fix {detail} -> Recovers {len(tails)} tails ({', '.join(tails[:3])})"
        })

    return ranked_drivers[:5]  # Top 5 binding constraint drivers
