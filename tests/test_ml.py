import unittest
import tempfile
import os
import shutil
import pandas as pd
from gen.db import init_db, get_connection
from gen.generate import generate_all_data
from features.build import build_dataset_for_class, extract_component_features
from models.train import train_rul_models
from models.registry import load_model_artifact
from models.infer import run_batch_inference

class TestMLEvidencePhase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_ml.db")
        generate_all_data(self.db_path, seed=42)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_feature_store_extraction(self):
        conn = get_connection(self.db_path)
        df_feat = extract_component_features(conn, comp_id=1)
        conn.close()
        
        self.assertFalse(df_feat.empty)
        self.assertIn("sensor_1_mean_10", df_feat.columns)
        self.assertIn("sensor_12_max_30", df_feat.columns)

    def test_model_training_and_artifacts(self):
        metrics = train_rul_models(self.db_path)
        for cc in ["engine", "avionics", "hydraulics", "airframe"]:
            self.assertIn(cc, metrics)
            model, meta = load_model_artifact(cc)
            self.assertIsNotNone(model)
            self.assertEqual(meta["comp_class"], cc)

    def test_batch_inference_predictions(self):
        train_rul_models(self.db_path)
        run_id = run_batch_inference(self.db_path)
        
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT component_id) FROM prediction WHERE run_id = ?", (run_id,))
        count, unique_comps = cursor.fetchone()
        conn.close()
        
        self.assertEqual(count, 160)  # 40 tails x 4 components
        self.assertEqual(unique_comps, 160)

if __name__ == "__main__":
    unittest.main()
