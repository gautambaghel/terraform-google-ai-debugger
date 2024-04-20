import json
import os
import functions_framework
import google.cloud.logging
import google.cloud.secretmanager_v1
import logging
import requests

# Setup google cloud logging and ignore errors
if "DISABLE_GOOGLE_LOGGING" not in os.environ:
    try:
        client = google.cloud.logging.Client()
        client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        pass

if 'LOG_LEVEL' in os.environ:
    logging.getLogger().setLevel(os.environ['LOG_LEVEL'])
    logging.info("LOG_LEVEL set to %s" % logging.getLogger().getEffectiveLevel())


@functions_framework.http
def callback_handler(request):
    try:
        logging.info("headers: " + str(request.headers))
        logging.info("payload: " + str(request.get_data()))

        headers = request.headers
        payload = request.get_json(silent=True)["result"]["message"]

        if payload:
            # Validate request
            request_valid, message = validate_request(payload)

            if request_valid:
                # Get TFC API key from Secret Manager
                tfc_api_key, secrets_mgr_error_msg = get_terraform_cloud_key(payload["tfc_api_secret_name"])

                if secrets_mgr_error_msg or not tfc_api_key:
                    return send_cloud_funtion_response(secrets_mgr_error_msg, 422, "error")

                logging.info("Secrets manager: successfully retrieved Terraform Cloud API key")

                # Send comment back to Terraform Cloud
                comment_response_json, comment_error_msg = attach_comment(payload["content"], tfc_api_key, payload["run_id"])
                if comment_error_msg:
                    return send_cloud_funtion_response(comment_error_msg, 422, "error")

                logging.info("Successfully created a comment in Terraform Cloud.")
            else:
                return send_cloud_funtion_response(message, 422, "error")
        else:
            return send_cloud_funtion_response("Payload missing in request", 422, "error")

        return send_cloud_funtion_response("Callback completed!", 200, "info")

    except Exception as e:
        logging.exception("Terraform AI debugger callback error: {}".format(e))
        return send_cloud_funtion_response("Internal Terraform AI debugger callback error occurred", 500, "error")


def send_cloud_funtion_response(message: str, code: int, type: str) -> (dict, int):
    if type == "error":
        logging.error(f"{code} - {message}")
        status = "failed"
    elif type == "info":
        logging.info(f"{code} - {message}")
        status = "OK"

    return {"message": message, "status": status}, code


def validate_request(payload: dict) -> (bool, str):
    """Validate request values"""

    if not payload.get("tfc_api_secret_name"):
        message = "The Terraform Cloud API secret name missing in request"
        return False, message

    if not payload.get("content"):
        message = "Content missing in request"
        return False, message

    if not payload.get("run_id"):
        message = "run_id missing in request"
        return False, message

    return True, None


def get_terraform_cloud_key(tfc_api_secret_name: str) -> (str, str):
    message = ""
    tfc_api_key = ""

    try:
        client = google.cloud.secretmanager_v1.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": f"{tfc_api_secret_name}/versions/latest"})
        tfc_api_key = response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.exception("Exception: {}".format(e))
        message = "Failed to get the Terraform Cloud API key. Please check the secrets manager id and TFC API key."

    return tfc_api_key, message


def attach_comment(comment: str, tfc_api_key: str, run_id: str) -> (dict, str):
    message = ""
    comment_response_json = {}

    try:
        headers = {
            "Authorization": f"Bearer {tfc_api_key}",
            "Content-Type": "application/vnd.api+json",
        }

        data = json.dumps({
            "data": {
            "attributes": {
                "body": f"{comment}"
            },
            "type": "comments"
            }
        })

        url = f"https://app.terraform.io/api/v2/runs/{run_id}/comments"
        response = requests.post(url, headers=headers, data=data)
        if 200 <= response.status_code < 300:
            comment_response_json = response.json()
        else:
            message = f"Failed creating comment in Terraform Cloud, status code {response.status_code}."

    except Exception as e:
        logging.exception("Exception: {}".format(e))
        message = "Failed to create comment in Terraform Cloud. Please check the Run id and TFC API key."

    return comment_response_json, message
