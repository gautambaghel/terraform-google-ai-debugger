data "archive_file" "request" {
  type        = "zip"
  source_dir  = "../cloud_functions/request"
  output_path = "../build/request.zip"

  excludes = ["__pycache__", "testing", "Makefile"]
}

resource "google_storage_bucket_object" "request" {
  name   = "request_${random_string.suffix.id}_${data.archive_file.request.output_md5}.zip"
  bucket = google_storage_bucket.cloud_functions.name
  source = data.archive_file.request.output_path
}

resource "google_cloudfunctions2_function" "request" {
  name        = "request-${random_string.suffix.id}"
  description = "request handler"
  location    = var.region

  build_config {
    runtime     = "python311"
    entry_point = "request_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.cloud_functions.name
        object = google_storage_bucket_object.request.name
      }
    }
  }

  service_config {
    available_cpu    = "1"
    available_memory = "192Mi"
    environment_variables = {
      TFC_API_KEY           = var.tfc_api_key
      HMAC_KEY              = var.hmac_key
      GOOGLE_PROJECT        = var.project_id
      GOOGLE_REGION         = var.region
      NOTIFICATION_WORKFLOW = google_workflows_workflow.notification_workflow.name
    }
    ingress_settings                 = "ALLOW_ALL"
    max_instance_count               = 1
    max_instance_request_concurrency = 10
    service_account_email            = google_service_account.cf_notification.email
    timeout_seconds                  = 30
  }
}

# IAM entry for apigw to invoke the function
resource "google_cloudfunctions2_function_iam_member" "request_invoker" {
  project        = google_cloudfunctions2_function.request.project
  location       = google_cloudfunctions2_function.request.location
  cloud_function = google_cloudfunctions2_function.request.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_service_account.apigw.email}"
}

resource "google_cloud_run_service_iam_member" "request_cloud_run_invoker" {
  project  = google_cloudfunctions2_function.request.project
  location = google_cloudfunctions2_function.request.location
  service  = google_cloudfunctions2_function.request.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.apigw.email}"
}

check "cloudfunction_request_health" {
  data "http" "cloudfunction_request" {
    url = google_cloudfunctions2_function.request.url
  }
  assert {
    condition     = data.http.cloudfunction_request.status_code == 403
    error_message = format("Cloud function request unhealthy: %s - %s", data.http.cloudfunction_request.status_code, data.http.cloudfunction_request.response_body)
  }
}
