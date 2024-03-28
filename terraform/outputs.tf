output "callback_uri" {
  description = "Callback cloud function uri"
  value       = google_cloudfunctions2_function.callback.url
}

output "process_uri" {
  description = "Process cloud function uri"
  value       = google_cloudfunctions2_function.process.url
}

output "request_uri" {
  description = "Request cloud function uri"
  value       = google_cloudfunctions2_function.request.url
}

output "cloud_functions_bucket" {
  description = "Cloud functions cloud storage bucket"
  value       = google_storage_bucket.cloud_functions.id
}

output "api_gateway_endpoint_uri" {
  description = "API Gateway notification endpoint URI"
  value       = "https://${google_api_gateway_gateway.tfc_notifications.default_hostname}"
}
