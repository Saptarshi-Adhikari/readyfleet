import os
import json
from models.registry import load_model_artifact, MODEL_DIR
from gen.seed import update_metrics

COMP_CLASSES = ["engine", "avionics", "hydraulics", "airframe"]

def evaluate_and_print_summary():
    print("\n" + "="*70)
    print(" READYFLEET RUL MODEL EVALUATION SUMMARY (JUDGE EVIDENCE PRINT-OUT)")
    print("="*70)
    print(f"{'Comp Class':<12} | {'RMSE':<8} | {'Baseline RMSE':<14} | {'MAE':<8} | {'Baseline MAE':<14}")
    print("-" * 70)

    summary = {}

    for comp_class in COMP_CLASSES:
        try:
            _, metrics = load_model_artifact(comp_class)
            print(f"{metrics['comp_class']:<12} | {metrics['rmse']:<8.2f} | {metrics['baseline_rmse']:<14.2f} | {metrics['mae']:<8.2f} | {metrics['baseline_mae']:<14.2f}")
            summary[comp_class] = metrics
        except Exception as e:
            print(f"{comp_class:<12} | NOT TRAINED")

    print("="*70 + "\n")
    update_metrics({"ml_eval_summary": summary})
    return summary

if __name__ == "__main__":
    evaluate_and_print_summary()
