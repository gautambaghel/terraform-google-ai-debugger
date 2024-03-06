terraform {
  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "0.52.0"
    }
  }
}

provider "tfe" {
  # Configuration options
}

data "tfe_organization" "org" {
  name = var.organization_name
}

data "tfe_workspace" "workspace" {
  organization = data.tfe_organization.org.name
  name         = var.workspace_name
}

resource "tfe_notification_configuration" "test" {
  name             = "ai-debugging-webhook"
  enabled          = true
  destination_type = "generic"
  triggers         = ["run:errored"]
  url              = var.webhook_url
  workspace_id     = data.tfe_workspace.workspace.id
}
