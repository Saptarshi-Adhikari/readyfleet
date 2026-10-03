import pickle
import json
import os
from typing import Dict, Any

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

def save_model_artifact(comp_class: str, model: Any, metrics: Dict[str, Any]) -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, f"model_{comp_class}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    metrics_path = os.path.join(MODEL_DIR, f"metrics_{comp_class}.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

def load_model_artifact(comp_class: str) -> tuple[Any, Dict[str, Any]]:
    model_path = os.path.join(MODEL_DIR, f"model_{comp_class}.pkl")
    metrics_path = os.path.join(MODEL_DIR, f"metrics_{comp_class}.json")
    
    if not os.path.exists(model_path) or not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Model or metrics artifact missing for class {comp_class}")
        
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
        
    return model, metrics
