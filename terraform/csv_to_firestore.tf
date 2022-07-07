data "archive_file" "gcs_to_firestore" {
  type = "zip"
  source_dir = "./../python"
  output_path = "./../dist/function-source.zip"
  excludes = [
    "./../python/.gcloudignore",
    "./../python/.main_test.py",
    "./../python/.mock_test.py",
    "./../python/filetest[collection=test][key=product_id].csv"
  ]
}

resource "google_project_iam_binding" "object_viewer" {
  project = var.gcp_project
  role    = "roles/storage.admin"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}

resource "google_project_iam_binding" "firestore_user" {
  project = var.gcp_project
  role    = "roles/datastore.user"
  members = [ "serviceAccount:${google_service_account.csv_to_firestore.email}" ]
}

resource "google_storage_bucket" "bq_export" {
  name          = var.gcs_export_bucket
  location      = var.gcp_bucket_location
  force_destroy = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }

}

resource "google_storage_bucket" "cf_upload_bucket" {
  name     = var.gcs_cf_upload
  location = var.gcp_bucket_location
  uniform_bucket_level_access = true
  force_destroy = true
  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_object" "cf_upload_object" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.cf_upload_bucket.name
  source = "./../dist/function-source.zip"
  depends_on = [
    data.archive_file.gcs_to_firestore
  ]
}

resource "google_cloudfunctions_function" "csv_to_firestore" {
  name = "csv-to-firestore"
  region = var.gcp_region_cloud_function
  description = "Cloud Function to import CSV files from GCS to Firestore"
  runtime     = "python39"
  service_account_email = google_service_account.csv_to_firestore.email

  available_memory_mb   = 1024
  source_archive_bucket = google_storage_bucket.cf_upload_bucket.name
  source_archive_object = google_storage_bucket_object.cf_upload_object.name
  timeout               = 540
  entry_point           = "cs_to_firestore_trigger"
  environment_variables = {
    UPLOAD_HISTORY = true
    EXCLUDE_DOCUMENT_ID_VALUE = true
  }

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource = var.gcs_export_bucket
  }

  depends_on = [
    google_storage_bucket_object.cf_upload_object
  ]
}