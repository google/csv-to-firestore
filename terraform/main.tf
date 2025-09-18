terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project     = var.gcp_project
}

resource "google_service_account" "csv_to_firestore" {
  account_id   = "csv-to-firestore"
  display_name = "gPS CSV to Firestore Service Account"
}
