resource "google_service_account" "cf_request" {
  account_id = "cf-request-${random_string.suffix.id}"
}

resource "google_service_account" "cf_process" {
  account_id = "cf-process-${random_string.suffix.id}"
}

resource "google_service_account" "cf_callback" {
  account_id = "cf-callback-${random_string.suffix.id}"
}

resource "google_service_account" "workflow" {
  account_id = "wf-${random_string.suffix.id}"
}

resource "google_service_account" "apigw" {
  account_id = "apigw-${random_string.suffix.id}"
}

# Allow access to the workflow services
resource "google_project_iam_member" "cf_request_roles" {
  project = var.project_id
  member  = "serviceAccount:${google_service_account.cf_request.email}"
  role    = "roles/workflows.invoker"
}

# Allow access to the VertexAI & Secrets Manager services
resource "google_project_iam_member" "cf_process_roles" {
  for_each = toset(var.cf_process_roles)
  project  = var.project_id
  member   = "serviceAccount:${google_service_account.cf_process.email}"
  role     = each.value
}

# Allow access to the Secrets Manager services
resource "google_project_iam_member" "cf_callback_roles" {
  project = var.project_id
  member  = "serviceAccount:${google_service_account.cf_callback.email}"
  role    = "roles/secretmanager.secretAccessor"
}
