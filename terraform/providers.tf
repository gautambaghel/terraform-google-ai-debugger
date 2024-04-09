provider "google-beta" {
  project = var.project_id
  region  = var.region
  alias = "impersonation"
  scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
  ]
}

provider "google" {
  project = var.project_id
  region  = var.region
  credentials = "../../keys.json"
}

# provider "tfe" {
#   # Configuration options
# }
