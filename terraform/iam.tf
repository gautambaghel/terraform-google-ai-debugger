resource "google_service_account" "cf_notification" {
  account_id = "cf-notification-${random_string.suffix.id}"
}

resource "google_service_account" "cf_notification_process" {
  account_id = "cf-notification-process-${random_string.suffix.id}"
}

resource "google_service_account" "workflow" {
  account_id = "wf-${random_string.suffix.id}"
}

resource "google_service_account" "apigw" {
  account_id = "apigw-${random_string.suffix.id}"
}

# Allow access to the VertexAI endpoint, fine tune the role to the minimum required
resource "google_project_iam_member" "project_viewer" {
  for_each = toset(var.cf_process_roles)
  member   = "serviceAccount:${google_service_account.cf_notification_process.email}"
  project  = var.project_id
  role     = each.value
}
