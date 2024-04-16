data "tfe_organization" "org" {
  name = var.terraform_org_name
}

data "tfe_workspace" "workspace" {
  organization = data.tfe_organization.org.name
  name         = var.terraform_workspace_name
}

resource "tfe_notification_configuration" "test" {
  name             = "ai-debugging-webhook"
  enabled          = true
  destination_type = "generic"
  triggers         = ["run:errored"]
  url              = "https://${google_api_gateway_gateway.tfc_notifications.default_hostname}"
  token            = var.hmac_key
  workspace_id     = data.tfe_workspace.workspace.id
}
