# Security and responsible AI notes

- runtime service account follows least-privilege design;
- no secrets committed to the repository;
- external endpoints should be protected with IAM or API gateway policies;
- extracted fields are validated before straight-through processing;
- high-value and low-confidence cases route to human review;
- logs should avoid raw document bodies and sensitive fields;
- BigQuery retention, CMEK and regionality should follow the client's data classification;
- Vertex AI prompts/outputs should be logged with appropriate redaction and retention controls.
