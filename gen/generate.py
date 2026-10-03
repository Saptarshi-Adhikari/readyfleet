import sqlite3
import numpy as np
import os
import datetime
from gen.db import init_db, get_connection, DB_PATH
from gen.degradation import generate_health_curve, generate_sensors_for_health
from gen.seed import compute_file_sha256, update_metrics

SEED = 42

def generate_all_data(db_path: str = DB_PATH, seed: int = SEED) -> None:
    init_db(db_path)
    rng = np.random.default_rng(seed)
    conn = get_connection(db_path)

    # 1. Populate Spares (Rotable inventory for component classes)
    spares_data = [
        ("PART-ENG-01", "engine", 3, 1, 48.0, 12.0),
        ("PART-AV-01", "avionics", 5, 2, 24.0, 6.0),
        ("PART-HYD-01", "hydraulics", 2, 0, 36.0, 8.0),
        ("PART-AF-01", "airframe", 4, 1, 72.0, 24.0),
    ]
    with conn:
        conn.executemany(
            "INSERT INTO spare (part_no, comp_class, qty_on_hand, qty_due_in, lead_time_h, expedited_lead_time_h, synthetic) VALUES (?, ?, ?, ?, ?, ?, 1)",
            spares_data
        )

    # 2. Populate Crew (Trades & Shifts)
    crew_data = [
        ("Tech-Alpha", "engine", "day", 8.0),
        ("Tech-Bravo", "avionics", "day", 8.0),
        ("Tech-Charlie", "hydraulics", "day", 8.0),
        ("Tech-Delta", "airframe", "day", 8.0),
        ("Tech-Echo", "engine", "night", 8.0),
    ]
    with conn:
        conn.executemany(
            "INSERT INTO crew (name, trade, shift, available_h_per_day, synthetic) VALUES (?, ?, ?, ?, 1)",
            crew_data
        )

    # 3. Populate Aircraft (40 Tails)
    comp_classes = ["engine", "avionics", "hydraulics", "airframe"]
    bases = ["Base-Alpha", "Base-Bravo", "Base-Charlie"]

    for i in range(1, 41):
        tail_no = f"SYN-{i:02d}"
        ac_type = "Fighter-Mk1" if i % 2 == 0 else "Transport-C1"
        base = bases[i % len(bases)]
        priority = int(rng.choice([1, 2, 3], p=[0.2, 0.5, 0.3]))
        status = "MC"

        with conn:
            conn.execute(
                "INSERT INTO aircraft (tail_no, type, base, mission_priority, status, synthetic) VALUES (?, ?, ?, ?, ?, 1)",
                (tail_no, ac_type, base, priority, status)
            )

        # Populate 4 Components per Tail
        for comp_class in comp_classes:
            serial_no = f"SN-{comp_class[:3].upper()}-{i:02d}"
            installed_cycles = int(rng.integers(50, 200))
            installed_hours = float(installed_cycles * 1.5)

            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO component (tail_no, comp_class, serial_no, installed_cycles, installed_hours, synthetic) VALUES (?, ?, ?, ?, ?, 1)",
                (tail_no, comp_class, serial_no, installed_cycles, installed_hours)
            )
            comp_id = cursor.lastrowid

            # Determine failure mode: 5% infant mortality, 10% no-fault
            roll = rng.random()
            is_infant = roll < 0.05
            is_no_fault = roll >= 0.90

            num_cycles = int(installed_cycles)
            health = generate_health_curve(num_cycles, is_infant_mortality=is_infant, is_no_fault=is_no_fault, rng=rng)
            op_settings, sensors = generate_sensors_for_health(health, rng=rng)

            # Insert sensor readings
            sensor_rows = []
            for cyc in range(num_cycles):
                row = (
                    comp_id,
                    cyc + 1,
                    float(op_settings[cyc, 0]),
                    float(op_settings[cyc, 1]),
                    float(op_settings[cyc, 2]),
                    *[float(sensors[cyc, s]) for s in range(12)],
                    1
                )
                sensor_rows.append(row)

            conn.executemany(
                "INSERT INTO sensor_reading (component_id, cycle, op_setting_1, op_setting_2, op_setting_3, "
                "sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6, sensor_7, sensor_8, sensor_9, sensor_10, sensor_11, sensor_12, synthetic) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                sensor_rows
            )

        # Create Digital Twin Registry Instance
        twin_id = f"DT-{tail_no}"
        now_str = "2026-10-04T00:00:00"
        with conn:
            conn.execute(
                "INSERT INTO digital_twin (twin_id, tail_no, twin_state, data_mode, last_sync_ts, sync_status, synthetic) "
                "VALUES (?, ?, 'SIMULATED', 'SYNTHETIC', ?, 'SYNCED-SIMULATION', 1)",
                (twin_id, tail_no, now_str)
            )

    # 4. Populate 7-Day Sortie Demand Schedule
    today = datetime.date.today()
    sortie_rows = []
    tails = [f"SYN-{i:02d}" for i in range(1, 41)]

    for day_offset in range(7):
        s_date = today + datetime.timedelta(days=day_offset)
        # Generate ~15 sorties per day
        for _ in range(15):
            t_no = rng.choice(tails)
            m_type = rng.choice(["PATROL", "RECON", "STRIKE", "TRAINING"])
            prio = int(rng.choice([1, 2, 3], p=[0.3, 0.4, 0.3]))
            req_status = "FMC" if prio == 1 else "PMC"
            sortie_rows.append((t_no, s_date.isoformat(), m_type, prio, req_status, 1))

    with conn:
        conn.executemany(
            "INSERT INTO sortie (tail_no, date, mission_type, priority, required_status, synthetic) VALUES (?, ?, ?, ?, ?, ?)",
            sortie_rows
        )

    conn.close()

    # Verify seed & SHA-256
    db_sha256 = compute_file_sha256(db_path)
    update_metrics({
        "seed": seed,
        "db_sha256": db_sha256,
        "generated_at": datetime.datetime.now().isoformat()
    })
    print(f"Dataset generated successfully! DB SHA-256: {db_sha256}")

if __name__ == "__main__":
    generate_all_data()
