from fastapi import FastAPI, HTTPException
from .models import DocumentInput, ProcessingResult
from .service import process_document

app = FastAPI(title="Document Operations API", version="0.1.0")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/ready")
def ready(): return {"status": "ready", "dependencies": {"document_ai": "offline_adapter", "vertex_ai": "offline_adapter", "bigquery": "sqlite_fallback"}}

@app.post("/v1/documents/process", response_model=ProcessingResult)
def process(doc: DocumentInput):
    try:
        return process_document(doc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="processing_failed") from exc
