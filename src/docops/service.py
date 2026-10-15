import time
from .models import DocumentInput, ProcessingResult
from .document_ai import extract_document
from .vertex_ai import classify
from .validation import validate
from .finops import estimate_cost
from .store import upsert

def process_document(doc: DocumentInput, persist: bool = True, db_path: str = "data/output/docops.db") -> ProcessingResult:
    start = time.perf_counter()
    extracted = extract_document(doc)
    classification = classify(extracted)
    errors = validate(extracted)
    if any(e in errors for e in ["negative_amount", "invalid_date"]):
        decision = "reject"
    elif errors or classification.priority == "high" or classification.confidence < 0.80:
        decision = "human_review"
    else:
        decision = "auto_process"
    latency = max(1, int((time.perf_counter() - start) * 1000))
    result = ProcessingResult(
        document_id=doc.document_id, extracted=extracted, classification=classification,
        decision=decision, validation_errors=errors,
        estimated_cost_usd=estimate_cost(len(doc.text)), latency_ms=latency
    )
    if persist: upsert(result, db_path)
    return result
