# FinOps instrumentation

The local demo calculates an illustrative per-document cost made up of extraction, AI classification and compute components. It is intentionally **not a Google Cloud price quote**. In a live deployment, replace the estimator with Cloud Billing export data joined to service labels in BigQuery. Recommended dimensions: product, environment, request route, document type, model, region and client/team cost centre.
