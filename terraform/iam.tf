resource "google_service_account" "cf_request" {
  account_id = "cf-request-${random_string.suffix.id}"
}

resource "google_service_account" "cf_process" {
  account_id = "cf-process-${random_string.suffix.id}"
}

resource "google_service_account" "cf_callback" {
  account_id = "cf-callback-${random_string.suffix.id}"
}

resource "google_service_account" "cf_cron" {
  account_id = "cf-cron-${random_string.suffix.id}"
}

resource "google_service_account" "workflow" {
  account_id = "wf-${random_string.suffix.id}"
}

resource "google_service_account" "apigw" {
  account_id = "apigw-${random_string.suffix.id}"
}

# Allow request function access to the workflow services
resource "google_project_iam_member" "cf_request_roles" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.cf_request.email}"
}

# Allow process function access to the workflows, VertexAI & Secrets Manager services
resource "google_project_iam_member" "cf_process_roles" {
  for_each = toset(var.cf_process_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cf_process.email}"
}

# Allow callback function access to the Secrets Manager services
resource "google_project_iam_member" "cf_callback_roles" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cf_callback.email}"
}

# Allow process function access to the VertexAI & Secrets Manager services
resource "google_project_iam_member" "cf_cron_roles" {
  for_each = toset(var.cf_cron_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cf_cron.email}"
}
