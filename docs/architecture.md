# Architecture notes

Current local flow:

`client -> FastAPI -> extraction -> classification -> checks -> route -> SQLite -> dashboard`

If I move it to GCP, the same shape becomes roughly:

`client -> Apigee/IAM -> Cloud Run -> Document AI -> Vertex AI -> checks/routing -> BigQuery -> dashboard/cost reporting`

For now the extraction/classification/storage pieces are local so the whole repo runs without cloud credentials. `gcp_adapters.py`, Terraform and the Cloud Run manifest are there for the next step.
