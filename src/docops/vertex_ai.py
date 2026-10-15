from .models import ExtractedFields, AIClassification

def classify(fields: ExtractedFields) -> AIClassification:
    amount = fields.amount_gbp or 0.0
    if fields.document_type == "unknown":
        return AIClassification(category="unclassified", priority="high", rationale="Document type is unclear.", confidence=0.62)
    if amount >= 100_000:
        return AIClassification(category="high_value_finance", priority="high", rationale="High-value financial document requires tighter control.", confidence=0.93)
    if fields.document_type == "contract":
        return AIClassification(category="legal_commercial", priority="medium", rationale="Contract-like content should follow commercial review.", confidence=0.90)
    return AIClassification(category="standard_finance", priority="low", rationale="Routine structured finance document.", confidence=0.94)
