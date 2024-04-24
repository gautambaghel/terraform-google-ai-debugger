import logging
import os
import functions_framework
import google.cloud.logging
import google.cloud.secretmanager_v1
import google_genai
import terraform_cloud
from typing import List

# Setup google cloud logging and ignore errors if authentication fails
if "DISABLE_GOOGLE_LOGGING" not in os.environ:
    try:
        client = google.cloud.logging.Client()
        client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        pass

if "LOG_LEVEL" in os.environ:
    logging.getLogger().setLevel(os.environ["LOG_LEVEL"])
    logging.info("LOG_LEVEL set to %s" % logging.getLogger().getEffectiveLevel())

if "TFC_PROJECT_LABEL" in os.environ:
    TFC_PROJECT_LABEL = os.environ["TFC_PROJECT_LABEL"]
else:
    TFC_PROJECT_LABEL = "tfc-deploy"


@functions_framework.http
def process_handler(request):
    try:
        logging.info("headers: " + str(request.headers))
        logging.info("payload: " + str(request.get_data())) # Remove API token and log the payload

        payload = request.get_json(silent=True)
        http_message = "{}"

        # Check if payload is valid
        if payload and ("run_id" in payload and "tfc_api_secret_name" in payload):
            run_id = payload["run_id"]
            tfc_api_secret_name = payload["tfc_api_secret_name"]

            # Get Terraform API key from Secret Manager
            tfc_api_key, secrets_mgr_error_msg = get_terraform_cloud_key(tfc_api_secret_name)
            if secrets_mgr_error_msg != "" or tfc_api_key == "":
                return send_cloud_funtion_response(secrets_mgr_error_msg, 422, "error")

            logging.info("Secrets manager: successfully retrieved Terraform Cloud API key")

            # Get error from Terraform Cloud
            run_error_response = terraform_cloud.get_run_error(tfc_api_key, run_id)
            logging.info("Run error: " + str(run_error_response))

            genAI = google_genai.GoogleGenAI()
            content = genAI.generate_content(run_error_response, stream=False)

            logging.info("Gemini response: " + str(content))

            # Deliver the payload for callback Cloud Function
            callback_payload = {
                "tfc_api_secret_name": tfc_api_secret_name,
                "content": content,
                "run_id": run_id
            }

            logging.info("Delivering payload to callback Cloud Function")
            return send_cloud_funtion_response(callback_payload, 200, "info")

        else:
            return send_cloud_funtion_response("Run ID or tfc_api_secret_name missing in request", 422, "error")

    # Error occurred return message
    except Exception as e:
        logging.exception("Notification process error: {}".format(e))
        return send_cloud_funtion_response("Internal Terraform Cloud notification 'process' error occurred", 500, "error")


def send_cloud_funtion_response(message: str, code: int, type: str) -> (dict, int):
    if type == "error":
        logging.error(f"{code} - {message}")
        status = "failed"
    elif type == "info":
        status = "OK"

    return {"message": message, "status": status}, code


def get_terraform_cloud_key(tfc_api_secret_name: str) -> (str, str):
    message = ""
    tfc_api_key = ""

    try:
        client = google.cloud.secretmanager_v1.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": f"{tfc_api_secret_name}/versions/latest"})
        tfc_api_key = response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.exception("Exception: {}".format(e))
        message = "Failed to get the Terraform Cloud API key. Please check the secrets manager id and Terraform Cloud API key."

    return tfc_api_key, message
