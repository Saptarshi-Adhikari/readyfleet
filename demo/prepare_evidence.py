import os
import json
import datetime
from gen.seed import compute_file_sha256, update_metrics
from models.eval import evaluate_and_print_summary

def bundle_evidence():
    print("Bundling READYFLEET evidence for judges...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "readyfleet.db")
    
    db_hash = compute_file_sha256(db_path) if os.path.exists(db_path) else "N/A"
    summary = evaluate_and_print_summary()
    
    evidence_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "db_sha256_hash": db_hash,
        "eval_summary": summary,
        "data_class": "synthetic"
    }
    
    update_metrics(evidence_data)
    print("Evidence bundled successfully into evidence/metrics.json!")

if __name__ == "__main__":
    bundle_evidence()
