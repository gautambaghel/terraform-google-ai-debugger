terraform {
  required_version = ">= 1.4.0"
  required_providers {
    google = {
      source = "hashicorp/google"
      # version = "~> 4.29.0"
    }
    google-beta = {
      source = "hashicorp/google-beta"
      # version = "~> 5.24.0"
    }
    # tfe = {
    #   source  = "hashicorp/tfe"
    #   # version = "~> 0.52.0"
    # }
  }
}
