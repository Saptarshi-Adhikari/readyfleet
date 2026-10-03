import sqlite3
import pandas as pd
import numpy as np
import yaml
import os
from typing import Dict, Any, List
from gen.db import get_connection, DB_PATH

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "thresholds.yaml")

def load_thresholds(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_fleet_state(db_path: str = DB_PATH) -> Dict[str, Any]:
    conn = get_connection(db_path)
    
    aircraft = pd.read_sql_query("SELECT * FROM aircraft", conn)
    components = pd.read_sql_query("SELECT * FROM component", conn)
    spares = pd.read_sql_query("SELECT * FROM spare", conn)
    crew = pd.read_sql_query("SELECT * FROM crew", conn)
    sorties = pd.read_sql_query("SELECT * FROM sortie", conn)
    
    # Get latest predictions per component
    pred_query = """
        SELECT p.component_id, p.predicted_rul_h, p.ci_low, p.ci_high
        FROM prediction p
        INNER JOIN (
            SELECT component_id, MAX(id) as max_id
            FROM prediction
            GROUP BY component_id
        ) latest ON p.id = latest.max_id
    """
    predictions = pd.read_sql_query(pred_query, conn)
    conn.close()
    
    return {
        "aircraft": aircraft,
        "components": components,
        "spares": spares,
        "crew": crew,
        "sorties": sorties,
        "predictions": predictions
    }

def clone_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "aircraft": state["aircraft"].copy(deep=True),
        "components": state["components"].copy(deep=True),
        "spares": state["spares"].copy(deep=True),
        "crew": state["crew"].copy(deep=True),
        "sorties": state["sorties"].copy(deep=True),
        "predictions": state["predictions"].copy(deep=True)
    }
