"""Cloud adapter interfaces.

The repository is fully verifiable offline. These adapters document the production seams for
Google Document AI, Vertex AI and BigQuery without pretending cloud calls were executed.
"""
from dataclasses import dataclass

@dataclass
class GoogleDocumentAIConfig:
    project_id: str
    location: str
    processor_id: str

@dataclass
class VertexAIConfig:
    project_id: str
    location: str
    model_name: str

@dataclass
class BigQueryConfig:
    project_id: str
    dataset: str
    table: str
