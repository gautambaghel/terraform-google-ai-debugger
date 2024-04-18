data "archive_file" "process" {
  type        = "zip"
  source_dir  = "../cloud_functions/process"
  output_path = "../build/process.zip"

  excludes = ["__pycache__", "testing", "Makefile"]
}

resource "google_storage_bucket_object" "process" {
  name   = "process_${random_string.suffix.id}_${data.archive_file.process.output_md5}.zip"
  bucket = google_storage_bucket.cloud_functions.name
  source = data.archive_file.process.output_path
}

resource "google_cloudfunctions2_function" "process" {
  name        = "process-${random_string.suffix.id}"
  description = "process handler"
  location    = var.region

  build_config {
    runtime     = "python311"
    entry_point = "process_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.cloud_functions.name
        object = google_storage_bucket_object.process.name
      }
    }
  }

  service_config {
    available_cpu                    = "1"
    available_memory                 = "512Mi"
    ingress_settings                 = "ALLOW_ALL"
    max_instance_count               = 1
    max_instance_request_concurrency = 10
    timeout_seconds                  = 30
    service_account_email            = google_service_account.cf_process.email
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions2_function_iam_member" "process_invoker" {
  project        = google_cloudfunctions2_function.process.project
  location       = google_cloudfunctions2_function.process.location
  cloud_function = google_cloudfunctions2_function.process.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_cloud_run_service_iam_member" "process_cloud_run_invoker" {
  project  = google_cloudfunctions2_function.process.project
  location = google_cloudfunctions2_function.process.location
  service  = google_cloudfunctions2_function.process.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.workflow.email}"
}

check "cloudfunction_process_health" {
  data "http" "cloudfunction_process" {
    url = google_cloudfunctions2_function.process.url
  }
  assert {
    condition     = data.http.cloudfunction_process.status_code == 403
    error_message = format("Cloud function request unhealthy: %s - %s", data.http.cloudfunction_process.status_code, data.http.cloudfunction_process.response_body)
  }
}
