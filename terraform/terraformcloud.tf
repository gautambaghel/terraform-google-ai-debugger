data "tfe_organization" "org" {
  name = var.terraform_org_name
}

data "tfe_workspace" "workspace" {
  for_each     = toset(var.terraform_workspace_names)
  organization = data.tfe_organization.org.name
  name         = each.value
}

locals {
  workspace_ids = [for name in var.terraform_workspace_names : data.tfe_workspace.workspace[name].id]
}

resource "tfe_notification_configuration" "test" {
  for_each         = toset(local.workspace_ids)
  name             = "ai-debugging-webhook"
  enabled          = true
  destination_type = "generic"
  triggers         = ["run:errored"]
  url              = "https://${google_api_gateway_gateway.tfc_notifications.default_hostname}"
  token            = var.hmac_key
  workspace_id     = each.value
}
