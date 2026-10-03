from typing import Dict
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from features.build import build_dataset_for_class
from models.registry import save_model_artifact
from gen.db import DB_PATH

COMP_CLASSES = ["engine", "avionics", "hydraulics", "airframe"]

def train_rul_models(db_path: str = DB_PATH) -> Dict[str, Dict[str, float]]:
    all_metrics = {}
    
    for comp_class in COMP_CLASSES:
        X, y, tails = build_dataset_for_class(db_path, comp_class)
        if X.empty:
            continue

        # Split BY TAIL (no data leakage across tails)
        unique_tails = tails.unique()
        split_idx = int(len(unique_tails) * 0.8)
        train_tails = set(unique_tails[:split_idx])
        test_tails = set(unique_tails[split_idx:])

        train_mask = tails.isin(train_tails)
        test_mask = tails.isin(test_tails)

        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]

        # Model: HistGradientBoostingRegressor
        model = HistGradientBoostingRegressor(
            max_iter=100,
            early_stopping=True,
            random_state=42
        )
        model.fit(X_train, y_train)

        # Predictions
        preds = model.predict(X_test)
        
        # Naive baseline: predicting mean of target
        baseline_pred = np.full_like(y_test, y_train.mean())

        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        
        base_rmse = float(np.sqrt(mean_squared_error(y_test, baseline_pred)))
        base_mae = float(mean_absolute_error(y_test, baseline_pred))

        metrics = {
            "comp_class": comp_class,
            "rmse": rmse,
            "mae": mae,
            "baseline_rmse": base_rmse,
            "baseline_mae": base_mae,
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test))
        }

        save_model_artifact(comp_class, model, metrics)
        all_metrics[comp_class] = metrics

    return all_metrics

if __name__ == "__main__":
    results = train_rul_models()
    print("Trained models for all component classes.")
