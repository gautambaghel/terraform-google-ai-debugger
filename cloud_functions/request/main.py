import json
import os
import functions_framework
import logging
import hmac
import hashlib

import google.cloud.logging
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1
from google.cloud.workflows.executions_v1 import Execution
from google.cloud.workflows.executions_v1.types import executions

# Setup google cloud logging and ignore errors
if "DISABLE_GOOGLE_LOGGING" not in os.environ:
    try:
        client = google.cloud.logging.Client()
        client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        pass

if "TFC_ORG" in os.environ:
    TFC_ORG = os.environ["TFC_ORG"]
else:
    TFC_ORG = False

if "WORKSPACE_PREFIX" in os.environ:
    WORKSPACE_PREFIX = os.environ["WORKSPACE_PREFIX"]
else:
    WORKSPACE_PREFIX = False

if "HMAC_KEY" in os.environ:
    HMAC_KEY = os.environ["HMAC_KEY"]
else:
    HMAC_KEY = False

if "TFC_API_SECRET_NAME" in os.environ:
    TFC_API_SECRET_NAME = os.environ["TFC_API_SECRET_NAME"]
else:
    TFC_API_SECRET_NAME = False

if "GOOGLE_PROJECT" in os.environ:
    GOOGLE_PROJECT = os.environ["GOOGLE_PROJECT"]
else:
    GOOGLE_PROJECT = False

if "GOOGLE_REGION" in os.environ:
    GOOGLE_REGION = os.environ["GOOGLE_REGION"]
else:
    GOOGLE_REGION = False

if "NOTIFICATION_WORKFLOW" in os.environ:
    NOTIFICATION_WORKFLOW = os.environ["NOTIFICATION_WORKFLOW"]
else:
    NOTIFICATION_WORKFLOW = False

if 'LOG_LEVEL' in os.environ:
    logging.getLogger().setLevel(os.environ['LOG_LEVEL'])
    logging.info("LOG_LEVEL set to %s" % logging.getLogger().getEffectiveLevel())


@functions_framework.http
def request_handler(request):
    try:
        logging.info("headers: " + str(request.headers))
        logging.info("payload: " + str(request.get_data()))

        request_headers = request.headers
        request_payload = request.get_json(silent=True)

        http_code = 422

        if not HMAC_KEY:
            http_message = "HMAC_KEY key environment variable missing on server"
            http_code = 500
            logging.error(http_message)
        elif not TFC_API_SECRET_NAME:
            http_message = "TFC_API_SECRET_NAME key environment variable missing on server"
            http_code = 500
            logging.error(http_message)
        elif not GOOGLE_PROJECT:
            http_message = "Project environment variable missing on server"
            http_code = 500
            logging.error(http_message)
        elif not GOOGLE_REGION:
            http_message = "Region environment variable missing on server"
            http_code = 500
            logging.error(http_message)
        elif not NOTIFICATION_WORKFLOW:
            http_message = "Workflow name environment variable missing on server"
            http_code = 500
            logging.error(http_message)
        elif request_payload:
            result, message = __validate_request(request_headers, request_payload)
            if result:
                # Check HMAC signature
                signature = request_headers['x-tfe-notification-signature']
                # Need to use request.get_data() for hmac digest
                if __validate_hmac(HMAC_KEY, request.get_data(), signature):
                    try:
                        request_payload["tfc_api_secret_name"] = TFC_API_SECRET_NAME
                        __execute_workflow(request_payload)
                        http_message = "OK"
                        http_code = 200
                    except Exception as e:
                        http_code = 500
                        http_message = "Workflow execution error"
                        logging.error(f"{http_code} - {http_message}: {e}")
                else:
                    http_message = "HMAC signature invalid"
                    logging.warning(message)
        else:
            http_code = 200
            http_message = "Payload missing in request"

        logging.info(f"{http_code} - {http_message}")

        return http_message, http_code

    except Exception as e:
        logging.exception("Terraform Cloud notification Request error: {}".format(e))
        http_message = "Internal notification API error occurred"
        http_code = 500
        logging.warning(f"{http_code} - {http_message}: {e}")

        return http_message, http_code


def __validate_request(headers, payload) -> (bool, str):
    """Validate request values"""

    result = True
    message = "OK"

    if headers is None:
        message = "Headers missing in request"
        logging.warning(message)
        result = False

    elif payload is None:
        message = "Payload missing in request"
        logging.warning(message)
        result = False

    elif "x-tfe-notification-signature" not in headers:
        message = "Terraform notification signature missing"
        logging.warning(message)
        result = False

    elif "organization_name" not in payload.keys():
        message = "Terraform payload missing : organization_name"
        logging.warning(message)
        result = False

    elif "workspace_name" not in payload.keys():
        message = "Terraform payload missing : workspace_name"
        logging.warning(message)
        result = False

    elif TFC_ORG and payload["organization_name"] != TFC_ORG:
        message = "Terraform Org verification failed : {}".format(payload["organization_name"])
        logging.warning(message)
        result = False

    return result, message


def __validate_hmac(key: str, payload: str, signature: str) -> bool:
    """Returns true if the x-tfe-notification-signature header matches the SHA512 digest of the payload"""

    digest = hmac.new(bytes(key, 'utf-8'), msg=payload, digestmod=hashlib.sha512).hexdigest()
    result = hmac.compare_digest(digest, signature)

    if not result:
        logging.warning(f"HMAC mismatch, digest: {digest}, signature: {signature}")

    return result


def __execute_workflow(payload: dict, project: str = GOOGLE_PROJECT, location: str = GOOGLE_REGION,
                       workflow: str = NOTIFICATION_WORKFLOW) -> Execution:
    """
    Execute a workflow and print the execution results

    :param project: The Google Cloud project id which contains the workflow to execute.
    :param location: The location for the workflow
    :param workflow: The ID of the workflow to execute.
    :return:
    """

    arguments = payload

    execution = Execution(argument=json.dumps(arguments))

    # Set up API clients.
    execution_client = executions_v1.ExecutionsClient()
    workflows_client = workflows_v1.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    logging.info(f"Created execution: {response.name}")
    execution = execution_client.get_execution(request={"name": response.name})

    return execution
