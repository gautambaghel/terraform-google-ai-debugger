resource "google_api_gateway_api" "tfc_notifications" {
  provider = google-beta

  api_id       = "apigw-${random_string.suffix.id}"
  display_name = "Terraform Cloud Notifications ${random_string.suffix.id}"
}

resource "google_api_gateway_api_config" "tfc_notifications" {
  provider      = google-beta
  api           = google_api_gateway_api.tfc_notifications.api_id
  api_config_id = "apigw-config-${random_string.suffix.id}"

  gateway_config {
    backend_config {
      google_service_account = google_service_account.apigw.email
    }
  }

  openapi_documents {
    document {
      path     = "spec.yaml"
      contents = base64encode(templatefile("${path.module}/files/openapi.yaml", { "request_url" = google_cloudfunctions2_function.request.url }))
    }
  }
  lifecycle {
    create_before_destroy = false
  }
}

resource "google_api_gateway_gateway" "tfc_notifications" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.tfc_notifications.id
  gateway_id = google_api_gateway_api.tfc_notifications.api_id
  region     = var.gw_region
}
