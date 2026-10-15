import sqlite3, json
from pathlib import Path
from .models import ProcessingResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS document_events (
 document_id TEXT PRIMARY KEY,
 document_type TEXT NOT NULL,
 supplier TEXT,
 amount_gbp REAL,
 category TEXT NOT NULL,
 priority TEXT NOT NULL,
 decision TEXT NOT NULL,
 validation_errors TEXT NOT NULL,
 estimated_cost_usd REAL NOT NULL,
 latency_ms INTEGER NOT NULL,
 processed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def connect(path: str = "data/output/docops.db"):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.execute(SCHEMA); con.commit()
    return con

def upsert(result: ProcessingResult, path: str = "data/output/docops.db"):
    con = connect(path)
    con.execute("""INSERT OR REPLACE INTO document_events
    (document_id, document_type, supplier, amount_gbp, category, priority, decision, validation_errors, estimated_cost_usd, latency_ms)
    VALUES (?,?,?,?,?,?,?,?,?,?)""", (
        result.document_id, result.extracted.document_type, result.extracted.supplier,
        result.extracted.amount_gbp, result.classification.category, result.classification.priority,
        result.decision, json.dumps(result.validation_errors), result.estimated_cost_usd, result.latency_ms
    ))
    con.commit(); con.close()
