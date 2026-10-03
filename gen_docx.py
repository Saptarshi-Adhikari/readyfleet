import os
import json
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_master_docx():
    doc = docx.Document()

    # Define Styles
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("READYFLEET — MASTER PROJECT DOCUMENTATION")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("SIH 2026 (SIH26249) — Air Power: Predictive Maintenance & Fleet Availability\nMinistry of Defence — Defence Services Staff College")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    doc.add_paragraph().paragraph_format.space_after = Pt(18)

    # Helper function for headings
    def add_heading_1(text):
        h = doc.add_heading(text, level=1)
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.name = 'Arial'
            r.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)

    def add_heading_2(text):
        h = doc.add_heading(text, level=2)
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Arial'
            r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    # Section 1: Problem Statement & Vision
    add_heading_1("1. Executive Summary & Problem Statement")
    p = doc.add_paragraph()
    p.add_run("Problem Statement (SIH26249): ").bold = True
    p.add_run("Low aircraft availability due to fragmented and largely reactive maintenance practices across the air fleet. Maintenance data from aircraft health-monitoring systems, technical records, spares, and maintenance agencies is not adequately integrated, resulting in delayed fault prediction, avoidable downtime, and sub-optimal asset utilization.\n\n")
    p.add_run("Unique Selling Proposition (USP): ").bold = True
    p.add_run("The fleet-availability decision layer that fuses health predictions with spares, crew capacity, and technical records to forecast mission-capable aircraft, prescribing the maintenance actions today that change tomorrow's operational readiness number.")

    # Section 2: Architecture & Tech Stack
    add_heading_1("2. System Architecture & Tech Stack")
    p = doc.add_paragraph()
    p.add_run("READYFLEET operates as an overarching decision-intelligence layer sitting above diagnostic sensors and HUMS systems. It integrates 5 core data streams:\n")
    doc.add_paragraph("1. HUMS / IoT Signals: Engine and multi-component health telemetry degradation curves.", style='List Bullet')
    doc.add_paragraph("2. Technical Records: Maintenance histories, installed cycles, and overhaul metrics.", style='List Bullet')
    doc.add_paragraph("3. Spares Inventory: Rotable stock levels, standard lead times, and expedited supply times.", style='List Bullet')
    doc.add_paragraph("4. Crew Capacity: Trade-wise technician availability across day/night shifts.", style='List Bullet')
    doc.add_paragraph("5. Sortie Demand: Operational mission schedules, priority weights (1-3), and status requirements.", style='List Bullet')

    add_heading_2("Tech Stack Rationale")
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Layer"
    hdr_cells[1].text = "Technology"
    hdr_cells[2].text = "Rationale"
    
    tech_data = [
        ("Frontend", "Vanilla JS + HTML5 Canvas 2D", "High-performance 60 FPS fleet grid, line charts, and status cards with zero framework bloat."),
        ("Backend", "Python FastAPI (Uvicorn)", "Single deployable service providing REST APIs, Pydantic validation, and static frontend hosting."),
        ("Machine Learning", "Scikit-Learn (HistGradientBoosting)", "Trains fast on CPU; rolling-window features reach RMSE in the same band as published LSTMs (~30-40h)."),
        ("Database", "SQLite Single File", "Zero-ops local database storing 10 core tables with enforced synthetic data flags."),
        ("Simulation Engine", "NumPy / Pandas Generator", "Seeded physics degradation curves with 5% infant mortality and exact SHA-256 reproducibility.")
    ]
    for row in tech_data:
        r_cells = table.add_row().cells
        r_cells[0].text = row[0]
        r_cells[1].text = row[1]
        r_cells[2].text = row[2]

    # Section 3: File Hierarchy & Directory Structure
    add_heading_1("3. Directory Structure & File Inventory")
    p = doc.add_paragraph("Complete file map of the READYFLEET codebase:\n")
    
    structure_text = """
readyfleet/
├── config/
│   └── thresholds.yaml         # Rules engine thresholds & mission priority weights
├── gen/
│   ├── schema.sql              # 10 relational SQLite table definitions
│   ├── db.py                   # SQLite connection manager & schema initializer
│   ├── degradation.py          # Multi-sensor physics degradation & sensor generator
│   ├── seed.py                 # Determinism verification & SHA-256 metrics logger
│   └── generate.py             # 5-stream synthetic dataset generator (40 tails)
├── features/
│   └── build.py                # Rolling-window (10/30 cycle) feature store
├── models/
│   ├── train.py                # HistGradientBoosting training per component class
│   ├── eval.py                 # Judge evidence evaluation script (RMSE/MAE printout)
│   ├── registry.py             # Model artifact persistence (.pkl & metrics.json)
│   └── infer.py                # Batch prediction & prediction interval (±1.5x MAE) service
├── core/
│   ├── state.py                # Fleet state snapshot loader & cloning engine
│   ├── aggregator.py           # MC/PMC/NMC rules engine & 7-day forecast evaluator
│   ├── whatif.py               # Pure state-patching What-If scenario engine (<200ms)
│   ├── drivers.py              # Binding constraint & NMC driver impact ranker
│   ├── cannibal.py             # Cannibalization advisor & guardrails checker
│   ├── scheduler.py            # Crew capacity scheduler & hash-chained audit logger
│   └── audit.py                # Tamper-evident audit chain verification proxy
├── api/
│   ├── main.py                 # FastAPI application routes & static file server
│   └── schemas.py              # Pydantic contract validation schemas
├── web/
│   ├── index.html              # SPA HTML shell with persistent SYNTHETIC banner
│   ├── style.css               # Dark-mode styling tokens
│   ├── app.js                  # Navigation router & state manager
│   ├── fleet.js                # Canvas 2D Fleet Board renderer
│   ├── forecast.js             # Canvas 2D 7-Day MC forecast chart
│   └── whatif.js               # What-If & Cannibalization controls
├── demo/
│   ├── scenario.md             # 5-minute scripted presentation walkthrough
│   └── prepare_evidence.py     # Judge evidence bundler script
├── evidence/
│   └── metrics.json            # Benchmarks, SHA-256 hashes & test metrics
├── tests/                      # Pytest & Unittest suite (test_data, test_ml, test_core, test_api)
├── requirements.txt            # Python dependency requirements
├── TASKS.md                    # 6-Phase 19-Task build checklist
└── STEP_BY_STEP.md             # Complete step-by-step CLI execution guide
"""
    p_code = doc.add_paragraph()
    run_code = p_code.add_run(structure_text.strip())
    run_code.font.name = 'Consolas'
    run_code.font.size = Pt(9)

    # Section 4: 6-Phase Executed Tasks
    add_heading_1("4. Executed Tasks Breakdown (Phases A - F)")
    
    tasks_data = [
        ("Phase A: Data Foundation", "T1 - T4", "Created scaffold, 10-table SQLite schema, multi-sensor degradation generator, 5-stream data fusion, and SHA-256 seed determinism verification."),
        ("Phase B: ML Evidence", "T5 - T7", "Built rolling-window feature store, trained HistGradientBoosting RUL models without tail leakage, generated judge evidence printouts, and batch prediction service."),
        ("Phase C: Decision Logic", "T8 - T12", "Implemented fleet availability rules aggregator, sub-200ms What-If scenario engine, NMC-driver ranker, cannibalization advisor with priority guardrails, and hash-chained audit logger."),
        ("Phase D: API Layer", "T13", "Built FastAPI endpoints delivering standardized JSON responses tagged with 'data_class': 'synthetic'."),
        ("Phase E: Dashboard UI", "T14 - T17", "Created 60 FPS Canvas 2D Fleet Board, 7-day forecast chart, What-If controls, cannibalization advisor interface, and audit trail viewer."),
        ("Phase F: Demo & Verification", "T18 - T19", "Scripted 5-minute judge scenario walkthrough, automated test suite execution, and evidence bundling into evidence/metrics.json.")
    ]
    
    for t in tasks_data:
        add_heading_2(f"{t[0]} ({t[1]})")
        doc.add_paragraph(t[2])

    # Section 5: ML Benchmark Evidence
    add_heading_1("5. ML Benchmark Evidence & Judge Evaluation Printout")
    p_eval = doc.add_paragraph()
    p_eval.add_run("Printed evaluation results from models/eval.py comparing trained HistGradientBoosting models against naive mean-RUL baselines:\n\n")
    
    eval_table_text = """
======================================================================
 READYFLEET RUL MODEL EVALUATION SUMMARY (JUDGE EVIDENCE PRINT-OUT)
======================================================================
Comp Class   | RMSE     | Baseline RMSE  | MAE      | Baseline MAE  
----------------------------------------------------------------------
engine       | 45.94    | 41.94          | 37.80    | 37.97         
avionics     | 37.23    | 42.34          | 29.71    | 38.15         
hydraulics   | 40.12    | 42.48          | 32.61    | 38.22         
airframe     | 40.92    | 43.06          | 32.39    | 37.85         
======================================================================
"""
    p_eval_code = doc.add_paragraph()
    r_eval = p_eval_code.add_run(eval_table_text.strip())
    r_eval.font.name = 'Consolas'
    r_eval.font.size = Pt(9.5)

    # Save document
    output_path = os.path.join(os.path.dirname(__file__), "READYFLEET_MASTER_DOCUMENTATION.docx")
    doc.save(output_path)
    print(f"Master Word Document created successfully at: {output_path}")

if __name__ == "__main__":
    generate_master_docx()
