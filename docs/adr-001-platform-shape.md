# ADR-001: API-first, stateless processing service

## Decision
Use a stateless FastAPI processing service with explicit adapters for extraction, AI classification and persistence.

## Why
- maps cleanly to Cloud Run autoscaling;
- keeps AI providers replaceable;
- allows deterministic offline tests;
- makes validation and human-review controls visible;
- keeps business logic independent of cloud SDKs.

## Trade-offs
Adds adapter code and does not demonstrate live GCP latency until deployed.
