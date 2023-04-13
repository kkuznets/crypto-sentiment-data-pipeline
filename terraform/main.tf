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
  name                        = var.bucket_name
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = true
  versioning {
    enabled = true
  }
}

resource "google_bigquery_dataset" "dataset" {
  dataset_id                 = "crypto-market-data"
  friendly_name              = "Crypto Market Data"
  description                = "Dataset for crypto market analysis"
  location                   = "US"
  delete_contents_on_destroy = true
}
