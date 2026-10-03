import sqlite3
import unittest
import tempfile
import os
import shutil
from gen.db import init_db, get_connection
from gen.seed import compute_file_sha256
from gen.generate import generate_all_data

class TestDataFoundation(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_db_initialization(self):
        test_db = os.path.join(self.tmp_dir, "test_readyfleet.db")
        test_schema = "gen/schema.sql"
        init_db(test_db, test_schema)
        
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = [
            "aircraft", "component", "sensor_reading", "maintenance_record",
            "spare", "crew", "sortie", "prediction", "scenario", "audit_log"
        ]
        for tbl in expected_tables:
            self.assertIn(tbl, tables)

    def test_synthetic_flag_on_all_rows(self):
        test_db = os.path.join(self.tmp_dir, "test_readyfleet.db")
        generate_all_data(test_db, seed=42)
        
        conn = get_connection(test_db)
        cursor = conn.cursor()
        
        tables = ["aircraft", "component", "sensor_reading", "spare", "crew", "sortie"]
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl} WHERE synthetic != 1")
            non_synthetic_count = cursor.fetchone()[0]
            self.assertEqual(non_synthetic_count, 0, f"Table {tbl} has non-synthetic rows!")
            
        conn.close()

    def test_generator_determinism(self):
        db1 = os.path.join(self.tmp_dir, "run1.db")
        db2 = os.path.join(self.tmp_dir, "run2.db")
        
        generate_all_data(db1, seed=123)
        generate_all_data(db2, seed=123)
        
        hash1 = compute_file_sha256(db1)
        hash2 = compute_file_sha256(db2)
        
        self.assertEqual(hash1, hash2, "Generator is not deterministic for identical seeds!")

if __name__ == "__main__":
    unittest.main()

