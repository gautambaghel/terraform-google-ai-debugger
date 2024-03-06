variable "organization_name" {
  description = "The name of the Terraform Cloud organization"
  type        = string
  default     = "ai-debugging"
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
