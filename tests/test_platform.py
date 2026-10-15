import tempfile, json
from pathlib import Path
from fastapi.testclient import TestClient
from docops.models import DocumentInput
from docops.document_ai import extract_document
from docops.vertex_ai import classify
from docops.validation import validate
from docops.service import process_document
from docops.finops import estimate_cost
from docops.api import app

def invoice(amount=1250.50):
    return DocumentInput(document_id="DOC-001", text=f"Invoice\nSupplier: Acme Ltd\nInvoice Number: INV-001\nDate: 2026-01-15\nTotal GBP {amount}")

def test_invoice_extraction():
    x=extract_document(invoice()); assert x.document_type=="invoice" and x.supplier=="Acme Ltd" and x.invoice_number=="INV-001"
def test_money_extraction(): assert extract_document(invoice()).amount_gbp==1250.50
def test_standard_classification(): assert classify(extract_document(invoice())).category=="standard_finance"
def test_high_value_classification(): assert classify(extract_document(invoice(125000))).priority=="high"
def test_valid_invoice_has_no_errors(): assert validate(extract_document(invoice()))==[]
def test_missing_supplier_routed_review():
    d=DocumentInput(document_id="DOC-002", text="Invoice\nInvoice Number: INV-2\nDate: 2026-01-01\nTotal GBP 100")
    r=process_document(d,persist=False); assert r.decision=="human_review" and "missing_supplier" in r.validation_errors
def test_unknown_routed_review():
    r=process_document(DocumentInput(document_id="DOC-003",text="General memo"),persist=False); assert r.decision=="human_review"
def test_high_value_routed_review(): assert process_document(invoice(150000),persist=False).decision=="human_review"
def test_standard_auto_process(): assert process_document(invoice(1200),persist=False).decision=="auto_process"
def test_cost_positive(): assert estimate_cost(100)>0
def test_cost_scales(): assert estimate_cost(1000)>estimate_cost(100)
def test_api_health(): assert TestClient(app).get("/health").json()["status"]=="ok"
def test_api_ready(): assert TestClient(app).get("/ready").status_code==200
def test_api_process():
    resp=TestClient(app).post("/v1/documents/process",json=invoice().model_dump()); assert resp.status_code==200 and resp.json()["decision"]=="auto_process"
def test_persistence():
    with tempfile.TemporaryDirectory() as td:
        p=str(Path(td)/"x.db"); process_document(invoice(),persist=True,db_path=p); assert Path(p).exists()
def test_contract_medium_priority():
    d=DocumentInput(document_id="DOC-004", text="Commercial Agreement\nSupplier: A\nEffective Date: 2026-01-01\nContract Value GBP 5000")
    assert process_document(d,persist=False).classification.priority=="medium"
def test_po_requires_po_number():
    d=DocumentInput(document_id="DOC-005", text="Purchase Order\nSupplier: A\nDate: 2026-01-01\nTotal GBP 1000")
    assert "missing_po_number" in process_document(d,persist=False).validation_errors
def test_model_has_audit_fields():
    r=process_document(invoice(),persist=False); assert r.estimated_cost_usd>0 and r.latency_ms>=1
def test_gcp_adapter_module_importable():
    from docops.gcp_adapters import GoogleDocumentAIConfig, VertexAIConfig, BigQueryConfig
    assert GoogleDocumentAIConfig and VertexAIConfig and BigQueryConfig
def test_readme_keeps_cloud_scope_clear():
    text=Path("README.md").read_text().lower(); assert "have not wired the project to live gcp services" in text
