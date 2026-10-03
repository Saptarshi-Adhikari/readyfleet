import pandas as pd
import numpy as np
import sqlite3
from gen.db import get_connection, DB_PATH

def extract_component_features(conn: sqlite3.Connection, comp_id: int) -> pd.DataFrame:
    query = """
        SELECT cycle, op_setting_1, op_setting_2, op_setting_3,
               sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6,
               sensor_7, sensor_8, sensor_9, sensor_10, sensor_11, sensor_12
        FROM sensor_reading
        WHERE component_id = ?
        ORDER BY cycle ASC
    """
    df = pd.read_sql_query(query, conn, params=(comp_id,))
    if df.empty:
        return pd.DataFrame()

    sensor_cols = [f"sensor_{i}" for i in range(1, 13)]
    
    # 10- and 30-cycle rolling stats
    for col in sensor_cols:
        df[f"{col}_mean_10"] = df[col].rolling(window=10, min_periods=1).mean()
        df[f"{col}_std_10"] = df[col].rolling(window=10, min_periods=1).std().fillna(0.0)
        df[f"{col}_min_10"] = df[col].rolling(window=10, min_periods=1).min()
        df[f"{col}_max_10"] = df[col].rolling(window=10, min_periods=1).max()

        df[f"{col}_mean_30"] = df[col].rolling(window=30, min_periods=1).mean()
        df[f"{col}_std_30"] = df[col].rolling(window=30, min_periods=1).std().fillna(0.0)
        df[f"{col}_min_30"] = df[col].rolling(window=30, min_periods=1).min()
        df[f"{col}_max_30"] = df[col].rolling(window=30, min_periods=1).max()

    return df

def build_dataset_for_class(db_path: str = DB_PATH, comp_class: str = "engine") -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    conn = get_connection(db_path)
    query = """
        SELECT c.id, c.tail_no, c.comp_class, c.installed_cycles, c.installed_hours
        FROM component c
        WHERE c.comp_class = ?
    """
    components = pd.read_sql_query(query, conn, params=(comp_class,))
    
    feature_dfs = []
    targets = []
    tails = []
    
    for _, comp in components.iterrows():
        comp_id = comp["id"]
        tail_no = comp["tail_no"]
        total_cycles = comp["installed_cycles"]
        hours_per_cycle = comp["installed_hours"] / max(total_cycles, 1)
        
        df_feat = extract_component_features(conn, comp_id)
        if df_feat.empty:
            continue
            
        # Target: RUL in hours, capped at 125h (piecewise linear RUL trick)
        for idx, row in df_feat.iterrows():
            current_cycle = row["cycle"]
            remaining_cycles = total_cycles - current_cycle
            rul_hours = remaining_cycles * hours_per_cycle
            capped_rul = min(float(rul_hours), 125.0)
            
            feature_dfs.append(row)
            targets.append(capped_rul)
            tails.append(tail_no)

    conn.close()
    
    X = pd.DataFrame(feature_dfs).reset_index(drop=True)
    y = pd.Series(targets, name="target_rul").reset_index(drop=True)
    tail_series = pd.Series(tails, name="tail_no").reset_index(drop=True)
    
    return X, y, tail_series
