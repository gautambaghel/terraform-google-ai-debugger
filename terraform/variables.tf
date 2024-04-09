variable "project_id" {
  description = "Project id for deployment"
  type        = string
}

variable "region" {
  description = "Region for deployment"
  type        = string
  default     = "us-west1"
}

variable "gw_region" {
  description = "Region for gateway deployment"
  type        = string
  default     = "us-west2"
}

variable "hmac_key" {
  description = "HMAC key for signing requests"
  type        = string
  default     = "secret"
}

variable "tfc_api_key" {
  description = "Terraform Cloud API key for creating comments"
  type        = string
}

# variable "terraform_org_name" {
#   description = "The name of the Terraform Cloud organization"
#   type        = string
# }

# variable "terraform_workspace_name" {
#   description = "The name of the workspace to create the notification configuration for"
#   type        = string
# }
