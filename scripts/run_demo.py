from pathlib import Path
import json, sqlite3
from docops.models import DocumentInput
from docops.service import process_document

inp=Path("data/input/documents.jsonl")
if not inp.exists():
    import runpy; runpy.run_path("scripts/generate_fixture.py",run_name="__main__")
db=Path("data/output/docops.db")
if db.exists(): db.unlink()
results=[]
for line in inp.read_text(encoding="utf-8").splitlines():
    r=process_document(DocumentInput(**json.loads(line)),persist=True)
    results.append(r.model_dump())
Path("data/output/results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
summary={
 "documents":len(results),
 "auto_process":sum(r["decision"]=="auto_process" for r in results),
 "human_review":sum(r["decision"]=="human_review" for r in results),
 "reject":sum(r["decision"]=="reject" for r in results),
 "estimated_cost_usd":round(sum(r["estimated_cost_usd"] for r in results),4),
 "avg_latency_ms":round(sum(r["latency_ms"] for r in results)/len(results),2),
}
Path("data/output/summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(summary)
