import requests
import json


def get_run_error(tfc_api_key: str, run_id: str) -> str:
    """
    Get Terraform run error via API

    :param tfc_api_key: Terraform Cloud  API access token
    :param run_id: The run id to get the plan or apply error
    :return: response as dict
    """

    headers = {
        "Authorization": f"Bearer {tfc_api_key}",
        "Content-Type": "application/vnd.api+json",
    }

    url = f"https://app.terraform.io/api/v2/runs/{run_id}"
    response = requests.get(f"{url}/plan", headers=headers)
    if response.json()["data"]["attributes"]["status"] == "errored":
        logs_url = response.json()["data"]["attributes"]["log-read-url"]
        return requests.get(logs_url).text

    response = requests.get(f"{url}/apply", headers=headers)
    if response.json()["data"]["attributes"]["status"] == "errored":
        logs_url = response.json()["data"]["attributes"]["log-read-url"]
        return requests.get(logs_url).text

    return "Terraform run successfully completed!"

if __name__ == "__main__":

    tfc_api_key = ""
    run_id = ""

    run_error_response = get_run_error(tfc_api_key, run_id)
    # Convert the dictionary to JSON and pretty print it
    run_error_response_json = json.dumps(run_error_response, indent=4)
    # Print the JSON
    print(run_error_response_json)
