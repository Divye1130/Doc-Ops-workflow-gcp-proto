# Document Ops Workflow + GCP Prototype

I built this at home to understand a fairly common document-ops problem: pull useful fields out of invoices, POs and contracts, classify them, run a few business checks, send edge cases to review and keep enough of an audit trail to explain what happened.

The working version is local. I then added the GCP config/IaC I would use to move the same flow onto managed services.

## Working locally

- FastAPI API + health checks
- Pydantic request/response models
- field extraction + document classification
- validation, routing + manual-review rules
- SQLite audit log
- latency + rough per-request cost tracking
- Docker
- GitHub Actions + GitHub Pages dashboard
- 20 validation & workflow checks

## GCP next

I have not wired the project to live GCP services. The repo includes the plumbing for Document AI, Vertex AI, BigQuery, Cloud Run and Apigee, plus Terraform and a Cloud Run manifest so I could take the local version further without redesigning the app.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/generate_fixture.py
PYTHONPATH=src python scripts/run_demo.py
PYTHONPATH=src python scripts/build_dashboard.py
pytest -q
uvicorn docops.api:app --app-dir src --reload
```

Open `docs/index.html` for the dashboard. It uses the full local run: routing, document mix, validation hits, review queue, value/supplier views and the simple cost estimates recorded per request.

## If I moved it to GCP

1. Create the GCP project + billing.
2. Review `infra/terraform` and set project/region.
3. Build the container and push it to Artifact Registry.
4. Deploy the API to Cloud Run.
5. Swap the local extraction/classification/storage pieces for Document AI, Vertex AI + BigQuery.
6. Put IAM/Apigee in front if the API needs managed access.
7. Export billing data to BigQuery if I want real cost reporting instead of the local estimator.

## Short version

Built a document-ops workflow with FastAPI, Pydantic and SQLite to extract fields, classify docs, apply validation/routing rules and send edge cases to manual review. Added Docker/CI, a static ops dashboard, request-level cost/latency tracking and the Terraform/API pieces for a later GCP deployment.
