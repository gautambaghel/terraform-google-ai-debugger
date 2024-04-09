# data "tfe_organization" "org" {
#   name = var.terraform_org_name
# }

# resource "tfe_workspace" "workspace" {
#   organization = data.tfe_organization.org.name
#   name         = var.terraform_workspace_name
# }

# resource "tfe_workspace_run" "workspace_run" {
#   workspace_id    = tfe_workspace.workspace.id

#   apply {
#     manual_confirm = false
#     retry          = false
#   }

#   destroy {
#     manual_confirm = false
#     retry          = false
#     wait_for_run   = true
#   }
# }

# resource "tfe_notification_configuration" "test" {
#   name             = "ai-debugging-webhook"
#   enabled          = true
#   destination_type = "generic"
#   triggers         = ["run:errored"]
#   url              = "https://${google_api_gateway_gateway.tfc_notifications.default_hostname}"
#   workspace_id     = data.tfe_workspace.workspace.id
# }
