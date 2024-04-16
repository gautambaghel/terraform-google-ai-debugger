<!-- BEGIN_TF_DOCS -->
# terraform-google-ai-debugger

## Overview

Deploys Google Cloud resources for the Terraform AI debugger.

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.4.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.4.2 |
| <a name="provider_google"></a> [google](#provider\_google) | 5.25.0 |
| <a name="provider_google-beta"></a> [google-beta](#provider\_google-beta) | 5.25.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.0 |
| <a name="provider_tfe"></a> [tfe](#provider\_tfe) | 0.53.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | Project id for deployment | `string` | n/a | yes |
| <a name="input_terraform_org_name"></a> [terraform\_org\_name](#input\_terraform\_org\_name) | The name of the Terraform Cloud organization | `string` | n/a | yes |
| <a name="input_terraform_workspace_names"></a> [terraform\_workspace\_names](#input\_terraform\_workspace\_names) | The array of the workspace names to create the notification configuration | `list(string)` | n/a | yes |
| <a name="input_tfc_api_key"></a> [tfc\_api\_key](#input\_tfc\_api\_key) | Terraform Cloud API key for creating comments | `string` | n/a | yes |
| <a name="input_cf_process_roles"></a> [cf\_process\_roles](#input\_cf\_process\_roles) | Roles to assign to the process cloud function | `list(string)` | <pre>[<br>  "roles/aiplatform.user",<br>  "roles/secretmanager.secretAccessor"<br>]</pre> | no |
| <a name="input_gw_region"></a> [gw\_region](#input\_gw\_region) | Region for gateway deployment | `string` | `"us-west2"` | no |
| <a name="input_hmac_key"></a> [hmac\_key](#input\_hmac\_key) | HMAC key for signing requests | `string` | `"secret"` | no |
| <a name="input_region"></a> [region](#input\_region) | Region for deployment | `string` | `"us-west1"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_api_gateway_endpoint_uri"></a> [api\_gateway\_endpoint\_uri](#output\_api\_gateway\_endpoint\_uri) | API Gateway notification endpoint URI |
| <a name="output_callback_uri"></a> [callback\_uri](#output\_callback\_uri) | Callback cloud function uri |
| <a name="output_cloud_functions_bucket"></a> [cloud\_functions\_bucket](#output\_cloud\_functions\_bucket) | Cloud functions cloud storage bucket |
| <a name="output_process_uri"></a> [process\_uri](#output\_process\_uri) | Process cloud function uri |
| <a name="output_request_uri"></a> [request\_uri](#output\_request\_uri) | Request cloud function uri |
<!-- END_TF_DOCS -->