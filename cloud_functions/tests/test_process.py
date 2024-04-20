import os
import sys
import pytest
from unittest.mock import Mock
from unittest.mock import patch


sys.path.insert(0, f"{os.path.dirname(__file__)}/../process")
from process import main
from process import terraform_cloud
from process import google_genai


def test_process_handler_valid(mocker):
    mock_generate_content = mocker.patch(
        "google_genai.GoogleGenAI.generate_content", return_value="Gemini response"
    )

    class MockRequest:
        def __init__(self, model):
            self.model = model

        def generate_content(self, help_string: str, stream: bool = False) -> str:
            # Simulate generating content using the provided model
            response = self.model.generate_content(  # Assuming model has generate_content
                f"""Can you help with this Terraform error, please? {help_string}""",
                generation_config={
                    "max_output_tokens": 5535,
                    "temperature": 0.7,
                    "top_p": 1,
                },
                safety_settings={},
                stream=stream,
            )
            return response

    mock_model = Mock()
    mock_model.generate_content.return_value = "Gemini response"

    # Create a MockRequest instance with the mock model
    mock_request = MockRequest(mock_model)

    # Patch the GoogleGenAI.generate_content method
    mock_generate_content = mocker.patch(
        "google_genai.GoogleGenAI.generate_content", return_value="Gemini response"
    )

    # Use the mock_request in your test
    result = mock_request.generate_content(help_string="Example error message")
    assert result == "Gemini response"


# Test send_cloud_funtion_response
@pytest.mark.parametrize(
    "message, code, type, expected_status",
    [
        ("Error message", 500, "error", "failed"),
        ("Info message", 200, "info", "OK"),
    ],
)
def test_send_cloud_funtion_response(message, code, type, expected_status):
    response, status_code = main.send_cloud_funtion_response(message, code, type)

    assert response["message"] == message
    assert response["status"] == expected_status
    assert status_code == code


@pytest.fixture
def mock_secret_manager(mocker):
    mock_client = mocker.patch(
        "google.cloud.secretmanager_v1.SecretManagerServiceClient"
    )
    mock_access = mock_client.return_value.access_secret_version
    mock_access.return_value.payload.data = b"test_api_key"
    return mock_access


@patch("main.get_terraform_cloud_key")
def test_get_terraform_cloud_key_success(mock_secret_manager):
    api_key, message = main.get_terraform_cloud_key("test-secret-name")
    assert api_key == "test_api_key"
    assert message == ""


@patch("main.get_terraform_cloud_key")
def test_get_terraform_cloud_key_failure(mock_secret_manager):
    mock_secret_manager.side_effect = Exception("Mocked Error")
    api_key, message = main.get_terraform_cloud_key("test-secret-name")
    assert api_key == ""
    assert message != ""


def test_send_cloud_funtion_response_error():
    message = "Test Error Message"
    code = 400
    response, status_code = main.send_cloud_funtion_response(message, code, "error")
    assert response["message"] == message
    assert response["status"] == "failed"
    assert status_code == code


def test_send_cloud_funtion_response_info():
    message = "Test Info Message"
    code = 200
    response, status_code = main.send_cloud_funtion_response(message, code, "info")
    assert response["message"] == message
    assert response["status"] == "OK"
    assert status_code == code


# Test get_terraform_cloud_key with success
def test_get_terraform_cloud_key_success(mocker):
    mock_client = mocker.patch(
        "main.google.cloud.secretmanager_v1.SecretManagerServiceClient"
    )
    mock_client.return_value.access_secret_version.return_value.payload.data = (
        b"api-key"
    )

    api_key, message = main.get_terraform_cloud_key("secret-name")

    assert api_key == "api-key"
    assert message == ""


# Test get_terraform_cloud_key with failure
def test_get_terraform_cloud_key_failure(mocker):
    mock_client = mocker.patch(
        "main.google.cloud.secretmanager_v1.SecretManagerServiceClient"
    )
    mock_client.return_value.access_secret_version.side_effect = Exception(
        "Secret not found"
    )

    api_key, message = main.get_terraform_cloud_key("secret-name")

    assert api_key == ""
    assert message != ""


# Test get_run_error with success
def test_get_run_error_success(mocker):
    sample_run_error_response = {"error": "Something went wrong"}
    mock_terraform_cloud = mocker.patch("terraform_cloud.get_run_error")
    mock_terraform_cloud.return_value = sample_run_error_response

    response, message = main.get_run_error("api-key", "run-id")

    assert response == sample_run_error_response
    assert message == ""


# Test get_run_error with failure
def test_get_run_error_failure(mocker):
    mock_terraform_cloud = mocker.patch("terraform_cloud.get_run_error")
    mock_terraform_cloud.side_effect = Exception("Run not found")

    response, message = main.get_run_error("api-key", "run-id")

    assert response == ""
    assert message != ""
