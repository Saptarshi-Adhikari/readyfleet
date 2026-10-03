import sqlite3
import json
import hashlib
import datetime
from typing import Dict, Any, List
from gen.db import get_connection, DB_PATH

def evaluate_cannibalization_proposal(state: Dict[str, Any], donor_tail: str, recipient_tail: str, comp_class: str) -> tuple[bool, str, Dict[str, Any]]:
    aircraft_df = state["aircraft"]
    
    donor_ac = aircraft_df[aircraft_df["tail_no"] == donor_tail]
    rec_ac = aircraft_df[aircraft_df["tail_no"] == recipient_tail]

    if donor_ac.empty or rec_ac.empty:
        return False, "Invalid aircraft tail numbers specified.", {}

    donor_prio = donor_ac["mission_priority"].values[0]
    rec_prio = rec_ac["mission_priority"].values[0]
    donor_status = donor_ac["status"].values[0]

    # Guardrail 1: Donor priority must be strictly lower than recipient priority
    if donor_prio <= rec_prio:
        return False, f"Refused: Donor priority ({donor_prio}) must be strictly lower than recipient priority ({rec_prio}).", {}

    # Guardrail 2: Donor must already be NMC
    if donor_status != "NMC":
        return False, f"Refused: Donor aircraft ({donor_tail}) is currently {donor_status}. Cannibalization only allowed from NMC tails.", {}

    proposal_summary = {
        "donor_tail": donor_tail,
        "recipient_tail": recipient_tail,
        "comp_class": comp_class,
        "net_mc_impact": "+1 Ready Airframe",
        "guardrails_passed": ["lower_priority_donor", "already_nmc_donor"]
    }
    return True, "Cannibalization proposal approved.", proposal_summary

def record_cannibalization_debt(donor_tail: str, recipient_tail: str, comp_class: str, db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    detail = json.dumps({
        "donor_tail": donor_tail,
        "recipient_tail": recipient_tail,
        "comp_class": comp_class,
        "debt_status": "repayment_pending"
    })

    # Append to hash-chained audit log
    cursor = conn.cursor()
    cursor.execute("SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    prev_hash = last_row[0] if last_row else "0" * 64

    ts = datetime.datetime.now().isoformat()
    actor = "COMMANDER"
    action = "CANNIBALIZATION_APPROVED"
    entity = "AIRCRAFT"
    entity_id = recipient_tail

    row_content = f"{ts}|{actor}|{action}|{entity}|{entity_id}|{detail}|{prev_hash}"
    row_hash = hashlib.sha256(row_content.encode("utf-8")).hexdigest()

    with conn:
        conn.execute(
            "INSERT INTO audit_log (ts, actor, action, entity, entity_id, detail_json, prev_hash, row_hash, synthetic) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (ts, actor, action, entity, entity_id, detail, prev_hash, row_hash)
        )
    conn.close()
