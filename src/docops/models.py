from pydantic import BaseModel, Field
from typing import Literal

DocumentType = Literal["invoice", "contract", "purchase_order", "unknown"]
Decision = Literal["auto_process", "human_review", "reject"]

class DocumentInput(BaseModel):
    document_id: str = Field(min_length=3)
    text: str = Field(min_length=1)
    source_system: str = "demo"

class ExtractedFields(BaseModel):
    document_id: str
    document_type: DocumentType
    supplier: str | None = None
    amount_gbp: float | None = None
    invoice_number: str | None = None
    po_number: str | None = None
    effective_date: str | None = None
    confidence: float = Field(ge=0, le=1)

class AIClassification(BaseModel):
    category: str
    priority: Literal["low", "medium", "high"]
    rationale: str
    confidence: float = Field(ge=0, le=1)

class ProcessingResult(BaseModel):
    document_id: str
    extracted: ExtractedFields
    classification: AIClassification
    decision: Decision
    validation_errors: list[str]
    estimated_cost_usd: float
    latency_ms: int
