import hashlib
import json
import sqlite3
import pandas as pd
import datetime
from typing import Dict, Any, List
from gen.db import get_connection, DB_PATH

def schedule_1day_crew(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    crew_df = state["crew"]
    aircraft_df = state["aircraft"]
    
    allocations = []
    # Simple priority-weighted greedy allocation
    nmc_tails = aircraft_df[aircraft_df["status"] == "NMC"].sort_values("mission_priority", ascending=True)

    for _, crew_member in crew_df.iterrows():
        avail_h = crew_member["available_h_per_day"]
        trade = crew_member["trade"]
        
        if avail_h <= 0:
            continue
            
        assigned_tail = None
        if not nmc_tails.empty:
            assigned_tail = nmc_tails.iloc[0]["tail_no"]
            
        allocations.append({
            "crew_id": crew_member["id"],
            "name": crew_member["name"],
            "trade": trade,
            "allocated_hours": min(avail_h, 8.0),
            "assigned_tail": assigned_tail or "UNASSIGNED"
        })
        
    return allocations

def append_audit_entry(actor: str, action: str, entity: str, entity_id: str, detail: Dict[str, Any], db_path: str = DB_PATH) -> str:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    prev_hash = last_row[0] if last_row else "0" * 64
    
    ts = datetime.datetime.now().isoformat()
    detail_json = json.dumps(detail)
    
    row_content = f"{ts}|{actor}|{action}|{entity}|{entity_id}|{detail_json}|{prev_hash}"
    row_hash = hashlib.sha256(row_content.encode("utf-8")).hexdigest()
    
    with conn:
        conn.execute(
            "INSERT INTO audit_log (ts, actor, action, entity, entity_id, detail_json, prev_hash, row_hash, synthetic) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (ts, actor, action, entity, entity_id, detail_json, prev_hash, row_hash)
        )
        
    conn.close()
    return row_hash

def verify_audit_log(db_path: str = DB_PATH) -> bool:
    conn = get_connection(db_path)
    audit_rows = pd.read_sql_query("SELECT * FROM audit_log ORDER BY id ASC", conn)
    conn.close()
    
    if audit_rows.empty:
        return True
        
    prev_hash = "0" * 64
    for _, row in audit_rows.iterrows():
        expected_content = f"{row['ts']}|{row['actor']}|{row['action']}|{row['entity']}|{row['entity_id']}|{row['detail_json']}|{prev_hash}"
        computed_hash = hashlib.sha256(expected_content.encode("utf-8")).hexdigest()
        
        if computed_hash != row["row_hash"] or row["prev_hash"] != prev_hash:
            return False
            
        prev_hash = row["row_hash"]
        
    return True
