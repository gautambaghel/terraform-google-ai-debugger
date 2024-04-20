import os
import sys
import json
import pytest

sys.path.insert(0, f"{os.path.dirname(__file__)}/../callback")

from unittest.mock import patch
from callback import main

@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, headers, payload):
            self.headers = headers
            self.json_payload = payload

        def get_headers(self):
            return self.headers

        def get_json(self, silent=True):
            return {"result": {"message": self.json_payload}}

        def get_data(self, silent=True):
            return {"result": {"message": self.json_payload}}

    return MockRequest


@patch("callback.main.google.cloud.secretmanager_v1.SecretManagerServiceClient")
def test_callback_handler_missing_payload(mock_secret_client, mock_request):
    headers = {"Content-Type": "application/json"}
    payload = {}
    request = mock_request(headers, payload)

    response, status_code = main.callback_handler(request)

    assert status_code == 422
    assert response["message"] == "Payload missing in request"
    assert response["status"] == "failed"


def test_validate_request():
    valid_payload = {
        "tfc_api_secret_name": "secret",
        "content": "This is a test comment",
        "run_id": "run-id",
    }

    assert main.validate_request(valid_payload) == (True, None)

    invalid_payload = {}
    assert main.validate_request(invalid_payload) == (False, "The Terraform Cloud API secret name missing in request")


@patch("callback.main.google.cloud.secretmanager_v1.SecretManagerServiceClient")
def test_get_terraform_cloud_key_success(mock_secret_client):
    mock_secret_client.return_value.access_secret_version.return_value.payload.data.decode.return_value = "my-api-key"

    api_key, message = main.get_terraform_cloud_key("my-secret-name")

    assert api_key == "my-api-key"
    assert message == ""


@patch("callback.main.google.cloud.secretmanager_v1.SecretManagerServiceClient")
def test_get_terraform_cloud_key_failure(mock_secret_client):
    mock_secret_client.return_value.access_secret_version.side_effect = Exception("Secret not found")

    api_key, message = main.get_terraform_cloud_key("my-secret-name")

    assert api_key == ""
    assert "Failed to get the Terraform Cloud API key" in message


@patch("callback.main.requests.post")
def test_attach_comment_success(mock_post):
    mock_response = mock_post.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"id": "1"}}

    comment_response, message = main.attach_comment("This is a test comment", "my-api-key", "run-id")

    assert comment_response["data"]["id"] == "1"
    assert message == ""


@patch("callback.main.requests.post")
def test_attach_comment_failure(mock_post):
    mock_response = mock_post.return_value
    mock_response.status_code = 400
    
    comment_response, message = main.attach_comment("This is a test comment", "my-api-key", "run-id")

    assert comment_response == {}
    assert "Failed creating comment in Terraform Cloud, status code 400" in message
