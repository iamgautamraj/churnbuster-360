terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- 1. DATA LAKE BUCKETS (Medallion Architecture) ---

# Bronze: Raw Data (Auto-delete after 30 days to save money)
resource "google_storage_bucket" "bronze" {
  name          = "${var.bucket_name_prefix}-bronze"
  location      = var.region
  force_destroy = true # Allows deleting bucket even if it has files (Clean up easy)

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Silver: Processed Data (Parquet)
resource "google_storage_bucket" "silver" {
  name          = "${var.bucket_name_prefix}-silver"
  location      = var.region
  force_destroy = true
}

# Gold: We don't need a bucket for Gold, we use BigQuery!

# --- 2. DATA WAREHOUSE (BigQuery) ---

resource "google_bigquery_dataset" "churn_dataset" {
  dataset_id                 = "churn_data"
  friendly_name              = "Churn Prediction Data"
  description                = "Contains raw, staging, and final tables for ChurnBuster"
  location                   = var.region
  delete_contents_on_destroy = true
}

# Output the bucket names so we can use them in Python later
output "bronze_bucket" {
  value = google_storage_bucket.bronze.name
}