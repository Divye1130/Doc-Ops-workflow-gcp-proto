from pathlib import Path
import json, random
random.seed(42)
out=Path("data/input/documents.jsonl"); out.parent.mkdir(parents=True,exist_ok=True)
rows=[]
for i in range(240):
    kind=random.choice(["invoice","invoice","purchase_order","contract"])
    supplier=f"Supplier {random.randint(1,35):02d}"
    amount=round(random.uniform(250,150000),2)
    date=f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    if kind=="invoice": text=f"Invoice\nSupplier: {supplier}\nInvoice Number: INV-{i:05d}\nDate: {date}\nTotal GBP {amount:,.2f}"
    elif kind=="purchase_order": text=f"Purchase Order\nSupplier: {supplier}\nPO Number: PO-{i:05d}\nDate: {date}\nTotal GBP {amount:,.2f}"
    else: text=f"Commercial Agreement\nSupplier: {supplier}\nEffective Date: {date}\nContract Value GBP {amount:,.2f}"
    rows.append({"document_id":f"DOC-{i:05d}","text":text,"source_system":"synthetic_fixture"})
# Controlled failures
rows += [
 {"document_id":"BAD-001","text":"Unrecognised note with no structured fields","source_system":"synthetic_fixture"},
 {"document_id":"BAD-002","text":"Invoice\nInvoice Number: INV-BAD\nDate: 2026-02-01\nTotal GBP 1000.00","source_system":"synthetic_fixture"},
]
out.write_text("\n".join(json.dumps(r) for r in rows),encoding="utf-8")
print(f"wrote {len(rows)} documents")
