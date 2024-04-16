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

            # Get TFC API key from Secret Manager
            tfc_api_key, secrets_mgr_error_msg = __get_terraform_cloud_key(tfc_api_secret_name)
            if secrets_mgr_error_msg != "" or tfc_api_key == "":
                logging.error(secrets_mgr_error_msg)
                http_message = {"message": secrets_mgr_error_msg, "status": "failed"}
                http_code = 422
                return http_message, http_code
            else:
                logging.info("Secrets manager: successfully retrieved TFC API key")

            # Get error from Terraform Cloud
            run_error_response, run_error_json_msg = __get_run_error(tfc_api_key, run_id)
            logging.info("Run error: " + str(run_error_response))

            proj = google_genai.GoogleProject()
            content = proj.generate_content(run_error_response, stream=False)

            logging.info("Gemini response: " + str(content))

            # Create a comment in Terraform Cloud
            comment_response_json, comment_json_msg = __attach_comment(content, tfc_api_key, run_id)

            http_message = {"message": comment_response_json, "status": "ok"}
            http_code = 200

        else:
            run_message = "Run id missing in request"
            run_status = "failed"
            http_message = {"message": run_message, "status": run_status}
            http_code = 422
            logging.warning(payload)

        logging.info(f"{http_code} - {http_message}")

        return http_message, http_code
    # Error occurred return message
    except Exception as e:
        logging.exception("Notification process error: {}".format(e))
        http_message = "Internal Terraform Cloud notification 'process' error occurred"
        http_code = 500
        logging.warning(f"{http_code} - {http_message}: {e}")

        return http_message, http_code


def __get_terraform_cloud_key(tfc_api_secret_name: str) -> (str, str):
    message = ""
    tfc_api_key = ""

    try:
        client = google.cloud.secretmanager_v1.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": f"{tfc_api_secret_name}/versions/latest"})
        tfc_api_key = response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.warning("Warning: {}".format(e))
        message = "Failed to get the Terraform Cloud API key. Please check the secrets manager id and TFC API key."

    return tfc_api_key, message

def __get_run_error(tfc_api_key: str, run_id: str) -> (dict, str):
    message = ""
    run_error_response = ""

    try:
        run_error_response = terraform_cloud.get_run_error(tfc_api_key, run_id)
    except Exception as e:
        logging.warning("Warning: {}".format(e))
        message = "Failed to get error from the run in Terraform Cloud. Please check the Run id and TFC API key."

    return run_error_response, message

def __attach_comment(comment: str, tfc_api_key: str, run_id: str) -> (dict, str):
    message = ""
    comment_response_json = {}

    try:
        comment_response_json = terraform_cloud.attach_comment(comment, tfc_api_key, run_id)
    except Exception as e:
        logging.warning("Warning: {}".format(e))
        message = "Failed to create comment in Terraform Cloud. Please check the Run id and TFC API key."

    return comment_response_json, message
