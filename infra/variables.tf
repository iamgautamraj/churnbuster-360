variable "project_id" {
  description = "Your GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "bucket_name_prefix" {
  description = "Prefix for bucket names to ensure uniqueness (e.g., churn-johndoe)"
  type        = string
}