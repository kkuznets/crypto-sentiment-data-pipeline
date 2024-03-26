variable "gcp_region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

variable "ar_repository" {
  type        = string
  description = "Artifact repository with Prefect agent images"
  default     = "prefect-images"
}

variable "bucket_name" {
  type        = string
  description = "Name of the bucket to create"
  default     = "raw-crypto-data"
}

variable "dataset_name" {
  type        = string
  description = "Name of the dataset to create"
  default     = "crypto_data"
}

variable "data_location" {
  type        = string
  description = "Location of the bucket and dataset"
  default     = "US"
}
