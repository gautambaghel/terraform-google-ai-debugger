data "archive_file" "cron" {
  type        = "zip"
  source_dir  = "../cloud_functions/cron"
  output_path = "../build/cron.zip"

  excludes = ["__pycache__", "testing", "Makefile"]
}

resource "google_storage_bucket_object" "cron" {
  name   = "cron_${random_string.suffix.id}_${data.archive_file.cron.output_md5}.zip"
  bucket = google_storage_bucket.cloud_functions.name
  source = data.archive_file.cron.output_path
}

resource "google_cloudfunctions2_function" "cron" {
  name        = "cron-${random_string.suffix.id}"
  description = "cron handler"
  location    = var.region

  build_config {
    runtime     = "python311"
    entry_point = "cron_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.cloud_functions.name
        object = google_storage_bucket_object.cron.name
      }
    }
  }

  service_config {
    available_cpu                    = "1"
    available_memory                 = "512Mi"
    ingress_settings                 = "ALLOW_ALL"
    max_instance_count               = 1
    max_instance_request_concurrency = 10
    timeout_seconds                  = 90
    environment_variables = {
      CRON_CONFIG = jsonencode(var.cron_config)
    }
    service_account_email = google_service_account.cf_cron.email
  }
}

check "cloudfunction_cron_health" {
  data "http" "cloudfunction_cron" {
    url = google_cloudfunctions2_function.cron.url
  }
  assert {
    condition     = data.http.cloudfunction_cron.status_code == 403
    error_message = format("Cloud function request unhealthy: %s - %s", data.http.cloudfunction_cron.status_code, data.http.cloudfunction_cron.response_body)
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions2_function_iam_member" "cron_invoker" {
  project        = google_cloudfunctions2_function.cron.project
  location       = google_cloudfunctions2_function.cron.location
  cloud_function = google_cloudfunctions2_function.cron.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_cloud_run_service_iam_member" "cron_cloud_run_invoker" {
  project  = google_cloudfunctions2_function.cron.project
  location = google_cloudfunctions2_function.cron.location
  service  = google_cloudfunctions2_function.cron.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.workflow.email}"
}
