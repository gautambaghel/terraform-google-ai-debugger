data "archive_file" "callback" {
  type        = "zip"
  source_dir  = "../cloud_functions/callback"
  output_path = "../build/callback.zip"

  excludes = ["__pycache__", "testing", "Makefile"]
}

resource "google_storage_bucket_object" "callback" {
  name   = "callback_${random_string.suffix.id}_${data.archive_file.callback.output_md5}.zip"
  bucket = google_storage_bucket.cloud_functions.name
  source = data.archive_file.callback.output_path
}

resource "google_cloudfunctions2_function" "callback" {
  name        = "callback-${random_string.suffix.id}"
  description = "callback handler"
  location    = var.region

  build_config {
    runtime     = "python311"
    entry_point = "callback_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.cloud_functions.name
        object = google_storage_bucket_object.callback.name
      }
    }
  }

  service_config {
    available_cpu                    = "1"
    available_memory                 = "192Mi"
    ingress_settings                 = "ALLOW_ALL"
    max_instance_count               = 1
    max_instance_request_concurrency = 10
    timeout_seconds                  = 30
    service_account_email            = google_service_account.cf_callback.email
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions2_function_iam_member" "callback_invoker" {
  project        = google_cloudfunctions2_function.callback.project
  location       = google_cloudfunctions2_function.callback.location
  cloud_function = google_cloudfunctions2_function.callback.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_cloud_run_service_iam_member" "callback_cloud_run_invoker" {
  project  = google_cloudfunctions2_function.callback.project
  location = google_cloudfunctions2_function.callback.location
  service  = google_cloudfunctions2_function.callback.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.workflow.email}"
}

check "cloudfunction_callback_health" {
  data "http" "cloudfunction_callback" {
    url = google_cloudfunctions2_function.callback.url
  }
  assert {
    condition     = data.http.cloudfunction_callback.status_code == 403
    error_message = format("Cloud function request unhealthy: %s - %s", data.http.cloudfunction_callback.status_code, data.http.cloudfunction_callback.response_body)
  }
}
