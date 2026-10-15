import re
from .models import DocumentInput, ExtractedFields

_DOC_PATTERNS = {
    "invoice": re.compile(r"\binvoice\b", re.I),
    "purchase_order": re.compile(r"\b(purchase order|\bPO\b)\b", re.I),
    "contract": re.compile(r"\b(contract|agreement)\b", re.I),
}

def _money(text: str):
    m = re.search(r"(?:GBP|£)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", text, re.I)
    return float(m.group(1).replace(",", "")) if m else None

def _field(pattern: str, text: str):
    m = re.search(pattern, text, re.I)
    return m.group(1).strip() if m else None

def extract_document(doc: DocumentInput) -> ExtractedFields:
    dtype = "unknown"
    for name, pat in _DOC_PATTERNS.items():
        if pat.search(doc.text):
            dtype = name
            break
    supplier = _field(r"Supplier:\s*([^\n]+)", doc.text)
    inv = _field(r"Invoice(?: Number| No\.?):\s*([A-Z0-9-]+)", doc.text)
    po = _field(r"PO(?: Number| No\.?):\s*([A-Z0-9-]+)", doc.text)
    date = _field(r"(?:Effective Date|Date):\s*(\d{4}-\d{2}-\d{2})", doc.text)
    amount = _money(doc.text)
    present = sum(v is not None for v in [supplier, amount, inv or po, date])
    confidence = min(0.99, 0.58 + 0.095 * present + (0.03 if dtype != "unknown" else 0))
    return ExtractedFields(
        document_id=doc.document_id, document_type=dtype, supplier=supplier,
        amount_gbp=amount, invoice_number=inv, po_number=po,
        effective_date=date, confidence=round(confidence, 3)
    )
