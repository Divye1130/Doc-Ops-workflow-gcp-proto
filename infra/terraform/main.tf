terraform {
  required_version = ">= 1.6.0"
  required_providers { google = { source = "hashicorp/google" version = "~> 6.0" } }
}
provider "google" { project = var.project_id region = var.region }
locals { services = toset(["run.googleapis.com","aiplatform.googleapis.com","documentai.googleapis.com","bigquery.googleapis.com","apigee.googleapis.com","artifactregistry.googleapis.com"]) }
resource "google_project_service" "apis" { for_each = local.services service = each.value disable_on_destroy = false }
resource "google_service_account" "runtime" { account_id = "docops-runtime" display_name = "Doc Ops runtime" }
resource "google_bigquery_dataset" "ops" { dataset_id = "docops_ops" location = "EU" }
resource "google_artifact_registry_repository" "repo" { location = var.region repository_id = "docops" format = "DOCKER" }
resource "google_cloud_run_v2_service" "api" {
  name = "docops-service"; location = var.region
  template {
    service_account = google_service_account.runtime.email
    containers { image = "${var.region}-docker.pkg.dev/${var.project_id}/docops/app:latest" }
  }
  depends_on = [google_project_service.apis]
}
