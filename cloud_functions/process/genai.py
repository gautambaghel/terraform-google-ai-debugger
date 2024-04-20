import json
import requests


class GenAI:

    def __init__(self, ai_config_json: str):
        config = json.loads(ai_config_json)
        self.url = config.get("url")
        self.token = config.get("token")
        self.deployment = config.get("deployment")

    def generate_content(self, help_string: str) -> str:

        payload = {"question": help_string, "chat_history": []}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "azureml-model-deployment": f"{self.deployment}",
        }

        payload_json = json.dumps(payload)
        response = requests.post(self.url, data=payload_json, headers=headers)

        return f"{response.text}"


if __name__ == "__main__":
    proj = GenAI()
    proj.generate_content("I need help with my terraform code", stream=False)
