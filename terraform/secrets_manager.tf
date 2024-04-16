resource "google_secret_manager_secret" "terraform_key" {
  secret_id = "terraform-cloud-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "terraform_key_version" {
  secret      = google_secret_manager_secret.terraform_key.id
  secret_data = var.tfc_api_key
}
