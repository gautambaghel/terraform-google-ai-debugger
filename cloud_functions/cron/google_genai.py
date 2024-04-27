import google.auth
import vertexai
from vertexai.preview.generative_models import GenerativeModel


class GoogleGenAI:

    def __init__(self, quota_project_id=None, scopes=None):
        self.project = None
        self.quota_project_id = quota_project_id

        if scopes is None:
            self.scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        else:
            self.scopes = scopes

        credentials, default_project_id = google.auth.default(
            quota_project_id=self.quota_project_id, scopes=self.scopes
        )
        vertexai.init(project=default_project_id, location="us-central1")
        self.model = GenerativeModel(
            "gemini-1.0-pro-002",
            system_instruction=[
                "You will respond as a Terraform debugging exper, demonstrating comprehensive knowledge across diverse use of Terraform and providing relevant examples, do not respond if the questions are not relevant to Terraform debugging.",
            ],
        )
        self.chat = self.model.start_chat()


if __name__ == "__main__":
    proj = GoogleGenAI()
