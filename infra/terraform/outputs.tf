output "cloud_run_uri" { value = google_cloud_run_v2_service.api.uri }
output "bigquery_dataset" { value = google_bigquery_dataset.ops.dataset_id }
