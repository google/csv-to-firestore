variable "gcp_project" {
  type = string
  description = "Google Cloud Project to deploy resources on"
}

variable "gcp_bucket_location" {
  type = string
  description = "Multi-region location name to use for the Google Cloud Buckets. One of ASIA, EU, US"
}

variable "gcp_region_cloud_function" {
  type = string
  description = "GCP Region for the Cloud Function"
}

variable "gcp_region_scheduler" {
  type = string
  description = "GCP Region for the Cloud Scheduler job"
}

variable "gcp_region_workflow" {
  type = string
  description = "Google Cloud Region to deploy the workflow in"
}

variable "gcs_cf_upload" {
  type = string
  description = "Storage Bucket to deploy the Cloud Function from"
}

variable "gcs_export_bucket" {
  type = string
  description = "Storage Bucket to export BQ table to"
}

variable "fs_database" {
  type = string
  description = "Firestore database to use"
  default = "(default)"
}

variable "fs_collection" {
  type = string
  description = "Firestore collection to use"
}

variable "csv_key_column" {
  type = string
  description = "CSV column name to use as Firestore document ID"
}

variable "bq_dataset" {
  type = string
  description = "BQ Dataset where the table to export is located"
}

variable "bq_table" {
  type = string
  description = "BQ Table to export"
}

variable "bq_export_schedule" {
  type = string
  description = "Cron schedule to export the BQ table to GCS"
}

variable "bq_export_schedule_timezone" {
  type = string
  description = "Timezone for the schedule"
}