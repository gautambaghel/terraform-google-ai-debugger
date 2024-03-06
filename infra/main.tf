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


variable "organization_name" {
  description = "The name of the Terraform Cloud organization"
  type        = string
}

variable "workspace_name" {
  description = "The name of the workspace to create the notification configuration for"
  type        = string
}

variable "webhook_url" {
  description = "value of the webhook url to be used for the notification configuration"
  type        = string
  default     = "https://quiet-rain-8138.tines.com/webhook/e5b841692c521d72f1de3cf372af7908/ba869f5671b2bb488cc12c57a97f0627"
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
