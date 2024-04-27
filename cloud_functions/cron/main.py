import json
import os
import ast
import time
import logging
import requests
import functions_framework
import google.cloud.logging
import google.cloud.secretmanager_v1
from datetime import datetime

import google_genai
import terraform_cloud

# Setup google cloud logging and ignore errors
if "DISABLE_GOOGLE_LOGGING" not in os.environ:
    try:
        client = google.cloud.logging.Client()
        client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        pass

if "LOG_LEVEL" in os.environ:
    logging.getLogger().setLevel(os.environ["LOG_LEVEL"])
    logging.info("LOG_LEVEL set to %s" % logging.getLogger().getEffectiveLevel())

try:
    if "CRON_CONFIG" in os.environ:
        CRON_CONFIG = json.loads(os.environ["CRON_CONFIG"])
        time_limit_for_chat = CRON_CONFIG["time_limit_for_chat"]
        comments_api_ping_interval = CRON_CONFIG["comments_api_ping_interval"]
    else:
        time_limit_for_chat = 600
        comments_api_ping_interval = 5
except Exception as e:
    time_limit_for_chat = 600
    comments_api_ping_interval = 5


@functions_framework.http
def cron_handler(request):
    try:
        logging.info("headers: " + str(request.headers))
        logging.info("payload: " + str(request.get_data()))

        headers = request.headers
        payload = request.get_json(silent=True)["result"]["message"]

        if payload:
            # Validate request
            request_valid, message = validate_request(payload)

            if request_valid:
                # Get Terraform API key from Secret Manager
                tfc_api_key, secrets_mgr_error_msg = (
                    terraform_cloud.get_terraform_cloud_key(
                        payload["tfc_api_secret_name"]
                    )
                )

                if secrets_mgr_error_msg or not tfc_api_key:
                    return send_cloud_funtion_response(
                        secrets_mgr_error_msg, 422, "error"
                    )

                logging.info(
                    "Secrets manager: successfully retrieved Terraform Cloud API key"
                )

                # Get plan/apply error to initiate the chat
                run_id = payload["run_id"]
                run_error = terraform_cloud.get_run_error(
                    tfc_api_key=tfc_api_key, run_id=run_id
                )
                if not run_error:
                    send_cloud_funtion_response(
                        message="No plan/apply error found in the Terraform Cloud run",
                        code=422,
                        type="error",
                    )

                genAI = google_genai.GoogleGenAI()
                genAI.chat.send_message(
                    f"""Can you help with this Terraform error, please? {run_error}""",
                    stream=False,
                )

                run_timed_api_calls(
                    run_id,
                    tfc_api_key,
                    genAI,
                    time_limit_for_chat,
                    comments_api_ping_interval,
                )

                # Send final comment back to Terraform Cloud
                comment_response_json, comment_error_msg = (
                    terraform_cloud.attach_comment(
                        ":sparkles: Terraform AI debugger (powered by Google Gemini) :sparkles: \n\n AI chat time limit reached. Please create a new run to initiate a new chat!",
                        tfc_api_key,
                        run_id,
                    )
                )

                if comment_error_msg:
                    return send_cloud_funtion_response(comment_error_msg, 422, "error")

                logging.info("Successfully created a comment in Terraform Cloud.")
                return send_cloud_funtion_response("Cron completed!", 200, "info")
            else:
                return send_cloud_funtion_response(message, 422, "error")
        else:
            return send_cloud_funtion_response(
                "Payload missing in request", 422, "error"
            )

    except Exception as e:
        logging.exception("Terraform AI debugger cron error: {}".format(e))
        return send_cloud_funtion_response(
            "Internal Terraform AI debugger cron error occurred", 500, "error"
        )


# Keeps checking the comments API for new comments for 'X' minutes with 'Y' seconds interval
# This needs to be done because the chat API array is not sorted based on the time of the comment
def run_timed_api_calls(
    run_id: str, tfc_api_key: str, genAI, duration_seconds: int, interval_seconds: int
):

    start_time = time.time()
    end_time = start_time + duration_seconds

    while time.time() < end_time:
        processed_data, err = terraform_cloud.ping_comments_api(run_id, tfc_api_key)
        if not err and processed_data:

            comments = processed_data.get("data")
            debug_count = count_comment_occurrences(comments, "/debug")
            ai_response_count = count_comment_occurrences(comments, ":sparkles:")

            if debug_count >= ai_response_count:
                # Send response back to Terraform Cloud as a comment
                comment_response_json, comment_error_msg = (
                    terraform_cloud.attach_comment(
                        comment="Processing your request...",
                        tfc_api_key=tfc_api_key,
                        run_id=run_id,
                    )
                )

                question = find_the_latest_debug_comment(
                    comments, tfc_api_key=tfc_api_key
                )
                if question:
                    # Send GenAI engine the request to process
                    content = genAI.chat.send_message(
                        question.replace("/debug", ""), stream=False
                    )

                    # Send response back to Terraform Cloud as a comment
                    comment_response_json, comment_error_msg = (
                        terraform_cloud.attach_comment(
                            comment=f":sparkles: Terraform AI debugger (powered by Google Gemini) :sparkles: \n\n{content.text}",
                            tfc_api_key=tfc_api_key,
                            run_id=run_id,
                        )
                    )

        time_remaining = end_time - time.time()
        if time_remaining > interval_seconds:
            time.sleep(abs(interval_seconds))
        else:
            time.sleep(abs(time_remaining))


def count_comment_occurrences(comments, word):
    return sum(
        1
        for comment in comments
        if word.lower() in comment.get("attributes", {}).get("body", "").lower()
    )


def find_the_latest_debug_comment(comments, tfc_api_key: str) -> str:
    latest_comment = None
    latest_comment_re_id = None
    for comment in comments:
        body = comment["attributes"]["body"]
        if body.startswith("/debug"):
            current_re_id = comment["relationships"]["run-event"]["data"]["id"]

            # If the latest_comment is None, set the latest_comment to the first comment with debug
            # else compare the time of the current comment with the latest_comment
            if latest_comment is None or current_comment_sooner(
                current_re_id, latest_comment_re_id, tfc_api_key=tfc_api_key
            ):
                latest_comment = body
                latest_comment_re_id = current_re_id

    return latest_comment


def current_comment_sooner(
    current_re_id: str, latest_comment_re_id: str, tfc_api_key: str
) -> bool:
    current_comment = terraform_cloud.get_comment_time(
        run_event_id=current_re_id, tfc_api_key=tfc_api_key
    )
    latest_comment = terraform_cloud.get_comment_time(
        run_event_id=latest_comment_re_id, tfc_api_key=tfc_api_key
    )

    datetime_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    current_comment_time = datetime.strptime(current_comment, datetime_format)
    latest_comment_time = datetime.strptime(latest_comment, datetime_format)

    return current_comment_time > latest_comment_time


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

    if not payload.get("run_id"):
        message = "run_id missing in request"
        return False, message

    return True, None
