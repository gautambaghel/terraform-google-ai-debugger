import requests
import json
import google.cloud.secretmanager_v1


def get_terraform_cloud_key(tfc_api_secret_name: str) -> (str, str):
    """
    Get the Terraform Cloud API key from the secrets manager.

    Args:
        tfc_api_secret_name (str): The name of the secret in the secrets manager.

    Returns:
        tuple: A tuple containing the Terraform Cloud API key and a message indicating success or failure.
    """
    message = ""
    tfc_api_key = ""

    try:
        client = google.cloud.secretmanager_v1.SecretManagerServiceClient()
        response = client.access_secret_version(
            request={"name": f"{tfc_api_secret_name}/versions/latest"}
        )
        tfc_api_key = response.payload.data.decode("UTF-8")

    except Exception as e:
        message = f"Failed to get the Terraform Cloud API key. Please check the secrets manager id and Terraform API key. {e}"

    return tfc_api_key, message


def attach_comment(comment: str, tfc_api_key: str, run_id: str) -> (dict, str):
    """
    Attach a comment to a Terraform Cloud run.

    Args:
        comment (str): The comment to attach.
        tfc_api_key (str): The Terraform API key.
        run_id (str): The ID of the Terraform Cloud run.

    Returns:
        tuple: A tuple containing the comment response JSON and a message indicating success or failure.
    """
    message = ""
    comment_response_json = {}

    try:
        headers = {
            "Authorization": f"Bearer {tfc_api_key}",
            "Content-Type": "application/vnd.api+json",
        }

        data = json.dumps(
            {"data": {"attributes": {"body": f"{comment}"}, "type": "comments"}}
        )

        url = f"https://app.terraform.io/api/v2/runs/{run_id}/comments"
        response = requests.post(url, headers=headers, data=data)

        if 200 <= response.status_code < 300:
            comment_response_json = response.json()
        else:
            message = f"Failed creating comment in Terraform Cloud, status code {response.status_code}."

    except Exception as e:
        message = f"Failed to create comment in Terraform Cloud. Please check the Run id and Terraform API key. {e}"

    return comment_response_json, message


def ping_comments_api(run_id: str, tfc_api_key: str) -> (dict, str):
    """
    Ping the Terraform Cloud API to get comments for a run.

    Args:
        run_id (str): The ID of the Terraform Cloud run.
        tfc_api_key (str): The Terraform API key.

    Returns:
        tuple: A tuple containing the comment response JSON and a message indicating success or failure.
    """
    message = ""
    ping_response_json = {}

    try:
        headers = {
            "Authorization": f"Bearer {tfc_api_key}",
            "Content-Type": "application/vnd.api+json",
        }

        url = f"https://app.terraform.io/api/v2/runs/{run_id}/comments"
        response = requests.get(url, headers=headers)

        if 200 <= response.status_code < 300:
            ping_response_json = response.json()
        else:
            message = f"Failed getting comments from Terraform Cloud, status code {response.status_code}."

    except Exception as e:
        message = f"Failed pinging comments from Terraform Cloud. Please check the Run id and Terraform API key. {e}"

    return ping_response_json, message


if __name__ == "__main__":

    tfc_api_secret_name = ""
    run_id = ""

    tfc_api_key, tfc_api_key_err = get_terraform_cloud_key(tfc_api_secret_name)
    add_comment_response, add_comment_err = attach_comment(
        "hello world", tfc_api_key, run_id
    )
    add_comment_response_json = json.dumps(add_comment_response, indent=4)
    print(run_error_response_json)
