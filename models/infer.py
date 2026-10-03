import uuid
import sqlite3
import pandas as pd
import numpy as np
from gen.db import get_connection, DB_PATH
from features.build import extract_component_features
from models.registry import load_model_artifact

COMP_CLASSES = ["engine", "avionics", "hydraulics", "airframe"]

def run_batch_inference(db_path: str = DB_PATH) -> str:
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection(db_path)
    
    # Load all models and their MAEs for prediction interval bounds (±1.5x MAE)
    models = {}
    maes = {}
    for cc in COMP_CLASSES:
        try:
            m, met = load_model_artifact(cc)
            models[cc] = m
            maes[cc] = met["mae"]
        except Exception:
            pass

    query = "SELECT id, comp_class FROM component"
    components = pd.read_sql_query(query, conn)
    
    pred_rows = []
    for _, comp in components.iterrows():
        comp_id = comp["id"]
        comp_class = comp["comp_class"]
        
        if comp_class not in models:
            continue
            
        model = models[comp_class]
        mae = maes[comp_class]
        
        df_feat = extract_component_features(conn, comp_id)
        if df_feat.empty:
            continue
            
        # Perform inference on the latest cycle reading
        latest_reading = df_feat.iloc[[-1]]
        predicted_rul = float(model.predict(latest_reading)[0])
        
        ci_low = max(0.0, float(predicted_rul - 1.5 * mae))
        ci_high = float(predicted_rul + 1.5 * mae)
        
        pred_rows.append((comp_id, run_id, predicted_rul, ci_low, ci_high, 1))

    with conn:
        conn.executemany(
            "INSERT INTO prediction (component_id, run_id, predicted_rul_h, ci_low, ci_high, synthetic) VALUES (?, ?, ?, ?, ?, ?)",
            pred_rows
        )
        
    conn.close()
    print(f"Batch inference complete! Run ID: {run_id} ({len(pred_rows)} predictions generated)")
    return run_id

if __name__ == "__main__":
    run_batch_inference()
