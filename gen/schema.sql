-- READYFLEET Database Schema (SQLite)
-- All data is synthetic. Every table supports reproducible seeding.

CREATE TABLE IF NOT EXISTS aircraft (
    tail_no TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    base TEXT NOT NULL,
    mission_priority INTEGER NOT NULL CHECK (mission_priority BETWEEN 1 AND 3),
    status TEXT NOT NULL CHECK (status IN ('MC', 'PMC', 'NMC')),
    synthetic INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS component (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tail_no TEXT NOT NULL,
    comp_class TEXT NOT NULL CHECK (comp_class IN ('engine', 'avionics', 'hydraulics', 'airframe')),
    serial_no TEXT NOT NULL,
    installed_cycles INTEGER NOT NULL DEFAULT 0,
    installed_hours REAL NOT NULL DEFAULT 0.0,
    synthetic INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (tail_no) REFERENCES aircraft (tail_no) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sensor_reading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    cycle INTEGER NOT NULL,
    op_setting_1 REAL NOT NULL,
    op_setting_2 REAL NOT NULL,
    op_setting_3 REAL NOT NULL,
    sensor_1 REAL NOT NULL,
    sensor_2 REAL NOT NULL,
    sensor_3 REAL NOT NULL,
    sensor_4 REAL NOT NULL,
    sensor_5 REAL NOT NULL,
    sensor_6 REAL NOT NULL,
    sensor_7 REAL NOT NULL,
    sensor_8 REAL NOT NULL,
    sensor_9 REAL NOT NULL,
    sensor_10 REAL NOT NULL,
    sensor_11 REAL NOT NULL,
    sensor_12 REAL NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (component_id) REFERENCES component (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS maintenance_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tail_no TEXT NOT NULL,
    component_id INTEGER,
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    task_type TEXT NOT NULL CHECK (task_type IN ('scheduled', 'unscheduled')),
    crew_hours REAL NOT NULL,
    spare_used_id TEXT,
    synthetic INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (tail_no) REFERENCES aircraft (tail_no) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES component (id) ON DELETE SET NULL,
    FOREIGN KEY (spare_used_id) REFERENCES spare (part_no) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS spare (
    part_no TEXT PRIMARY KEY,
    comp_class TEXT NOT NULL CHECK (comp_class IN ('engine', 'avionics', 'hydraulics', 'airframe')),
    qty_on_hand INTEGER NOT NULL DEFAULT 0,
    qty_due_in INTEGER NOT NULL DEFAULT 0,
    lead_time_h REAL NOT NULL,
    expedited_lead_time_h REAL NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS crew (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trade TEXT NOT NULL,
    shift TEXT NOT NULL,
    available_h_per_day REAL NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sortie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tail_no TEXT,
    date DATE NOT NULL,
    mission_type TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 3),
    required_status TEXT NOT NULL CHECK (required_status IN ('FMC', 'PMC')),
    synthetic INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (tail_no) REFERENCES aircraft (tail_no) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS prediction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    predicted_rul_h REAL NOT NULL,
    ci_low REAL NOT NULL,
    ci_high REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synthetic INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (component_id) REFERENCES component (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scenario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_run_id TEXT NOT NULL,
    lever_json TEXT NOT NULL,
    result_mc_rate REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synthetic INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 1
);
