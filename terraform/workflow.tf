resource "google_workflows_workflow" "notification_workflow" {
  name            = "terraform-notification-${random_string.suffix.id}"
  region          = var.region
  description     = "Terraform Cloud notification workflow"
  service_account = google_service_account.workflow.email
  source_contents = templatefile("${path.module}/files/workflow.yaml",
    {
      "callback_url" = google_cloudfunctions2_function.callback.url
      "process_url"  = google_cloudfunctions2_function.process.url
    }
  )
}

resource "google_project_iam_member" "workflows_invoker_1" {
  member  = "serviceAccount:${google_service_account.cf_notification.email}"
  project = var.project_id
  role    = "roles/workflows.invoker"
}

resource "google_project_iam_member" "workflows_invoker_2" {
  member  = "serviceAccount:${google_service_account.cf_notification_process.email}"
  project = var.project_id
  role    = "roles/workflows.invoker"
}
