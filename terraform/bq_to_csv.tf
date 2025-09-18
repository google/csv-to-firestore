resource "google_project_service" "workflows" {
  service = "workflows.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_iam_binding" "workflow_invoker" {
  project = var.gcp_project
  role    = "roles/workflows.invoker"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}

resource "google_project_iam_binding" "bigquery_admin" {
  project = var.gcp_project
  role    = "roles/bigquery.admin"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}

resource "google_project_iam_binding" "object_creator" {
  project = var.gcp_project
  role    = "roles/storage.objectCreator"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}


resource "google_project_iam_binding" "cloud_scheduler" {
  project = var.gcp_project
  role    = "roles/cloudscheduler.admin"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}

resource "google_workflows_workflow" "bq_to_csv" {
  name          = "bq-to-gcs"
  region        = var.gcp_region_workflow
  description   = "BigQuery Table export to CSV"
  service_account = google_service_account.csv_to_firestore.email
  source_contents = templatefile("./workflow.tftpl", {
    gcp_project = var.gcp_project
    bq_dataset = var.bq_dataset
    bq_table = var.bq_table
    gcs_bucket = var.gcs_export_bucket
    file_name = "bq_export[database=${var.fs_database}][collection=${var.fs_collection}][key=${var.csv_key_column}].csv"
  })
}

resource "google_project_service" "cloud_scheduler_api" {
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_scheduler_job" "workflow_trigger" {
  name             = "export_bq_to_gcs"
  description      = "Export a BQ Table to Cloud Storage as CSV"
  schedule         = var.bq_export_schedule
  time_zone        = var.bq_export_schedule_timezone
  attempt_deadline = "320s"
  region = var.gcp_region_scheduler

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/projects/${var.gcp_project}/locations/${var.gcp_region_workflow}/workflows/${google_workflows_workflow.bq_to_csv.name}/executions"

    oauth_token {
      service_account_email = google_service_account.csv_to_firestore.email
    }
  }

  depends_on = [
    google_project_service.cloud_scheduler_api,
  ]
}
