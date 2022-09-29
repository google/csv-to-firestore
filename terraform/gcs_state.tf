resource "random_id" "bucket_prefix" {
  byte_length = 8
}

resource "google_storage_bucket" "backend" {
  name          = "${random_id.bucket_prefix.hex}-bucket-tfstate"
  force_destroy = false
  location      = var.gcp_bucket_location
  storage_class = "STANDARD"
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}