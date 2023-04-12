terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
}

resource "google_storage_bucket" "data-lake-bucket" {
  name          = "lalala" # Concatenating DL bucket & Project name for unique naming
  location      = "EU"

  # Optional, but recommended settings:
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}