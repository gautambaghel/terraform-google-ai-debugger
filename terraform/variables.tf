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

variable "cf_process_roles" {
  description = "Roles to assign to the process cloud function"
  type        = list(string)
  default     = ["roles/aiplatform.user", "roles/secretmanager.secretAccessor", "roles/workflows.invoker"]
}

variable "terraform_org_name" {
  description = "The name of the Terraform Cloud organization"
  type        = string
}

variable "terraform_workspace_names" {
  description = "The array of the workspace names to create the notification configuration"
  type        = list(string)
}
