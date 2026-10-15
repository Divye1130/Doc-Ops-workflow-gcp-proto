from datetime import date
from .models import ExtractedFields

def validate(fields: ExtractedFields) -> list[str]:
    errors = []
    if fields.document_type == "unknown": errors.append("unknown_document_type")
    if fields.supplier is None: errors.append("missing_supplier")
    if fields.amount_gbp is not None and fields.amount_gbp < 0: errors.append("negative_amount")
    if fields.document_type == "invoice" and not fields.invoice_number: errors.append("missing_invoice_number")
    if fields.document_type == "purchase_order" and not fields.po_number: errors.append("missing_po_number")
    if fields.effective_date:
        try:
            parsed = date.fromisoformat(fields.effective_date)
            if parsed.year < 2020 or parsed.year > 2035: errors.append("date_out_of_policy_range")
        except ValueError:
            errors.append("invalid_date")
    if fields.confidence < 0.80: errors.append("low_extraction_confidence")
    return errors
