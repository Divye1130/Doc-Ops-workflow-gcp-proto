# Local run notes

## Run

- Docs: 242
- Auto: 164
- Manual review: 78
- Rejected: 0
- Validation/workflow checks: 20/20 passed
- Est. local cost: about $0.60

## What I checked

The local app runs end to end: FastAPI request -> extraction -> classification -> validation -> routing -> SQLite log. Docker/CI and the static dashboard are included too.

The GCP files are the next-step setup, not a live deployment. I have not connected Document AI, Vertex AI, BigQuery, Cloud Run or Apigee to a real GCP project yet.

## Things I wanted to make explicit

- missing/odd docs go to review rather than slipping through;
- high-value docs are reviewed by rule;
- negative amounts / invalid dates are hard failures;
- every result keeps a route, latency and rough cost estimate;
- the dashboard is built from the full local results file.
