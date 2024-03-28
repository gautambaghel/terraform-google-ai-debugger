resource "google_storage_bucket" "cloud_functions" {
  name     = "tf-notification-cf-${random_string.suffix.id}"
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = true
}
