# Links terraform to a cloud storage backend to manage Terraform state.
# Fill in the bucket name of "resource.google_storage_bucket.backend"
# after initial apply to link.

# terraform {
#  backend "gcs" {
#    bucket  = [YOUR-BACKEND-BUCKET-NAME]
#    prefix  = "terraform/state"
#  }
# }